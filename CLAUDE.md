# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A2Alaw is an AI-native server governance kernel for A2A Claw OS. Natural language in, real system changes out, with a seven-stage pipeline (NL parse → DAG → OPA policy → codegen → host exec → self-heal → audit). 用户使用中文交流。

## Commands

```bash
# Run the daemon (FastAPI on port 8741)
uvicorn a2alaw.hub.daemon:app --host 127.0.0.1 --port 8741

# CLI
python -m a2alaw run "查看磁盘"          # dry-run
python -m a2alaw run! "安装 htop"         # real execution
python -m a2alaw agent! "安装 nginx"      # multi-step via smolagents

# Lint
ruff check . --fix
ruff format .

# Test
pytest test_host.py test_loop.py -v

# Deploy daemon to server
scp -r . root@10.10.0.1:/root/a2alaw/
ssh root@10.10.0.1 "systemctl restart a2alawd"
```

## Architecture

**Core flow**: `cli.py` → `pipeline.py` → (orchestrator → executor → safety → feedback)

`pipeline.py` is the main orchestrator. It chains 7 stages via the `Pipeline` class:
1. `orchestrator/nl_parser.py` — Three-tier LLM routing (Doubao → Claude → MiniMax), falls back to regex
2. `orchestrator/dag_parser.py` — Intent → `ExecutionDAG` of `DAGNode`s, topological sort
3. `safety/opa_client.py` — OPA Rego policy check + `orchestrator/risk_scorer.py`
4. `executor/code_gen.py` — Jinja2 templates (`executor/templates/*.sh.j2`) → bash scripts
5. `executor/host.py` — `subprocess.run()` on real host (not Docker)
6. `executor/self_heal.py` — Classify errors, retry up to 3x
7. `safety/git_audit.py` + `feedback/redis_streams.py` + `feedback/nl_report.py`

**Daemon**: `hub/daemon.py` — FastAPI app with endpoints `/v1/execute`, `/v1/plan`, `/v1/status`, `/v1/heal`, `/v1/council/propose`. Systemd unit: `hub/a2alawd.service`.

**Mesh** (three-node peer-to-peer):
- `mesh/peer.py` — Node identity, ring topology (central→sv→tokyo→central)
- `mesh/heartbeat.py` — 30s HTTP+SSH health checks, `NodeState` enum
- `mesh/healer.py` — Auto-diagnose + 5 repair scripts via SSH
- `mesh/council.py` — Redis Streams `mesh:council`, 2/3 quorum voting

**OpenClaw system integration** (`system/`): Shell scripts for FHS migration, dual-slot hot update, skill subprocess isolation. Not Python — these are deployment tools.

## Key Patterns

- **Jinja2 templates** follow Arch PKGBUILD three-phase: `pre_check` (idempotent skip) → `execute` → `post_verify`
- **LLM routing**: env vars `DOUBAO_*`, `YUNYI_*`, `MINIMAX_*` in `.env`. Three tiers by cost
- **Risk scoring**: `risk_scorer.py` determines approval requirements. Low risk (<0.4) auto-approved; high risk needs council vote
- **Event bus**: 7 Redis Streams channels (execute, audit, health, council, etc.)
- **Host execution**: `executor/host.py` writes script to temp file, runs via `subprocess.run()`. OPA check MUST happen before calling

## Constraints

- Python 3.11+, lint with ruff (line-length=100)
- Target servers run OpenCloudOS with dnf (not apt)
- Central server is 2 core / 2GB RAM — keep memory usage low
- LLM tier 1 (Doubao) is free; avoid expensive models for routine parsing
- Never execute on host without OPA policy check first
- All system changes must produce a git audit commit
