# CodeAgents - 代码多智能体框架

**面向软件开发全流程的轻量级多智能体协作框架。**
代码生成 · 代码审查 · 任务规划 · 多 Agent 编排

[![CI](https://github.com/luckysun001/codeagents/actions/workflows/ci.yml/badge.svg)](https://github.com/luckysun001/codeagents/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12-blue)
![License](https://img.shields.io/badge/license-MIT-green)

> **状态：Alpha (v0.1.0)** — 核心框架可用：6 个 Agent 角色、19 个内置工具、
> 4 个 LLM provider（OpenAI 兼容 / Anthropic / 通义千问 / 豆包）、三种编排模式均已实现。

---

## 核心特性

### 多 Agent 协作
- 6 个已实现的专业角色 Agent：CodeAgent / PlanningAgent / ReviewAgent /
  ArchitectAgent / DebuggerAgent / DocumenterAgent
- Agent 之间通过消息总线异步通信
- 支持顺序、并行、流水线三种编排模式

### 工具系统
- 装饰器 + 注册表模式，支持自动生成 function calling 格式
- 内置 19 个工具：文件操作（6 个）、代码分析（5 个）、Git 操作（8 个）
- 支持自定义工具注册

### LLM 适配
- 4 个 provider：`openai`（含任何 OpenAI 兼容服务）、`anthropic`、
  `qwen`（通义千问 DashScope）、`doubao`（豆包火山方舟）
- 统一的 `get_llm()` 工厂接口，后两者复用 OpenAI 兼容协议，
  只需配置对应的 API Key 环境变量即可（见下表）
- function calling 与工具调用解析开箱可用

| provider | `get_llm()` 名称 | 默认 Base URL | API Key 环境变量 |
|---|---|---|---|
| OpenAI | `openai` | —（官方） | `OPENAI_API_KEY` |
| Anthropic | `anthropic` | —（官方） | `ANTHROPIC_API_KEY` |
| 通义千问 | `qwen` / `dashscope` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `DASHSCOPE_API_KEY` |
| 豆包 | `doubao` / `ark` | `https://ark.cn-beijing.volces.com/api/v3` | `ARK_API_KEY` |

### 记忆系统
- 基于 JSON 文件的对话记忆和知识库存储
- 支持上下文注入和历史检索

---

## Agent 角色

| Agent | 职责 | 状态 |
|---|---|---|
| **CodeAgent** | 代码生成、功能实现、文件操作 | 已实现 |
| **PlanningAgent** | 任务拆分、步骤规划 | 已实现 |
| **ReviewAgent** | 代码审查、质量评估 | 已实现 |
| **ArchitectAgent** | 架构设计、技术选型、方案取舍 | 已实现 |
| **DebuggerAgent** | Bug 定位、根因分析、回归验证 | 已实现 |
| **DocumenterAgent** | 文档生成与维护 | 已实现 |

前三者之外，Architect / Debugger / Documenter 同样支持工具调用
（都继承自 `LLMToolAgent`，注册了工具就自动走 function calling）。

---

## 项目结构

```text
codeagents/
├── setup.py                  # 包安装配置
├── pyproject.toml            # 项目配置
├── README.md
├── LICENSE
│
├── src/codeagents/           # 源码包（src-layout）
│   ├── __init__.py           # 公开 API
│   ├── cli.py                # CLI 入口 (codeagents 命令)
│   ├── core/                 # 核心抽象
│   │   ├── agent.py          # BaseAgent 抽象基类
│   │   └── schema.py         # 数据结构（Message, ToolCall, ToolResult 等）
│   ├── agents/               # Agent 实现
│   │   ├── llm_tool_agent.py     # LLMToolAgent：带工具调用的 LLM Agent 基类
│   │   ├── code_agent.py         # CodeAgent, PlanningAgent, ReviewAgent
│   │   └── specialized_agents.py # ArchitectAgent, DebuggerAgent, DocumenterAgent
│   ├── orchestration/        # 编排层
│   │   ├── orchestrator.py   # 任务编排器（顺序/并行/流水线）
│   │   └── message_bus.py    # 消息总线（主题订阅/点对点/广播）
│   ├── memory/               # 记忆系统
│   │   └── memory.py         # JSON 文件记忆
│   ├── tools/                # 工具集（共 19 个）
│   │   ├── registry.py       # 工具注册表（装饰器模式）
│   │   ├── file_tools.py     # 文件操作（6 个）
│   │   ├── code_tools.py     # 代码分析（5 个）
│   │   └── git_tools.py      # Git 操作（8 个）
│   ├── models/               # LLM 适配层
│   │   └── llm.py            # OpenAILLM, AnthropicLLM, get_llm
│   └── examples/             # 示例代码
│       ├── 01_single_agent.py
│       ├── 02_multi_agent.py
│       └── 03_custom_tools.py
│
└── tests/                    # 单元测试
    ├── test_agent.py         # Agent 行为测试
    ├── test_llm_providers.py # LLM provider 与工厂函数测试
    ├── test_memory.py        # 记忆系统测试
    ├── test_message_bus.py   # 消息总线测试
    ├── test_orchestrator.py  # 编排器测试
    ├── test_registry.py      # 工具注册表测试
    ├── test_specialized_agents.py # Architect/Debugger/Documenter 测试
    └── test_tools.py         # 工具系统测试
```

---

## 快速开始

### 安装

```bash
cd 02-agent-frameworks/codeagents
pip install -e .
```

### 配置环境变量

```bash
# 设置 API Key
export OPENAI_API_KEY="your-api-key"
# 或使用兼容 API
export OPENAI_BASE_URL="http://localhost:8000/v1"
```

### 示例：单个 Agent

```python
from codeagents import CodeAgent, get_llm, create_tool_registry

# 1. 初始化 LLM
llm = get_llm(provider="openai", model="gpt-4o")

# 2. 创建工具注册表
tool_registry = create_tool_registry()

# 3. 创建 Agent
agent = CodeAgent(
    agent_id="coder-1",
    name="Python Coder",
    llm=llm,
    tool_registry=tool_registry,
    max_steps=5,
)

# 4. 运行
context = agent.run("实现一个快速排序函数，写入 sorting.py")
print(f"状态: {context.status}, 步数: {context.current_step}")
```

### 示例：多 Agent 编排

```python
from codeagents import (
    CodeAgent, PlanningAgent, ReviewAgent,
    Orchestrator, get_llm, ExecutionMode,
)

llm = get_llm(provider="openai", model="gpt-4o")

# 1. 创建编排器
orchestrator = Orchestrator()

# 2. 注册 Agent
orchestrator.register_agent(PlanningAgent(agent_id="planner", llm=llm))
orchestrator.register_agent(CodeAgent(agent_id="coder", llm=llm))
orchestrator.register_agent(ReviewAgent(agent_id="reviewer", llm=llm))

# 3. 创建任务和 workflow
task1 = orchestrator.create_task("分析需求并拆分任务", assigned_agent_id="planner")
task2 = orchestrator.create_task("实现 Todo List 核心功能", assigned_agent_id="coder", dependencies=[task1.task_id])
task3 = orchestrator.create_task("审查代码质量", assigned_agent_id="reviewer", dependencies=[task2.task_id])

workflow = orchestrator.create_workflow(
    name="Todo List CLI",
    tasks=[task1, task2, task3],
    mode=ExecutionMode.PIPELINE,
)

# 4. 运行
result = orchestrator.run_workflow(workflow)
print(orchestrator.get_workflow_summary(result))
```

更多示例见 `examples/` 目录。

---

## 运行测试

```bash
pytest tests/ -v
```

---

## 🔗 相关项目

本仓库是「**通用代码 Agent 框架**」，不绑定具体行业。

如果你关心「**Agent 在垂直行业（银行审计）里怎么落地**」，推荐作者的另一个开源项目：

> ### 🏦 [银行审计多智能体平台（bank-audit-agents）](https://github.com/luckysun001/bank-audit-agents)
> 5 个审计角色 Agent + 编排器 + 三种审计流水线；配套的
> [audit-rag](https://github.com/luckysun001/audit-rag) 提供法规与合同的检索增强能力。

想系统学习多智能体背后的原理，另见 [AI-Learning-Playground](https://github.com/luckysun001/AI-Learning-Playground)。

---

## 技术栈

- Python 3.11+（CI 覆盖 3.11 / 3.12）
- openai >= 1.0.0（核心依赖）
- anthropic >= 0.18.0（可选）
- pytest / flake8 / mypy / black（开发依赖）

---

## 许可证

MIT License
