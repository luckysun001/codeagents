"""核心数据结构定义"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from datetime import datetime
import uuid


class Role(str, Enum):
    """消息角色"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class MessageType(str, Enum):
    """消息类型"""
    TEXT = "text"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    THINKING = "thinking"
    OBSERVATION = "observation"


@dataclass
class ToolCall:
    """工具调用"""
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class ToolResult:
    """工具执行结果"""
    tool_call_id: str
    name: str
    content: str
    is_error: bool = False


@dataclass
class Message:
    """消息数据结构"""
    role: Role
    content: str
    type: MessageType = MessageType.TEXT
    tool_calls: List[ToolCall] = field(default_factory=list)
    tool_result: Optional[ToolResult] = None
    timestamp: datetime = field(default_factory=datetime.now)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role.value,
            "content": self.content,
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


class AgentStatus(str, Enum):
    """智能体状态"""
    IDLE = "idle"
    THINKING = "thinking"
    RUNNING_TOOL = "running_tool"
    WAITING = "waiting"
    FINISHED = "finished"
    ERROR = "error"


@dataclass
class AgentContext:
    """智能体执行上下文"""
    agent_id: str
    task: str
    messages: List[Message] = field(default_factory=list)
    status: AgentStatus = AgentStatus.IDLE
    current_step: int = 0
    max_steps: int = 10
    metadata: Dict[str, Any] = field(default_factory=dict)
