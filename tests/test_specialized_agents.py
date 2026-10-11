"""扩展角色 Agent 测试（Architect / Debugger / Documenter）

使用 FakeLLM 驱动，不依赖真实 API。
"""
import pytest

from codeagents.agents.llm_tool_agent import LLMToolAgent
from codeagents.agents.specialized_agents import (
    ArchitectAgent,
    DebuggerAgent,
    DocumenterAgent,
)
from codeagents.core.schema import AgentStatus, Role
from codeagents.tools.registry import ToolRegistry, tool


class FakeLLM:
    """按顺序返回预设响应的假 LLM"""

    def __init__(self, contents=None, tool_calls=None):
        self._contents = list(contents or ["ok"])
        self._tool_calls = list(tool_calls or [])
        self._idx = 0
        self.chat_calls = []
        self.chat_with_tools_calls = []

    def chat(self, messages, **kwargs):
        self.chat_calls.append(messages)
        return {"content": self._next(), "tool_calls": None, "usage": None}

    def chat_with_tools(self, messages, tools, **kwargs):
        self.chat_with_tools_calls.append((messages, tools))
        return {
            "content": self._next(),
            "tool_calls": self._tool_calls,
            "usage": None,
        }

    def _next(self):
        content = self._contents[min(self._idx, len(self._contents) - 1)]
        self._idx += 1
        return content


@tool(name="fake_probe", description="探测用工具", category="test")
def fake_probe(target: str = ".") -> str:
    return f"probe:{target}"


def make_registry():
    registry = ToolRegistry()
    registry.register(fake_probe)
    return registry


class TestAgentDefinitions:
    """角色定义与继承关系"""

    def test_all_subclass_llm_tool_agent(self):
        for cls in (ArchitectAgent, DebuggerAgent, DocumenterAgent):
            assert issubclass(cls, LLMToolAgent)

    @pytest.mark.parametrize(
        "cls,expected_name",
        [
            (ArchitectAgent, "Architect"),
            (DebuggerAgent, "Debugger"),
            (DocumenterAgent, "Documenter"),
        ],
    )
    def test_default_name_and_system_prompt(self, cls, expected_name):
        agent = cls(agent_id=f"{expected_name.lower()}-1", llm=FakeLLM())
        assert agent.name == expected_name
        assert agent.system_prompt  # 每个角色都有专属 prompt
        assert agent.llm is not None

    def test_custom_system_prompt_overrides_default(self):
        agent = DebuggerAgent(
            agent_id="dbg-1", llm=FakeLLM(), system_prompt="只回答根因"
        )
        assert agent.system_prompt == "只回答根因"

    def test_prompts_are_role_specific(self):
        prompts = {
            cls.DEFAULT_SYSTEM_PROMPT
            for cls in (ArchitectAgent, DebuggerAgent, DocumenterAgent)
        }
        assert len(prompts) == 3  # 三个角色的 prompt 互不相同


class TestAgentExecution:
    """think-act 循环"""

    def test_run_without_tools_uses_chat(self):
        llm = FakeLLM(contents=["架构方案：分三层"])
        agent = ArchitectAgent(agent_id="arch-1", llm=llm)

        ctx = agent.run("设计一个短链服务的架构")

        assert ctx.status == AgentStatus.FINISHED
        assert len(llm.chat_calls) == 1
        assert llm.chat_with_tools_calls == []
        # system prompt + task + assistant 回复
        assert len(ctx.messages) == 3
        assert ctx.messages[0].role == Role.SYSTEM
        assert ctx.messages[-1].content == "架构方案：分三层"

    def test_run_with_tools_uses_function_calling(self):
        llm = FakeLLM(
            contents=["先看一下目录结构", "结论：问题在 parser.py 第 42 行"],
            tool_calls=[{"id": "call-1", "name": "fake_probe", "arguments": {"target": "src"}}],
        )
        agent = DebuggerAgent(
            agent_id="dbg-1", llm=llm, tool_registry=make_registry(), max_steps=3
        )

        ctx = agent.run("pytest 挂了，帮我定位")

        assert ctx.status == AgentStatus.FINISHED
        # 第一步走 function calling，第二步无工具调用后结束
        assert len(llm.chat_with_tools_calls) >= 1
        tool_results = [m for m in ctx.messages if m.tool_result is not None]
        assert tool_results
        assert tool_results[0].tool_result.content == "probe:src"
        assert tool_results[0].tool_result.is_error is False

    def test_tool_execution_error_is_captured(self):
        class BrokenLLM(FakeLLM):
            def chat_with_tools(self, messages, tools, **kwargs):
                super().chat_with_tools(messages, tools, **kwargs)
                return {
                    "content": "",
                    "tool_calls": [
                        {"id": "c", "name": "not_exist", "arguments": {}}
                    ],
                    "usage": None,
                }

        agent = DocumenterAgent(
            agent_id="doc-1", llm=BrokenLLM(), tool_registry=make_registry(), max_steps=2
        )
        ctx = agent.run("生成 README")

        tool_results = [m for m in ctx.messages if m.tool_result is not None]
        assert tool_results[0].tool_result.is_error is True
        assert "Error" in tool_results[0].tool_result.content

    def test_max_steps_is_respected(self):
        # 工具调用一直返回同一个调用，靠 max_steps 终止
        llm = FakeLLM(
            contents=["继续"],
            tool_calls=[{"id": "c", "name": "fake_probe", "arguments": {}}],
        )
        agent = DebuggerAgent(
            agent_id="dbg-2", llm=llm, tool_registry=make_registry(), max_steps=2
        )
        ctx = agent.run("死循环测试")
        assert ctx.current_step <= 2
        assert ctx.status == AgentStatus.FINISHED
