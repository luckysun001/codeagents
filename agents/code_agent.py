"""代码智能体实现"""
from typing import List
from ..core.agent import BaseAgent
from ..core.schema import ToolCall, ToolResult, Role, MessageType
from ..models.llm import BaseLLM


class CodeAgent(BaseAgent):
    """代码智能体：专注于代码生成、审查、调试等任务"""

    DEFAULT_SYSTEM_PROMPT = """你是一个专业的代码助手，擅长编写、审查、调试和优化代码。

工作原则：
1. 先理解需求，再给出方案
2. 代码要符合最佳实践，有适当的注释
3. 遇到问题时，主动使用工具来获取更多信息
4. 对于复杂任务，分步骤解决
5. 保持代码的可读性和可维护性
"""

    def __init__(
        self,
        agent_id: str,
        name: str = "CodeAgent",
        description: str = "专注于代码任务的智能体",
        llm: BaseLLM = None,
        system_prompt: str = None,
        **kwargs,
    ):
        super().__init__(
            agent_id=agent_id,
            name=name,
            description=description,
            system_prompt=system_prompt or self.DEFAULT_SYSTEM_PROMPT,
            **kwargs,
        )
        self.llm = llm
        self._last_response = None

    def think(self) -> str:
        """思考：调用LLM决定下一步"""
        messages = self.get_messages()
        tools = self.tool_registry.to_openai_format()

        if tools:
            response = self.llm.chat_with_tools(messages, tools)
        else:
            response = self.llm.chat(messages)

        self._last_response = response
        return response["content"] or ""

    def parse_tool_calls(self, thinking: str) -> List[ToolCall]:
        """解析工具调用"""
        if not self._last_response or not self._last_response.get("tool_calls"):
            return []

        tool_calls = []
        for tc in self._last_response["tool_calls"]:
            tool_calls.append(
                ToolCall(
                    id=tc["id"],
                    name=tc["name"],
                    arguments=tc["arguments"],
                )
            )
        return tool_calls

    def execute_tool_call(self, tool_call: ToolCall) -> ToolResult:
        """执行工具"""
        try:
            result = self.tool_registry.execute(
                tool_call.name,
                tool_call.arguments,
            )
            return ToolResult(
                tool_call_id=tool_call.id,
                name=tool_call.name,
                content=str(result),
                is_error=False,
            )
        except Exception as e:
            return ToolResult(
                tool_call_id=tool_call.id,
                name=tool_call.name,
                content=f"Error: {str(e)}",
                is_error=True,
            )


class PlanningAgent(BaseAgent):
    """规划智能体：将复杂任务分解为子任务"""

    DEFAULT_SYSTEM_PROMPT = """你是一个任务规划专家。你的工作是将复杂任务分解为可执行的子任务。

分析任务，制定清晰的执行计划。每个子任务应该：
1. 有明确的目标
2. 是原子性的（不可再分）
3. 有依赖关系说明
4. 有预期的输出

按步骤思考，最终输出结构化的计划。"""

    def __init__(
        self,
        agent_id: str,
        name: str = "Planner",
        llm: BaseLLM = None,
        **kwargs,
    ):
        super().__init__(
            agent_id=agent_id,
            name=name,
            description="任务规划智能体",
            system_prompt=self.DEFAULT_SYSTEM_PROMPT,
            **kwargs,
        )
        self.llm = llm
        self._last_response = None

    def think(self) -> str:
        messages = self.get_messages()
        response = self.llm.chat(messages)
        self._last_response = response
        return response["content"] or ""

    def parse_tool_calls(self, thinking: str) -> List[ToolCall]:
        return []  # 规划智能体不使用工具

    def execute_tool_call(self, tool_call: ToolCall) -> ToolResult:
        pass  # 不需要实现


class ReviewAgent(BaseAgent):
    """审查智能体：负责代码审查和质量检查"""

    DEFAULT_SYSTEM_PROMPT = """你是一个严格的代码审查员。

审查标准：
1. 代码正确性：没有明显的bug
2. 代码风格：符合PEP8或语言规范
3. 安全性：没有明显的安全漏洞
4. 性能：没有明显的性能问题
5. 可维护性：代码清晰、有注释、有测试

给出具体的改进建议，不要含糊其辞。"""

    def __init__(
        self,
        agent_id: str,
        name: str = "Reviewer",
        llm: BaseLLM = None,
        **kwargs,
    ):
        super().__init__(
            agent_id=agent_id,
            name=name,
            description="代码审查智能体",
            system_prompt=self.DEFAULT_SYSTEM_PROMPT,
            **kwargs,
        )
        self.llm = llm
        self._last_response = None

    def think(self) -> str:
        messages = self.get_messages()
        response = self.llm.chat(messages)
        self._last_response = response
        return response["content"] or ""

    def parse_tool_calls(self, thinking: str) -> List[ToolCall]:
        return []

    def execute_tool_call(self, tool_call: ToolCall) -> ToolResult:
        pass
