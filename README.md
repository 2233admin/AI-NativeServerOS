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

A2Alaw（Agent-to-Action Law）是为 **A2A Claw OS** 设计的 AI 原生服务器治理内核。它将自然语言指令转化为真实的系统变更操作，同时通过策略引擎、风险评估和审计追踪保障安全性。

传统服务器运维依赖管理员手写脚本或逐条执行命令。A2Alaw 将这一过程重构为一条七阶段流水线：从自然语言理解到执行图规划，从策略审批到主机执行，每一步都有对应的安全机制。它不是一个 ChatOps 机器人——它是一个带有完整策略执行引擎的操作系统内核层。

> *「博士，只需要一句话，剩下的交给我来处理。」*

```bash
$ a2alawctl run! "给三台服务器都装上 nginx，配好反向代理"
```

<br>

## 设计理念

A2Alaw 的核心假设是：**服务器运维本质上是一个"意图→执行"的翻译问题**。管理员心里想的是"我要装 nginx"，但实际操作涉及包管理器选择、依赖检查、配置文件编辑、服务重启、验证——这些中间步骤完全可以由 AI 推导完成。

基于这个假设，A2Alaw 采用三层架构：

| 层级 | 组件 | 职责 |
|------|------|------|
| **App** | OpenClaw Skills · a2alawctl · Rich TUI | 用户交互，自然语言输入 |
| **Kernel** | a2alawd · NL Parser · DAG · OPA · CodeGen | 意图理解、规划、审批、执行 |
| **Hardware** | OS syscalls · systemd · WireGuard Mesh | 系统调用、进程管理、网络互联 |

这一架构参考了 AIOS 论文提出的 LLM-as-OS 范式，但做了关键调整：A2Alaw 不是在操作系统之上模拟一个 AI 操作系统，而是直接作为现有 Linux 系统的治理层，通过 subprocess 执行真实系统调用。

<br>

## 七阶段执行流水线

```
NL Input → P1 意图解析 → P2 执行图规划 → P3 策略审批 → P4 脚本编译 → P5 主机执行 → P6 自愈重试 → P7 审计记录 → Result
```

**P1 — 自然语言解析**：三级 LLM 路由。优先使用 Doubao（免费），复杂指令升级到 Claude，兜底使用规则引擎。输出结构化 Intent。

**P2 — DAG 执行图**：将 Intent 拆解为有向无环图，拓扑排序确定执行顺序。复杂多步指令通过 smolagents CodeAgent 自动编排。

**P3 — OPA 策略审批**：Rego 规则引擎评估风险等级。封锁名单（如 `rm -rf /`）直接拦截，高风险操作需要议会 2/3 多数批准。

**P4 — 脚本编译**：Jinja2 模板生成 Bash 脚本。每个模板遵循 Arch Linux PKGBUILD 的三阶段设计——`pre_check`（幂等检查，已完成则跳过）→ `execute`（执行核心指令）→ `post_verify`（验证结果）。

**P5 — 主机执行**：通过 subprocess 直接在主机上执行，不是 Docker 沙箱模拟。dry-run 模式仅输出预览不执行。

**P6 — 自愈重试**：执行失败时自动诊断错误类型，最多重试 3 次。

**P7 — 审计记录**：每次操作生成 Git commit（包含执行脚本、输出、耗时），同时写入 Redis Streams 事件流。

<br>

## 核心能力

### 实弹执行 vs 预览模式

```bash
a2alawctl run  "安装 nginx"    # dry-run: 仅输出将要执行的脚本
a2alawctl run! "安装 nginx"    # 真实执行: 实际变更系统状态
```

### OPA 策略护盾

高危操作自动拦截，无需人工介入：

```bash
$ a2alawctl run! "rm -rf /"
# → BLOCKED: Blocked pattern: rm -rf /
# → Risk Level: CRITICAL — 需要议会 2/3 多数批准
```

### smolagents 多步编排

复杂指令自动拆解为 DAG，逐步执行：

```bash
$ a2alawctl agent! "安装 Redis，配置密码，设置开机自启"
# → DAG: install_package:redis → edit_file:redis.conf → restart_service:redis
```

### 三节点对等 Mesh

环形互修拓扑，每 30 秒心跳检测，3 次失败判定宕机，自动 SSH 诊断修复：

```
central (10.10.0.1) → sv (10.10.0.2) → tokyo (10.10.0.3) → central
```

自动修复项：daemon 宕机、WireGuard 断开、Redis 挂掉、磁盘满、内存不足。关键操作需 2/3 议会投票通过。

### 系统级 OpenClaw 集成

将 OpenClaw 从用户态 npm 包提升为 FHS 标准系统基础设施。双槽原子热更新（slot-a / slot-b），30 秒内健康检查失败自动回滚。技能作为独立 systemd 子进程运行，资源隔离（CPU 10% / Mem 256M），不影响网关。不改一行 OpenClaw 源码，完全通过环境变量重定向。

