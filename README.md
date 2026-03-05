<div align="center">

```
     ___   ___    ___   _
    / _ \ |__ \  / _ \ | |
   | |_| |   ) || |_| || |  __ ___      __
   |  _  |  / / |  _  || | / _` \ \ /\ / /
   | | | | / /_ | | | || || (_| |\ V  V /
   |_| |_||____||_| |_||_| \__,_| \_/\_/
```

### 🌸 自然语言即系统调用 · AI原生服务器操作系统 🌸

*「ねえ、サーバーに話しかけるだけで、全部やってくれるんだよ？」*

*——就像对服务器说句话，它就会帮你把一切都搞定。*

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-pink.svg)](LICENSE)
[![ClawDebian](https://img.shields.io/badge/OS-ClawDebian-purple?logo=debian)](https://github.com)
[![OpenClaw](https://img.shields.io/badge/兼容-OpenClaw-orange)](https://github.com)

</div>

---

## ✨ A2Alaw 是什么？

A2Alaw（**Agent-to-Action Law**）不是又一个运维 CLI 工具。

她是一个 **AI 原生的服务器操作系统内核**——为 [ClawDebian](https://github.com) 集群量身定制的治理控制平面。你可以把她想象成服务器世界的「管家少女」：你用自然语言说出想做的事，她来理解、规划、审批、执行、审计，全链路自动化。

```
  你说：「给三台服务器都装上 nginx，配好反向代理」

  她做：
    📝 理解意图 → 拆解成 DAG 执行图
    🛡️ OPA 策略审查 → 风险评估
    ⚡ 在真实主机上执行 → 不是沙箱玩具
    📋 Git 自动审计 → 每次变更都有记录
    💬 Redis Streams 事件流 → 全程可观测
```

### 🎯 核心理念

> **「自然语言即系统调用」** —— NL = syscall

灵感来源于 [AIOS](https://arxiv.org/abs/2403.16971) 论文的三层架构，但我们走得更远：

```
┌─────────────────────────────────────────┐
│  🌐 App Layer                           │
│  OpenClaw Skills · CLI · Rich TUI       │
├─────────────────────────────────────────┤
│  🧠 Kernel Layer (a2alawd)              │
│  NL Parser → DAG → OPA → Host Execute  │
│  CLAW API Hub · Redis Streams Event Bus │
├─────────────────────────────────────────┤
│  ⚙️ Hardware Layer                       │
│  OS syscalls · systemd · WireGuard Mesh │
│  三节点对等自治 · 环形互修              │
└─────────────────────────────────────────┘
```

---

## 🌟 特性一览

### 🔥 主机直执行，不是玩具沙箱

```bash
# 真的在服务器上装了 nginx，不是 docker 里演戏
$ a2alawctl run! "安装 nginx 并重启服务"
Task a8f3b2: processed 'nginx' in 4017ms. System state was modified.
Audit: 331c6b1e75b31dd60f46ab95f455278b248613b7
```

### 🛡️ OPA 策略守护，高危必拦截

```bash
$ a2alawctl run! "rm -rf /"
BLOCKED by policy: Blocked pattern: rm -rf /
# 你的服务器安全了 ✨
```

### 🤖 smolagents 多步骤规划

```bash
$ a2alawctl agent! "安装 Redis，配置密码，设置开机自启"
# 自动拆解为 3 步 DAG：install → configure → enable
# 每步独立执行、独立审计
```

### 🌐 三节点对等 Mesh

```
  ┌──────────┐     ┌──────────┐     ┌──────────┐
  │ central  │────▶│    sv    │────▶│  tokyo   │
  │ 10.10.0.1│     │ 10.10.0.2│     │ 10.10.0.3│
  └────▲─────┘     └──────────┘     └────┬─────┘
       └──────────────────────────────────┘
                 环形互修 Ring
```

- **心跳监控**：每 30s 互 ping，3 次失败 = DOWN
- **自动诊断**：SSH 到故障节点运行 5 项检查
- **自动修复**：daemon / WireGuard / Redis / 磁盘 / 内存
- **议会投票**：2/3 多数同意才执行高风险操作

### 🏯 系统级 OpenClaw

OpenClaw 不再是 `npm i -g` 的客人——她是系统的一部分：

```
/usr/lib/openclaw/core → slot-a    # 双槽原子热更新
/etc/openclaw/                     # 系统级配置
/var/lib/openclaw/skills/          # 技能子进程隔离
/var/log/openclaw/                 # 统一日志管理
```

零停机热更新、30 秒自动回滚、技能依赖永不冲突。

---

## 🚀 快速开始

### 前置要求

- Debian 12 (ClawDebian)
- Python 3.11+
- Redis 7+
- Node.js 22+ (for OpenClaw)

### 安装

```bash
git clone https://github.com/anthropic-claw/a2alaw.git
cd a2alaw
pip3 install -r requirements.txt  # redis, rich, jinja2, httpx, smolagents

# 启动 a2alawd 守护进程
cp hub/a2alawd.service /etc/systemd/system/
systemctl enable --now a2alawd

# (可选) 系统级 OpenClaw 迁移
sudo bash system/openclaw-systemize.sh
```

### 使用

```bash
# 预览模式（不执行）
a2alawctl run "安装 htop"

# 真实执行
a2alawctl run! "安装 htop"

# 多步骤 AI 规划
a2alawctl agent! "安装 nginx 并配置反向代理到 8080"

# 交互式 TUI
a2alawctl interactive

# API 调用
curl -X POST http://127.0.0.1:8741/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"command": "查看磁盘使用率"}'
```

---

## 🏗️ 项目结构

```
a2alaw/
├── 🧠 orchestrator/          # 大脑：NL 理解 + DAG 规划
│   ├── nl_parser.py          #   三级 LLM 路由 (Doubao→Claude→MiniMax)
│   ├── dag_parser.py         #   Intent → 执行图 (拓扑排序)
│   ├── agent.py              #   smolagents CodeAgent 多步骤
│   └── risk_scorer.py        #   风险评估
│
├── ⚡ executor/               # 双手：执行引擎
│   ├── host.py               #   主机直接执行 (subprocess)
│   ├── remote.py             #   SSH 远程执行 (WireGuard mesh)
│   ├── code_gen.py           #   Jinja2 模板代码生成
│   ├── sandbox.py            #   Docker 沙箱 (dry-run 用)
│   ├── self_heal.py          #   错误分类 + 3 次重试
│   └── templates/            #   Arch PKGBUILD 风格模板
│       ├── install_package.sh.j2
│       ├── edit_file.sh.j2
│       ├── restart_service.sh.j2
│       ├── run_command.sh.j2
│       └── check_status.sh.j2
│
├── 🛡️ safety/                # 护盾：安全策略
│   ├── opa_client.py         #   OPA 策略引擎客户端
│   ├── opa_policies/base.rego #  Rego 安全规则
│   ├── git_audit.py          #   Git 自动审计
│   └── seccomp.json          #   44 syscall 黑名单
│
├── 🌐 mesh/                  # 神经网络：节点通信
│   ├── peer.py               #   节点身份 + 环形拓扑
│   ├── heartbeat.py          #   心跳监控 (HTTP + SSH fallback)
│   ├── healer.py             #   自动诊断 + 5 种修复脚本
│   └── council.py            #   议会投票 + 共识机制
│
├── 🏯 hub/                   # 内核：API 守护进程
│   ├── daemon.py             #   FastAPI (port 8741)
│   ├── a2alawd.service       #   systemd 服务
│   └── hub.yaml              #   Hub 配置
│
├── 🏛️ system/                # 系统级 OpenClaw 改造
│   ├── openclaw-systemize.sh #   一键迁移脚本
│   ├── openclaw.service      #   系统级 systemd 服务
│   ├── openclaw-update.sh    #   双槽热更新
│   ├── openclaw-rollback.sh  #   一键回滚
│   ├── spawn-skill.sh        #   技能子进程启动器
│   └── claw-skill.sh         #   技能包管理 CLI
│
├── 📡 feedback/              # 感知：事件流
│   ├── redis_streams.py      #   7 通道 Redis Streams
│   └── nl_report.py          #   自然语言报告生成
│
├── 🖥️ tui/                   # 容颜：交互界面
│   └── dialog.py             #   Rich TUI 对话
│
├── 📋 schemas/               # 契约：JSON Schema
├── 🔄 update/                # 更新：原子切换
├── pipeline.py               # 核心 7 级流水线
├── cli.py                    # CLI 入口 (a2alawctl)
└── docker-compose.yml        # Redis + PostgreSQL + OPA
```

---

## 🔮 七级流水线

每一条自然语言指令，都会经历完整的七级炼化：

```
  「安装 nginx」
       │
  P1 ──┤ NL → Intent        三级 LLM 路由，规则兜底
  P2 ──┤ Intent → DAG       拓扑排序，依赖推导
  P3 ──┤ OPA Policy Check   Rego 规则，黑名单拦截
  P4 ──┤ Code Generation    Jinja2 模板，Arch PKGBUILD 风格
  P5 ──┤ Host Execution     真实主机执行，不是沙箱
  P6 ──┤ Self-Heal          错误分类，3 次重试，人工兜底
  P7 ──┤ Audit + Report     Git commit + Redis Streams + NL 报告
       │
  「Task a8f3b2: nginx installed successfully in 4.0s」
```

---

## 🎭 Jinja2 模板：Arch PKGBUILD 的哲学

每个 Skill 模板都遵循 Arch Linux 的三阶段设计哲学：

```bash
# ── Phase 1: pre_check ──     跳过已完成的操作（幂等）
# ── Phase 2: execute ──       执行核心操作
# ── Phase 3: post_verify ──   验证执行结果
```

声明式、幂等、可验证。像 PKGBUILD 一样优雅。

---

## 🤝 与 OpenClaw 的关系

A2Alaw **深度兼容** OpenClaw，但她们是不同的存在：

| | OpenClaw | A2Alaw |
|---|---|---|
| 定位 | AI 聊天网关 | 服务器治理 OS |
| 语言 | Node.js/TypeScript | Python |
| 执行 | 技能路由 + 对话 | 主机系统变更 |
| 关系 | A2Alaw 让 OpenClaw 成为系统级基础设施 |

OpenClaw 是嘴，A2Alaw 是手。她们一起，让服务器听懂你说的每一句话。

---

## 📜 License

MIT

---

<div align="center">

*Built with 💜 for ClawDebian*

*「全ての始まりは、一つの言葉から」*

*—— 一切的开始，源于一句话。*

</div>
