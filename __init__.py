"""CodeAgents - 面向代码的轻量级多智能体框架"""

__version__ = "0.1.0"
__author__ = "CodeAgents Team"

# 核心
from .core.schema import Message, Role, MessageType, ToolCall, ToolResult, AgentStatus
from .core.agent import BaseAgent

# 智能体
from .agents.code_agent import CodeAgent, PlanningAgent, ReviewAgent

# 记忆系统
from .memory.memory import Memory

# 工具系统
from .tools.registry import Tool, ToolRegistry, tool
from .tools.file_tools import get_file_tools
from .tools.code_tools import get_code_tools
from .tools.git_tools import get_git_tools

# 模型
from .models.llm import BaseLLM, OpenAILLM, AnthropicLLM, get_llm

# 编排
from .orchestration.message_bus import MessageBus, SharedContext, MessagePriority
from .orchestration.orchestrator import (
    Orchestrator,
    Task,
    Workflow,
    ExecutionMode,
    TaskStatus,
)


def create_tool_registry(include: list = None) -> ToolRegistry:
    """创建工具注册表

    Args:
        include: 要包含的工具类型，可选值: ["file", "code", "git"]
                 None 表示包含全部
    """
    registry = ToolRegistry()

    if include is None or "file" in include:
        for t in get_file_tools().list_tools():
            registry.register(t)

    if include is None or "code" in include:
        for t in get_code_tools().list_tools():
            registry.register(t)

    if include is None or "git" in include:
        for t in get_git_tools().list_tools():
            registry.register(t)

    return registry


__all__ = [
    # 核心
    "Message",
    "Role",
    "MessageType",
    "ToolCall",
    "ToolResult",
    "AgentStatus",
    "BaseAgent",
    # 智能体
    "CodeAgent",
    "PlanningAgent",
    "ReviewAgent",
    # 记忆
    "Memory",
    # 工具
    "Tool",
    "ToolRegistry",
    "tool",
    "get_file_tools",
    "get_code_tools",
    "get_git_tools",
    "create_tool_registry",
    # 模型
    "BaseLLM",
    "OpenAILLM",
    "AnthropicLLM",
    "get_llm",
    # 编排
    "MessageBus",
    "SharedContext",
    "MessagePriority",
    "Orchestrator",
    "Task",
    "Workflow",
    "ExecutionMode",
    "TaskStatus",
]