<br>

## 项目结构

```
a2alaw/
├─ orchestrator/           意图解析与执行规划
│  ├─ nl_parser.py         三级 LLM 路由 (Doubao → Claude → MiniMax)
│  ├─ dag_parser.py        Intent → DAG 执行图 (拓扑排序)
│  ├─ agent.py             smolagents CodeAgent 多步编排
│  └─ risk_scorer.py       风险评估引擎
│
├─ executor/               执行层
│  ├─ host.py              主机直执行 (subprocess)
│  ├─ remote.py            SSH 远程执行 (WireGuard mesh)
│  ├─ code_gen.py          Jinja2 模板编译
│  ├─ self_heal.py         自愈重试 (最多 3 次)
│  └─ templates/           Arch PKGBUILD 风格脚本模板
│     ├─ install_package.sh.j2
│     ├─ edit_file.sh.j2
│     ├─ restart_service.sh.j2
│     ├─ run_command.sh.j2
│     └─ check_status.sh.j2
│
├─ safety/                 安全层
│  ├─ opa_client.py        OPA 策略引擎客户端
│  ├─ opa_policies/        Rego 规则 (base.rego)
│  ├─ git_audit.py         Git 审计记录
│  └─ seccomp.json         seccomp 系统调用封锁 (44 条)
│
├─ mesh/                   集群治理
│  ├─ peer.py              节点身份 + 环形拓扑
│  ├─ heartbeat.py         心跳监控 (HTTP + SSH fallback)
│  ├─ healer.py            自动诊断 + 5 种修复协议
│  └─ council.py           议会投票 + Redis Streams 共识
│
├─ hub/                    守护进程
│  ├─ daemon.py            FastAPI 服务 (port 8741)
│  └─ a2alawd.service      systemd 服务单元
│
├─ system/                 OpenClaw 系统级集成
│  ├─ openclaw-systemize.sh   FHS 目录迁移
│  ├─ openclaw.service        systemd 服务
│  ├─ openclaw-update.sh      双槽热更新
│  ├─ openclaw-rollback.sh    一键回滚
│  ├─ spawn-skill.sh          技能子进程隔离
│  └─ claw-skill.sh           技能包管理 CLI
│
├─ feedback/               事件回馈
│  ├─ redis_streams.py     7 通道事件总线
│  └─ nl_report.py         自然语言执行报告
│
├─ pipeline.py             七阶段流水线主控
└─ cli.py                  CLI 入口 (a2alawctl)
```

<br>

## 部署

**前置要求**：Debian 12+ / A2A Claw OS，Python 3.11+，Redis 7+，Node.js 22+（OpenClaw 集成）

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

**CLI 用法**：

```bash
a2alawctl run  "查看磁盘使用率"                    # dry-run 预览
a2alawctl run! "安装 htop"                          # 真实执行
a2alawctl agent! "安装 nginx 并配置反向代理到 8080"  # 多步编排
a2alawctl interactive                                # 交互终端
```

**API 用法**：

```bash
curl -X POST http://127.0.0.1:8741/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"command": "查看磁盘使用率"}'
```

<br>

## A2Alaw 与 OpenClaw

| | OpenClaw | A2Alaw |
|---|---------|--------|
| 角色 | AI 聊天网关 | 服务器治理内核 |
| 技术栈 | Node.js / TypeScript | Python 3.11 |
| 职责 | 技能路由、对话管理 | 主机系统变更 |
| 关系 | 嘴——理解用户意图 | 手——执行系统操作 |

A2Alaw 将 OpenClaw 从用户态 npm 包提升为系统级基础设施，通过环境变量重定向（`OPENCLAW_HOME` / `OPENCLAW_CONFIG_PATH` / `OPENCLAW_STATE_DIR`）实现 FHS 标准目录布局，不改一行源码。

<br>

## 参考论文与技术

| 论文 / 技术 | 应用位置 | 说明 |
|-------------|---------|------|
| **AIOS: LLM Agent Operating System** (arXiv:2403.16971) | 整体架构 | 提出 LLM-as-OS 三层架构（App / Kernel / Hardware）。A2Alaw 采用该范式但不虚拟化 OS，而是直接作为 Linux 治理层 |
| **smolagents** (HuggingFace) | `orchestrator/agent.py` | 轻量级 CodeAgent 框架，用于将复杂自然语言指令自动拆解为多步 DAG 执行图 |
| **Open Policy Agent (OPA)** + **Rego** | `safety/opa_client.py` | 声明式策略引擎，用于实时风险评估和高危操作拦截。封锁名单 + 风险分级 + 议会投票三重防护 |
| **Arch Linux PKGBUILD** | `executor/code_gen.py` + `templates/` | 三阶段脚本设计（prepare → build → check）启发了 A2Alaw 的模板系统（pre_check → execute → post_verify），确保幂等性和可验证性 |
| **Jinja2 Template Engine** | `executor/code_gen.py` | 声明式模板编译，将结构化 Intent 转化为可执行 Bash 脚本 |
| **Redis Streams** | `feedback/redis_streams.py` | 7 通道事件总线（execute / audit / health / council 等），用于异步事件分发、Mesh 心跳和议会投票 |
| **systemd Transient Units** | `system/spawn-skill.sh` | 利用 `systemd-run` 为每个 OpenClaw 技能创建独立 cgroup，实现 CPU/内存隔离（CPUQuota=10%, MemoryMax=256M） |
| **WireGuard** | `mesh/peer.py` | 三节点全互联 VPN，承载心跳监控和 SSH 远程执行的安全通道 |
| **LiteLLM** | `orchestrator/agent.py` | 统一多 LLM 提供商接口，支持三级路由：Doubao（免费）→ Claude（复杂）→ MiniMax（兜底） |

