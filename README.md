<div align="center">

# A2Alaw

**AI-Native Server Governance Kernel for A2A Claw OS**

自然语言即系统调用

<br>

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-000?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-000?style=flat-square)](LICENSE)
[![A2A Claw OS](https://img.shields.io/badge/A2A_Claw_OS-ACTIVE-000?style=flat-square)](https://github.com/2233admin/a2alaw)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-COMPATIBLE-333?style=flat-square)](https://github.com)

</div>

<br>

## 概述

A2Alaw（Agent-to-Action Law）是为 **A2A Claw OS** 集群打造的服务器治理内核。你用自然语言下达指令，它来理解、规划、审批、执行、审计。

> *「博士，只需要一句话，剩下的交给我来处理。」*

```bash
$ a2alawctl run! "给三台服务器都装上 nginx，配好反向代理"
```

七步完成：意图解析 → 执行图规划 → 策略审批 → 脚本编译 → 主机执行 → 自愈重试 → 审计记录

<br>

## 核心能力

### 实弹执行

不是沙箱模拟，是真实主机系统变更。基于 subprocess 直接执行，每次操作自动 Git 审计。

```bash
a2alawctl run! "安装 nginx 并重启服务"    # 真实执行
a2alawctl run  "安装 nginx 并重启服务"    # dry-run 预览
```

### 策略护盾

OPA Rego 规则引擎自动拦截高危操作。`rm -rf /` 之类的指令直接封锁，无需人工介入。

### 多步规划

复杂指令自动拆解为 DAG 执行图，拓扑排序，依赖推导，逐步执行。

```
install_package:redis → edit_file:redis.conf → restart_service:redis
```

### 三节点对等 Mesh

三节点环形互修拓扑。每 30 秒心跳检测，连续 3 次失败判定宕机，自动诊断修复。关键操作需要 2/3 议会多数批准。

```
central (10.10.0.1) ──repair──▸ sv (10.10.0.2)
    ▴                                │ repair
    └───── tokyo (10.10.0.3) ◂───────┘
```

### 系统级 OpenClaw

将 OpenClaw 从用户态 npm 包提升为系统基础设施：FHS 标准目录、双槽原子热更新（slot-a / slot-b）、30 秒自动回滚、技能子进程隔离。不改一行 OpenClaw 源码。

<br>

## 架构

基于 AIOS（arXiv:2403.16971）三层架构：

| 层级 | 组件 | 职责 |
|------|------|------|
| **App** | OpenClaw Skills · a2alawctl · TUI | 用户交互入口 |
| **Kernel** | a2alawd · NL Parser · DAG · OPA | 意图理解、规划、审批、执行 |
| **Hardware** | OS syscalls · systemd · WireGuard | 系统调用、进程管理、网络互联 |

<br>

## 项目结构

```
a2alaw/
├─ orchestrator/           意图解析与执行规划
│  ├─ nl_parser.py         三级 LLM 路由 (Doubao → Claude → MiniMax)
│  ├─ dag_parser.py        Intent → DAG 执行图
│  ├─ agent.py             smolagents 多步编排
│  └─ risk_scorer.py       风险评估
│
├─ executor/               执行层
│  ├─ host.py              主机直执行
│  ├─ remote.py            SSH 远程执行
│  ├─ code_gen.py          Jinja2 模板编译
│  ├─ self_heal.py         自愈重试
│  └─ templates/           Arch PKGBUILD 风格脚本模板
│
├─ safety/                 安全层
│  ├─ opa_client.py        OPA 策略引擎
│  ├─ opa_policies/        Rego 安全规则
│  └─ git_audit.py         Git 审计记录
│
├─ mesh/                   集群治理
│  ├─ peer.py              节点身份与拓扑
│  ├─ heartbeat.py         心跳监控
│  ├─ healer.py            自动诊断与修复
│  └─ council.py           议会投票与共识
│
├─ hub/                    守护进程
│  ├─ daemon.py            FastAPI 服务 (port 8741)
│  └─ a2alawd.service      systemd 服务单元
│
├─ system/                 OpenClaw 系统级集成
│  ├─ openclaw-systemize.sh   系统迁移脚本
│  ├─ openclaw.service        systemd 服务
│  ├─ openclaw-update.sh      双槽热更新
│  ├─ openclaw-rollback.sh    一键回滚
│  ├─ spawn-skill.sh          技能子进程隔离
│  └─ claw-skill.sh           技能包管理
│
├─ feedback/               事件回馈
│  ├─ redis_streams.py     7 通道 Redis Streams
│  └─ nl_report.py         自然语言报告
│
├─ pipeline.py             七级执行流水线
└─ cli.py                  CLI 入口
```

<br>

## 执行流水线

```
NL Input
  │
  ▾
┌─ P1 ─┐  意图解析      三级 LLM 路由，规则引擎兜底
├─ P2 ─┤  执行图规划    拓扑排序，依赖推导
├─ P3 ─┤  策略审批      OPA Rego 规则，封锁名单
├─ P4 ─┤  脚本编译      Jinja2 模板，三阶段幂等
├─ P5 ─┤  主机执行      subprocess 直执行
├─ P6 ─┤  自愈重试      失败自动诊断，最多 3 次
└─ P7 ─┘  审计记录      Git commit + Redis 事件流
  │
  ▾
Result + Audit Hash
```

每个脚本模板遵循 Arch PKGBUILD 三阶段：`pre_check`（幂等检查）→ `execute`（执行）→ `post_verify`（验证）。

<br>

## 部署

```bash
git clone https://github.com/2233admin/a2alaw.git
cd a2alaw
pip3 install -r requirements.txt

# 部署守护进程
cp hub/a2alawd.service /etc/systemd/system/
systemctl enable --now a2alawd

# (可选) OpenClaw 系统级迁移
sudo bash system/openclaw-systemize.sh
```

<br>

## A2Alaw 与 OpenClaw

| | OpenClaw | A2Alaw |
|---|---------|--------|
| 角色 | AI 聊天网关 | 服务器治理内核 |
| 技术栈 | Node.js / TypeScript | Python 3.11 |
| 职责 | 技能路由、对话管理 | 主机系统变更 |
| 比喻 | 嘴 | 手 |

A2Alaw 让 OpenClaw 成为系统级基础设施。

<br>

## License

MIT

<br>

<div align="center">

*この戦いに、言葉だけで十分だ。*

这场战斗，只需一句话就够了。

</div>
