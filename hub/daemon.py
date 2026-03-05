"""CLAW API Hub — A2Alaw kernel daemon.

FastAPI service exposing:
  POST /v1/execute   — NL command → host execution
  POST /v1/plan      — NL command → DAG preview (dry-run)
  GET  /v1/status    — System health
  GET  /health       — Liveness probe

Runs as systemd service (a2alawd), listens on localhost:8741 + unix socket.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from a2alaw.pipeline import Pipeline, PipelineResult


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connect event bus on startup
    app.state.event_bus = _try_event_bus()
    # Start mesh heartbeat monitor
    app.state.heartbeat = _start_heartbeat(app.state.event_bus)
    yield
    if app.state.heartbeat:
        app.state.heartbeat.stop()


app = FastAPI(title="A2Alaw Hub", version="0.1.0", lifespan=lifespan)


class ExecuteRequest(BaseModel):
    command: str
    use_agent: bool = False
    dry_run: bool = False


class ExecuteResponse(BaseModel):
    success: bool
    report: str
    policy_blocked: bool = False
    policy_reasons: list[str] = []
    audit_sha: str | None = None
    total_ms: int = 0


@app.post("/v1/execute")
def execute(req: ExecuteRequest) -> ExecuteResponse:
    pipe = Pipeline(
        dry_run=req.dry_run,
        event_bus=app.state.event_bus,
        use_agent=req.use_agent,
        auto_approve_low_risk=True,
        approval_fn=lambda a, t, r: req.dry_run,  # Auto-approve in dry-run
    )
    result = pipe.run(req.command)
    return ExecuteResponse(
        success=result.success,
        report=result.report,
        policy_blocked=result.policy_blocked,
        policy_reasons=result.policy_reasons,
        audit_sha=result.audit_sha,
        total_ms=result.total_ms,
    )


@app.post("/v1/plan")
def plan(req: ExecuteRequest) -> ExecuteResponse:
    """Always dry-run — preview only."""
    req.dry_run = True
    return execute(req)


@app.get("/v1/status")
def status():
    import shutil
    disk = shutil.disk_usage("/")
    from a2alaw.mesh.peer import whoami
    me = whoami()
    peer_health = {}
    if app.state.heartbeat:
        peer_health = {
            name: ph.state.value
            for name, ph in app.state.heartbeat.health.items()
        }
    return {
        "status": "ok",
        "node": me.name,
        "ip": me.ip,
        "disk_free_gb": round(disk.free / (1024**3), 1),
        "event_bus": app.state.event_bus is not None,
        "peers": peer_health,
    }


@app.post("/v1/heal")
def heal():
    """Trigger repair of my designated repair target."""
    from a2alaw.mesh.healer import auto_heal
    result = auto_heal(event_bus=app.state.event_bus)
    if result is None:
        return {"status": "ok", "message": "Repair target is healthy"}
    return {
        "status": "repaired" if not result.failed else "partial",
        "node": result.node,
        "issues": result.issues,
        "fixed": result.fixed,
        "failed": result.failed,
        "duration_ms": result.duration_ms,
    }


@app.post("/v1/council/propose")
def propose(action: str, risk_level: str = "medium"):
    """Propose an action for peer vote."""
    if not app.state.event_bus:
        raise HTTPException(503, "Event bus not connected")
    from a2alaw.mesh.council import Council
    council = Council(app.state.event_bus)
    prop = council.propose(action, risk_level=risk_level)
    return {"proposal_id": prop.id, "proposer": prop.proposer, "action": action}


@app.get("/health")
def health():
    return {"status": "ok"}


def _start_heartbeat(event_bus):
    try:
        from a2alaw.mesh.heartbeat import HeartbeatMonitor
        monitor = HeartbeatMonitor(event_bus=event_bus)
        monitor.start()
        return monitor
    except Exception:
        return None


def _try_event_bus():
    try:
        from a2alaw.feedback.redis_streams import EventBus
        bus = EventBus()
        bus.r.ping()
        return bus
    except Exception:
        return None


def main():
    import uvicorn
    host = os.environ.get("A2ALAW_HOST", "127.0.0.1")
    port = int(os.environ.get("A2ALAW_PORT", "8741"))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