<br>

## 实验记录

以下是 A2Alaw 从概念到部署的完整开发时间线。所有实验均在中央节点（43.163.225.27, OpenCloudOS 2 核 / 2G）上完成。

### Phase 1 — MVP 骨架 `2026-03-05`

| 时间 | 事件 | 结果 |
|------|------|------|
| 22:22 | 初始化项目骨架，建立 `pyproject.toml`、目录结构 | `5a34431` |
| 22:58 | 实现 NL Parser + Pipeline Runner + CLI 入口 | 基础流水线跑通，dry-run 可用 |
| 00:02 | 接入 FreeClaw 三级 LLM 路由 | Doubao 作为默认解析模型 |
| 00:16 | 启用 Docker 沙箱执行 | sandbox writable 模式可安装包 |

### Phase 2 — 安全层 + 多步编排 `2026-03-06 00:39–01:19`

| 时间 | 事件 | 结果 |
|------|------|------|
| 00:39 | 集成 OPA Rego 策略引擎 + Redis Streams + Rich TUI | 高危命令拦截验证通过 |
| 01:13 | 集成 smolagents CodeAgent | 复杂指令自动拆解为 DAG |
| 01:19 | Jinja2 模板系统 (PKGBUILD 三阶段) | 5 个模板：install_package / edit_file / restart_service / run_command / check_status |

### Phase 3 — 主机执行 + Mesh 自愈 `2026-03-06 02:00–03:00`

| 时间 | 事件 | 结果 |
|------|------|------|
| ~02:00 | 从 Docker 沙箱切换到主机直执行 | `executor/host.py` subprocess 模式 |
| ~02:00 | SSH 远程执行模块 | `executor/remote.py` 三节点 WireGuard mesh |
| ~02:30 | 环形互修拓扑 + 心跳监控 | central→sv→tokyo→central，30s 间隔 |
| ~02:30 | 自动诊断 + 5 种修复协议 | daemon / wireguard / redis / disk / memory |
| ~02:45 | 议会投票共识机制 | Redis Streams `mesh:council`，2/3 quorum |
| ~02:48 | **端到端测试通过** | `"安装 cowsay"` → 真实 apt install → Git audit commit |

### Phase 4 — 系统级 OpenClaw 部署 `2026-03-06 05:00–05:38`

| 时间 | 事件 | 结果 |
|------|------|------|
| 05:28 | 编写 6 个系统集成脚本 | systemize / service / update / rollback / spawn-skill / claw-skill |
| 05:34 | OpenClaw 迁移到 `/usr/lib/openclaw/slot-a/` | 双槽目录结构就位 |
| 05:35 | 系统级 systemd 服务启动 | `openclaw.service` active，端口 18789 |
| 05:35 | **遇到问题**：配置路径不兼容 | `OPENCLAW_CONFIG_PATH` 指向目录而非文件，qqbot channel 验证失败 |
| 05:38 | **解决方案**：回退配置路径到 `~/.openclaw/` | 服务运行正常，Dashboard 可访问。配置完全迁移留待后续 |

### Phase 5 — 发布 `2026-03-06 05:39–06:02`

| 时间 | 事件 | 结果 |
|------|------|------|
| 05:41 | 推送至 GitHub | https://github.com/2233admin/a2alaw |
| 05:44 | 品牌修正：ClawDebian → A2A Claw OS | 全文替换 |
| 06:02 | README 设计迭代 | 从 ASCII art 过度装饰 → 简洁现代风格 |

### 已知问题与后续计划

- **OpenClaw 配置迁移未完成**：`/etc/openclaw/openclaw.json` 中 qqbot channel 验证失败，当前回退到原路径
- **热更新未实测**：`openclaw-update.sh` 已编写但未在生产环境执行
- **硅谷 / 东京节点未部署**：Mesh 模块就绪，等待节点重装后部署
- **smolagents 多步编排缺少集成测试**：单步执行已验证，多步 DAG 需要更多测试用例

<br>

## License

MIT

<br>

<div align="center">

*この戦いに、言葉だけで十分だ。*

这场战斗，只需一句话就够了。

</div>
