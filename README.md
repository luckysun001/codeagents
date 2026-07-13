# CodeAgents - 代码多智能体框架

**面向软件开发全流程的轻量级多智能体协作框架。**
代码生成 · 代码审查 · 任务规划 · 多 Agent 编排

> **状态：Alpha (v0.1.0)** — 核心框架可用，部分高级特性仍在开发中。

---

## 核心特性

### 多 Agent 协作
- 3 个已实现的专业角色 Agent（CodeAgent / PlanningAgent / ReviewAgent）
- Agent 之间通过消息总线异步通信
- 支持顺序、并行、流水线三种编排模式

### 工具系统
- 装饰器 + 注册表模式，支持自动生成 function calling 格式
- 内置 19 个工具：文件操作（6 个）、代码分析（5 个）、Git 操作（8 个）
- 支持自定义工具注册

### LLM 适配
- 已实现 OpenAI（含兼容 API）和 Anthropic 两个 provider
- 统一的 `get_llm()` 工厂接口
- 通义千问、豆包等 provider 为 TODO

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
| Architect Agent | 架构设计、技术选型 | TODO |
| Debugger Agent | Bug 定位、根因分析 | TODO |
| Documenter Agent | 文档生成 | TODO |

---

## 项目结构

```text
codeagents/
├── setup.py                  # 包安装配置
├── pyproject.toml            # 项目配置
├── README.md
├── LICENSE
├── cli.py                    # CLI 入口 (codeagents 命令)
│
├── __init__.py               # 公开 API
├── core/                     # 核心抽象
│   ├── agent.py              # BaseAgent 抽象基类
│   └── schema.py             # 数据结构（Message, ToolCall, ToolResult 等）
├── agents/                   # Agent 实现
│   └── code_agent.py         # CodeAgent, PlanningAgent, ReviewAgent
├── orchestration/            # 编排层
│   ├── orchestrator.py       # 任务编排器（顺序/并行/流水线）
│   └── message_bus.py        # 消息总线（主题订阅/点对点/广播）
├── memory/                   # 记忆系统
│   └── memory.py             # JSON 文件记忆
├── tools/                    # 工具集
│   ├── registry.py           # 工具注册表（装饰器模式）
│   ├── file_tools.py         # 文件操作工具（6 个）
│   ├── code_tools.py         # 代码分析工具（5 个）
│   └── git_tools.py          # Git 操作工具（8 个）
├── models/                   # LLM 适配层
│   └── llm.py                # OpenAILLM, AnthropicLLM, get_llm
│
├── examples/                 # 示例代码
│   ├── 01_single_agent.py    # 单个 Agent 使用
│   ├── 02_multi_agent.py     # 多 Agent 协作
│   └── 03_custom_tools.py    # 自定义工具
│
└── tests/                    # 单元测试
    ├── test_memory.py        # 记忆系统测试
    ├── test_message_bus.py   # 消息总线测试
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

## 技术栈

- Python 3.9+
- openai >= 1.0.0（核心依赖）
- anthropic >= 0.18.0（可选）
- pytest / flake8 / mypy / black（开发依赖）

---

## 许可证

MIT License
