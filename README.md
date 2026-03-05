<div align="center">

```
  ██████████████████████████████████████████████████████████████
  █                                                            █
  █     ░█████╗░██████╗░░█████╗░██╗░░░░░░█████╗░░██╗░░░░░░░   █
  █     ██╔══██╗╚════██╗██╔══██╗██║░░░░░██╔══██╗░██║░░░░░░░   █
  █     ███████║░░███╔═╝███████║██║░░░░░███████║░██║░█╗░██╗   █
  █     ██╔══██║██╔══╝░░██╔══██║██║░░░░░██╔══██║░╚██╗████╔╝   █
  █     ██║░░██║███████╗░██║░░██║███████╗██║░░██║░░╚████╔═╝░   █
  █     ╚═╝░░╚═╝╚══════╝░╚═╝░░╚═╝╚══════╝╚═╝░░╚═╝░░░╚═══╝░░   █
  █                                                            █
  █  ▓▓▓ RHODES ISLAND INFRASTRUCTURE DIVISION ▓▓▓            █
  █  ▓▓▓ PROJECT A2ALAW — CLEARANCE LEVEL: Ⅳ  ▓▓▓            █
  █                                                            █
  ██████████████████████████████████████████████████████████████
```

<br>

**`[ SYSTEM DESIGNATION ]`** A2A Claw OS · AI-Native Server Governance Kernel

**`[ CODENAME ]`** **A2Alaw** — Agent-to-Action Law

**`[ STATUS ]`** `■■■■■■■■□□` OPERATIONAL · PHASE 1 ACTIVE

