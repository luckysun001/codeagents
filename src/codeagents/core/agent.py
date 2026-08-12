"""智能体基类"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
from .schema import (
    Message,
    AgentContext,
    AgentStatus,
    Role,
    MessageType,
    ToolCall,
    ToolResult,
)
from ..memory import Memory
from ..tools import ToolRegistry


class BaseAgent(ABC):
    """智能体抽象基类"""

    def __init__(
        self,
        agent_id: str,
        name: str,
        description: str = "",
        system_prompt: str = "",
        memory: Optional[Memory] = None,
        tool_registry: Optional[ToolRegistry] = None,
        max_steps: int = 10,
    ):
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.memory = memory or Memory()
        self.tool_registry = tool_registry or ToolRegistry()
        self.max_steps = max_steps
        self.context: Optional[AgentContext] = None
        self._callbacks: Dict[str, List[Callable]] = {
            "on_message": [],
            "on_tool_call": [],
            "on_tool_result": [],
            "on_status_change": [],
        }

    def on(self, event: str, callback: Callable):
        """注册事件回调"""
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def _emit(self, event: str, *args, **kwargs):
        """触发事件"""
        for callback in self._callbacks.get(event, []):
            callback(*args, **kwargs)

    def init_context(self, task: str) -> AgentContext:
        """初始化执行上下文"""
        self.context = AgentContext(
            agent_id=self.agent_id,
            task=task,
            max_steps=self.max_steps,
        )

        # 添加系统提示
        if self.system_prompt:
            self.add_message(Role.SYSTEM, self.system_prompt)

        # 添加任务消息
        self.add_message(Role.USER, task)

        return self.context

    def add_message(
        self,
        role: Role,
        content: str,
        message_type: MessageType = MessageType.TEXT,
        tool_calls: List[ToolCall] = None,
        tool_result: ToolResult = None,
        metadata: Dict[str, Any] = None,
    ) -> Message:
        """添加消息到上下文"""
        message = Message(
            role=role,
            content=content,
            type=message_type,
            tool_calls=tool_calls or [],
            tool_result=tool_result,
            metadata=metadata or {},
        )
        self.context.messages.append(message)
        self._emit("on_message", message)
        return message

    def set_status(self, status: AgentStatus):
        """设置智能体状态"""
        self.context.status = status
        self._emit("on_status_change", status)

    @abstractmethod
    def think(self) -> str:
        """思考阶段：决定下一步做什么"""
        pass

    @abstractmethod
    def execute_tool_call(self, tool_call: ToolCall) -> ToolResult:
        """执行工具调用"""
        pass

    @abstractmethod
    def parse_tool_calls(self, thinking: str) -> List[ToolCall]:
        """从思考结果中解析工具调用"""
        pass

    def step(self) -> bool:
        """执行一步，返回是否应该继续"""
        if not self.context:
            raise RuntimeError("Context not initialized. Call init_context() first.")

        if self.context.current_step >= self.context.max_steps:
            self.set_status(AgentStatus.FINISHED)
            return False

        self.set_status(AgentStatus.THINKING)

        # 思考阶段
        thinking_result = self.think()
        self.add_message(
            Role.ASSISTANT,
            thinking_result,
            MessageType.THINKING,
            metadata={"step": self.context.current_step},
        )

        # 解析工具调用
        tool_calls = self.parse_tool_calls(thinking_result)

        if not tool_calls:
            # 没有工具调用，结束
            self.set_status(AgentStatus.FINISHED)
            return False

        # 执行工具
        self.set_status(AgentStatus.RUNNING_TOOL)
        for tool_call in tool_calls:
            self._emit("on_tool_call", tool_call)
            result = self.execute_tool_call(tool_call)
            self._emit("on_tool_result", result)

            self.add_message(
                Role.TOOL,
                result.content,
                MessageType.TOOL_RESULT,
                tool_result=result,
                metadata={"tool_name": result.name},
            )

        self.context.current_step += 1
        return True

    def run(self, task: str) -> AgentContext:
        """运行智能体直到完成"""
        self.init_context(task)

        while self.step():
            pass

        # 保存到记忆
        self.memory.add_conversation(
            conversation_id=self.context.id if hasattr(self.context, "id") else self.agent_id,
            messages=[m.to_dict() for m in self.context.messages],
            metadata={"task": task},
        )

        return self.context

    def get_messages(self) -> List[Dict[str, Any]]:
        """获取格式化的消息列表供LLM使用"""
        messages = []
        for msg in self.context.messages:
            if msg.type == MessageType.TOOL_RESULT:
                messages.append({
                    "role": "tool",
                    "tool_call_id": msg.tool_result.tool_call_id,
                    "content": msg.content,
                })
            elif msg.tool_calls:
                messages.append({
                    "role": "assistant",
                    "content": msg.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": tc.name, "arguments": tc.arguments},
                        }
                        for tc in msg.tool_calls
                    ],
                })
            else:
                messages.append({"role": msg.role.value, "content": msg.content})
        return messages
