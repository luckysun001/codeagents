"""带工具调用能力的 LLM Agent 基类"""
from typing import List

from ..core.agent import BaseAgent
from ..core.schema import ToolCall, ToolResult
from ..models.llm import BaseLLM


class LLMToolAgent(BaseAgent):
    """使用 LLM 驱动、并按 LLM 返回决定是否调用工具的 Agent 基类

    子类只需提供 ``DEFAULT_SYSTEM_PROMPT``，即可获得：
    - ``think()``：有工具时走 function calling，无工具时走普通对话
    - ``parse_tool_calls()``：把 LLM 返回的工具调用转为框架内部的 ``ToolCall``
    - ``execute_tool_call()``：执行工具并把异常收敛为 ``ToolResult(is_error=True)``
    """

    DEFAULT_SYSTEM_PROMPT = ""

    def __init__(
        self,
        agent_id: str,
        name: str = "LLMAgent",
        description: str = "",
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