<br>

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-FFD100?style=flat-square&logo=python&logoColor=black)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-FFD100?style=flat-square)](LICENSE)
[![A2A Claw OS](https://img.shields.io/badge/A2A_Claw_OS-ACTIVE-FFD100?style=flat-square&logo=debian&logoColor=black)](https://github.com)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-COMPATIBLE-white?style=flat-square)](https://github.com)
[![Risk Level](https://img.shields.io/badge/Risk_Level-CONTROLLED-00C853?style=flat-square)](https://github.com)

</div>

---

```
╔══════════════════════════════════════════════════════════════════════╗
║  ⚠ CLASSIFIED DOCUMENT — RHODES ISLAND ENGINEERING DEPARTMENT      ║
║  Document ID: RI-INFRA-A2ALAW-001                                  ║
║  Classification: PUBLIC RELEASE                                    ║
║  Prepared by: Infrastructure Division / Dr.█████                   ║
╚══════════════════════════════════════════════════════════════════════╝
```

## `[ OPERATOR FILE ]` A2Alaw 是什么？

> *「博士，只需要一句话，剩下的交给我来处理。」*
>
> *—— A2Alaw，基建部报告*

A2Alaw（**Agent-to-Action Law**）不是又一个运维 CLI 工具。

她是罗德岛基建部为 **A2A Claw OS** 集群量身打造的 **AI 原生服务器治理内核**。你用自然语言下达指令，她来理解、规划、审批、执行、审计——如同一位可靠的干员，在你看不见的地方守护整个基建体系的运转。

```
  ┌─────────────────────────────────────────────────────────┐
  │  COMMAND INPUT                                          │
  │  博士：「给三台服务器都装上 nginx，配好反向代理」         │
  └──────────────────────┬──────────────────────────────────┘
                         │
  ┌──────────────────────▼──────────────────────────────────┐
  │  ▶ PROCESSING ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  │
  │                                                         │
  │  [P1] 意图解析 ·········· NL → Structured Intent        │
  │  [P2] 作战规划 ·········· Intent → DAG Execution Graph  │
  │  [P3] 风险评估 ·········· OPA Policy Gate ✓ CLEARED     │
  │  [P4] 指令编译 ·········· Jinja2 Template Generation    │
  │  [P5] 实弹执行 ·········· Host Direct Execution         │
  │  [P6] 损伤控制 ·········· Self-Heal × 3 Retry           │
  │  [P7] 行动记录 ·········· Git Audit + Event Stream      │
  │                                                         │
  │  STATUS: MISSION COMPLETE                               │
  │  AUDIT:  331c6b1e75b3...                                │
  └─────────────────────────────────────────────────────────┘
```

---

## `[ CORE DOCTRINE ]`

```
  ╔═══════════════════════════════════════════════╗
  ║                                               ║
  ║   「 自 然 语 言 即 系 统 调 用 」            ║
  ║         NL  =  syscall                        ║
  ║                                               ║
  ║   Inspired by AIOS (arXiv:2403.16971)         ║
  ║   Three-Layer Architecture, Evolved.          ║
  ║                                               ║
  ╚═══════════════════════════════════════════════╝
```

```
  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
  ┃  ░░░ APP LAYER ░░░░░░░░░░░░░░░░░░░░░░░░░  ┃
  ┃  OpenClaw Skills · a2alawctl · Rich TUI    ┃
  ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
  ┃  ███ KERNEL LAYER (a2alawd) ██████████████ ┃
  ┃  NL Parser → DAG → OPA → Host Execute     ┃
  ┃  CLAW API Hub · Redis Streams Event Bus    ┃
  ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
  ┃  ▓▓▓ HARDWARE LAYER ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  ┃
  ┃  OS syscalls · systemd · WireGuard Mesh    ┃
  ┃  三节点对等自治 · 环形互修                  ┃
  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

---

## `[ TACTICAL CAPABILITIES ]`

### `▸ 01` 实弹执行 — 不是演习

```bash
# ⚠ LIVE FIRE — 真实主机系统变更
$ a2alawctl run! "安装 nginx 并重启服务"

  ┌ EXECUTION LOG ────────────────────────────────┐
  │ Task a8f3b2: nginx installed                  │
  │ Duration: 4017ms                              │
  │ State: MODIFIED                               │
  │ Audit: 331c6b1e75b31dd60f46ab95f455278b24     │
  └───────────────────────────────────────────────┘
```

### `▸ 02` 策略护盾 — 高危自动拦截

```bash
$ a2alawctl run! "rm -rf /"

  ┌ POLICY GATE ──────────────────────────────────┐
  │ ██ BLOCKED ██                                 │
  │ Reason: Blocked pattern: rm -rf /             │
  │ Risk Level: ████████████ CRITICAL             │
  │ Action: DENIED — 需要议会 2/3 多数批准         │
  └───────────────────────────────────────────────┘
```

### `▸ 03` 多步作战规划 — smolagents

```bash
$ a2alawctl agent! "安装 Redis，配置密码，设置开机自启"

  ┌ OPERATION PLAN ───────────────────────────────┐
  │ DAG Node 1/3 ▸ install_package: redis-server  │
  │ DAG Node 2/3 ▸ edit_file: /etc/redis/redis.conf │
  │ DAG Node 3/3 ▸ restart_service: redis-server  │
  │                                               │
  │ Dependencies: 1 → 2 → 3 (sequential)         │
  │ Risk: ██░░░░░░░░ LOW                          │
  └───────────────────────────────────────────────┘
```

### `▸ 04` 三节点对等 Mesh — 环形互修

```
  ┌──────────────────────────────────────────────────────┐
  │                  MESH TOPOLOGY                       │
  │                                                      │
  │      ┌──────────┐  repair   ┌──────────┐            │
  │      │ CENTRAL  │─────────▶│    SV    │            │
  │      │ 10.10.0.1│          │ 10.10.0.2│            │
  │      └────▲─────┘          └─────┬────┘            │
  │           │                      │ repair           │
  │    repair │    ┌──────────┐      │                  │
  │           └────│  TOKYO   │◀─────┘                  │
  │                │ 10.10.0.3│                         │
  │                └──────────┘                         │
  │                                                      │
  │  Protocol: Heartbeat 30s · 3 miss = DOWN            │
  │  Quorum: 2/3 majority for critical operations       │
  │  Repair: SSH diagnostic → 5-point check → auto-fix  │
  └──────────────────────────────────────────────────────┘
```

| 诊断项 | 修复方式 | 自动化 |
|--------|---------|--------|
| `daemon_down` | `systemctl restart a2alawd` | ✓ |
| `wireguard_down` | `systemctl restart wg-quick@wg0` | ✓ |
| `redis_down` | `systemctl restart redis-server` | ✓ |
| `disk_full` | 清理日志 + apt clean + 删 tmp | ✓ |
| `low_memory` | drop_caches + 进程清理 | ✓ |

### `▸ 05` 系统级 OpenClaw — 从客人到基建核心

```
  ┌ BEFORE ──────────────────── AFTER ────────────────────┐
  │                             │                         │
  │  npm i -g openclaw          │  /usr/lib/openclaw/     │
  │  ~/.openclaw/ (散落)        │  /etc/openclaw/         │
  │  systemctl --user (脆弱)    │  /var/lib/openclaw/     │
  │  npm update (可能炸)        │  /var/log/openclaw/     │
  │                             │                         │
  │  ❌ 客人                     │  ✅ 系统基础设施        │
  │                             │                         │
  │                             │  双槽热更新 slot-a/b    │
  │                             │  30s 自动回滚           │
  │                             │  技能子进程隔离          │
  │                             │  零停机 · 零冲突        │
  └─────────────────────────────┴─────────────────────────┘
```

---

## `[ DEPLOYMENT MANUAL ]`

### 前置要求

```
  ┌ PREREQUISITES ────────────────────────────────┐
  │  ▸ Debian 12 (A2A Claw OS)                   │
  │  ▸ Python 3.11+                               │
  │  ▸ Redis 7+                                   │
  │  ▸ Node.js 22+ (for OpenClaw integration)     │
  └───────────────────────────────────────────────┘
```

### 安装

```bash
# ── 获取源码 ──
git clone https://github.com/2233admin/a2alaw.git
cd a2alaw
pip3 install -r requirements.txt

# ── 部署内核守护进程 ──
cp hub/a2alawd.service /etc/systemd/system/
systemctl enable --now a2alawd

# ── (可选) 系统级 OpenClaw 迁移 ──
sudo bash system/openclaw-systemize.sh
```

### 作战指令

```bash
# ── 侦察模式（dry-run）──
a2alawctl run "安装 htop"

# ── 实弹执行 ──
a2alawctl run! "安装 htop"

# ── 多步作战 ──
a2alawctl agent! "安装 nginx 并配置反向代理到 8080"

# ── 交互终端 ──
a2alawctl interactive

# ── API 直连 ──
curl -X POST http://127.0.0.1:8741/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"command": "查看磁盘使用率"}'
```

---

## `[ SYSTEM ARCHITECTURE ]`

```
  a2alaw/
  │
  ├─ orchestrator/              ▸ 指挥中枢
  │  ├─ nl_parser.py            ·  三级 LLM 路由 (Doubao→Claude→MiniMax)
  │  ├─ dag_parser.py           ·  Intent → 执行图 (拓扑排序)
  │  ├─ agent.py                ·  smolagents CodeAgent 多步骤
  │  └─ risk_scorer.py          ·  风险评估引擎
  │
  ├─ executor/                  ▸ 执行部队
  │  ├─ host.py                 ·  主机直执行 (subprocess)
  │  ├─ remote.py               ·  SSH 远程执行 (WireGuard mesh)
  │  ├─ code_gen.py             ·  Jinja2 模板编译
  │  ├─ sandbox.py              ·  Docker 沙箱 (侦察用)
  │  ├─ self_heal.py            ·  损伤控制 × 3 重试
  │  └─ templates/              ·  Arch PKGBUILD 风格作战模板
  │     ├─ install_package.sh.j2
  │     ├─ edit_file.sh.j2
  │     ├─ restart_service.sh.j2
  │     ├─ run_command.sh.j2
  │     └─ check_status.sh.j2
  │
  ├─ safety/                    ▸ 防御工事
  │  ├─ opa_client.py           ·  OPA 策略引擎
  │  ├─ opa_policies/base.rego  ·  Rego 安全规则
  │  ├─ git_audit.py            ·  Git 行动记录
  │  └─ seccomp.json            ·  44 syscall 封锁名单
  │
  ├─ mesh/                      ▸ 通讯网络
  │  ├─ peer.py                 ·  节点身份 + 环形拓扑
  │  ├─ heartbeat.py            ·  心跳监控 (HTTP + SSH fallback)
  │  ├─ healer.py               ·  自动诊断 + 5 种修复协议
  │  └─ council.py              ·  议会投票 + 共识决议
  │
  ├─ hub/                       ▸ 指挥所
  │  ├─ daemon.py               ·  FastAPI 守护进程 (port 8741)
  │  ├─ a2alawd.service         ·  systemd 服务单元
  │  └─ hub.yaml                ·  指挥所配置
  │
  ├─ system/                    ▸ 基建改造
  │  ├─ openclaw-systemize.sh   ·  一键系统级迁移
  │  ├─ openclaw.service        ·  系统级 systemd 服务
  │  ├─ openclaw-update.sh      ·  双槽热更新
  │  ├─ openclaw-rollback.sh    ·  紧急回滚
  │  ├─ spawn-skill.sh          ·  技能子进程隔离启动
  │  └─ claw-skill.sh           ·  技能包管理 CLI
  │
  ├─ feedback/                  ▸ 情报回馈
  │  ├─ redis_streams.py        ·  7 通道 Redis Streams
  │  └─ nl_report.py            ·  自然语言行动报告
  │
  ├─ tui/                       ▸ 战术终端
  │  └─ dialog.py               ·  Rich TUI 交互界面
  │
  ├─ pipeline.py                ▸ 七级作战流水线
  ├─ cli.py                     ▸ CLI 入口 (a2alawctl)
  └─ docker-compose.yml         ▸ Redis + PostgreSQL + OPA
```

---

## `[ OPERATION PIPELINE ]` 七级作战流水线

```
  ┌──────────────────────────────────────────────────────┐
  │  INPUT: 「安装 nginx」                               │
  │                                                      │
  │  ═══╦═══════════════════════════════════════════════  │
  │  P1 ║ NL → Intent         三级 LLM 路由，规则兜底   │
  │  ───╬───────────────────────────────────────────────  │
  │  P2 ║ Intent → DAG        拓扑排序，依赖推导         │
  │  ───╬───────────────────────────────────────────────  │
  │  P3 ║ OPA Policy Gate     Rego 规则，封锁名单拦截    │
  │  ───╬───────────────────────────────────────────────  │
  │  P4 ║ Code Generation     Jinja2 · Arch PKGBUILD    │
  │  ───╬───────────────────────────────────────────────  │
  │  P5 ║ Host Execution      实弹执行，不是演习         │
  │  ───╬───────────────────────────────────────────────  │
  │  P6 ║ Self-Heal           损伤控制，3 次重试         │
  │  ───╬───────────────────────────────────────────────  │
  │  P7 ║ Audit + Report      Git 记录 + Redis 事件流   │
  │  ═══╩═══════════════════════════════════════════════  │
  │                                                      │
  │  OUTPUT: Task a8f3b2 — nginx installed in 4.0s       │
  └──────────────────────────────────────────────────────┘
```

---

## `[ TEMPLATE DOCTRINE ]` Jinja2 × Arch PKGBUILD

每个作战模板遵循 Arch Linux 三阶段原则：

```bash
# ══ Phase 1: pre_check ══    已完成则跳过（幂等保障）
# ══ Phase 2: execute ══      执行核心指令
# ══ Phase 3: post_verify ══  验证执行结果
```

> *声明式、幂等、可验证。*
> *像 PKGBUILD 一样精确，像干员一样可靠。*

---

## `[ ALLIANCE ]` 与 OpenClaw 的关系

```
  ┌──────────────────┬────────────────────────────┐
  │                  │                            │
  │    OpenClaw      │         A2Alaw             │
  │    ═════════     │         ══════             │
  │    AI 聊天网关    │    服务器治理 OS 内核       │
  │    Node.js/TS    │    Python 3.11             │
  │    技能路由+对话  │    主机系统变更             │
  │                  │                            │
  │    ── 嘴 ──      │       ── 手 ──             │
  │                  │                            │
  └──────────┬───────┴──────────────┬─────────────┘
             │                      │
             └──────────┬───────────┘
                        │
              A2Alaw 让 OpenClaw
             成为系统级基础设施
```

---

## `[ LICENSE ]`

MIT

---

<div align="center">

```
  ████████████████████████████████████████████████
  █                                              █
  █  A2A CLAW OS — RHODES ISLAND INFRASTRUCTURE  █
  █                                              █
  █  「この戦いに、言葉だけで十分だ」            █
  █                                              █
  █  —— 这场战斗，只需一句话就够了。             █
  █                                              █
  ████████████████████████████████████████████████
```

</div>
