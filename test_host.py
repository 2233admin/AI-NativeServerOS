"""Quick test of host execution pipeline."""
from a2alaw.orchestrator.dag_parser import _assess_risk
print("check risk:", _assess_risk("check", "disk"))
print("run risk:", _assess_risk("run", "ls"))

from a2alaw.pipeline import Pipeline

# Dry-run test
p = Pipeline(dry_run=True)
r = p.run("查看磁盘使用率")
print(f"\n[dry-run] blocked={r.policy_blocked} approved={r.approved}")
print(f"report: {r.report[:120]}")
for res in r.results:
    print(f"  {res.get('skill')}: exit={res.get('exit_code')} stdout={res.get('stdout','')[:60]}")

# Real execution test
p2 = Pipeline(dry_run=False)
r2 = p2.run("查看磁盘使用率")
print(f"\n[REAL] blocked={r2.policy_blocked} approved={r2.approved}")
print(f"report: {r2.report[:120]}")
for res in r2.results:
    print(f"  {res.get('skill')}: exit={res.get('exit_code')} stdout={res.get('stdout','')[:80]}")
if r2.audit_sha:
    print(f"audit: {r2.audit_sha}")
