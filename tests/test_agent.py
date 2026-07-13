"""BaseAgent 核心逻辑测试

使用 Mock LLM 验证 think-act 循环、上下文管理、回调机制、步数限制等。
"""
import pytest
from unittest.mock import MagicMock, patch
from codeagents.core.agent import BaseAgent
from codeagents.core.schema import (
    Message, Role, MessageType, ToolCall, ToolResult,
    AgentContext, AgentStatus,
)
from codeagents.tools.registry import ToolRegistry, Tool, tool, ToolDefinition, ToolParameter


class MockAgent(BaseAgent):
    """用于测试的 Mock Agent，可控的 think/parse/execute 行为"""

    def __init__(self, think_responses=None, tool_calls_map=None, **kwargs):
        super().__init__(**kwargs)
        self._think_responses = think_responses or []
        self._call_index = 0
        self._tool_calls_map = tool_calls_map or {}

    def think(self) -> str:
        if self._call_index < len(self._think_responses):
            resp = self._think_responses[self._call_index]
            self._call_index += 1
            return resp
        return "done"

    def parse_tool_calls(self, thinking: str):
        return self._tool_calls_map.get(thinking, [])

    def execute_tool_call(self, tool_call: ToolCall) -> ToolResult:
        return ToolResult(
            tool_call_id=tool_call.id,
            name=tool_call.name,
            content=f"mock result for {tool_call.name}",
            is_error=False,
        )


class TestAgentContext:
    """测试上下文初始化"""

    def test_init_context_creates_system_and_user_messages(self):
        agent = MockAgent(
            agent_id="test-1",
            name="TestAgent",
            system_prompt="You are a test agent.",
        )
        ctx = agent.init_context("do something")

        assert ctx.agent_id == "test-1"
        assert ctx.task == "do something"
        assert ctx.status == AgentStatus.IDLE
        assert ctx.current_step == 0
        # system prompt + user task = 2 messages
        assert len(ctx.messages) == 2
        assert ctx.messages[0].role == Role.SYSTEM
        assert ctx.messages[0].content == "You are a test agent."
        assert ctx.messages[1].role == Role.USER
        assert ctx.messages[1].content == "do something"

    def test_init_context_without_system_prompt(self):
        agent = MockAgent(agent_id="test-2", name="TestAgent")
        ctx = agent.init_context("hello")
        assert len(ctx.messages) == 1
        assert ctx.messages[0].role == Role.USER


class TestStepLoop:
    """测试 think-act 循环"""

    def test_step_without_tool_calls_finishes(self):
        agent = MockAgent(
            agent_id="test-3",
            name="TestAgent",
            think_responses=["I'm done, no tools needed."],
            tool_calls_map={"I'm done, no tools needed.": []},
            max_steps=5,
        )
        agent.init_context("test task")
        should_continue = agent.step()

        assert should_continue is False
        assert agent.context.status == AgentStatus.FINISHED

    def test_step_with_tool_calls_continues(self):
        tool_call = ToolCall(id="tc-1", name="read_file", arguments={"path": "test.py"})
        agent = MockAgent(
            agent_id="test-4",
            name="TestAgent",
            think_responses=["Let me read the file.", "Done."],
            tool_calls_map={
                "Let me read the file.": [tool_call],
                "Done.": [],
            },
            max_steps=5,
        )
        agent.init_context("read a file")

        # First step: has tool call, should continue
        should_continue = agent.step()
        assert should_continue is True
        assert agent.context.current_step == 1

        # Second step: no tool call, should finish
        should_continue = agent.step()
        assert should_continue is False
        assert agent.context.status == AgentStatus.FINISHED

    def test_max_steps_limit(self):
        tool_call = ToolCall(id="tc-1", name="loop", arguments={})
        agent = MockAgent(
            agent_id="test-5",
            name="TestAgent",
            think_responses=["keep going"] * 100,
            tool_calls_map={"keep going": [tool_call]},
            max_steps=3,
        )
        agent.init_context("loop task")

        # Should stop after max_steps iterations
        agent.run("loop task")
        assert agent.context.current_step == 3
        assert agent.context.status == AgentStatus.FINISHED

    def test_step_without_context_raises(self):
        agent = MockAgent(agent_id="test-6", name="TestAgent")
        with pytest.raises(RuntimeError, match="Context not initialized"):
            agent.step()


class TestCallbacks:
    """测试事件回调机制"""

    def test_on_message_callback(self):
        messages_received = []
        agent = MockAgent(
            agent_id="test-7",
            name="TestAgent",
            system_prompt="You are a test agent.",
            think_responses=["done"],
            tool_calls_map={"done": []},
        )
        agent.on("on_message", lambda msg: messages_received.append(msg))
        agent.run("test")

        # system + user + thinking message = at least 3
        assert len(messages_received) >= 3

    def test_on_tool_call_and_result_callbacks(self):
        tool_calls_received = []
        tool_results_received = []
        tool_call = ToolCall(id="tc-1", name="read_file", arguments={"path": "x.py"})
        agent = MockAgent(
            agent_id="test-8",
            name="TestAgent",
            think_responses=["read it", "done"],
            tool_calls_map={"read it": [tool_call], "done": []},
        )
        agent.on("on_tool_call", lambda tc: tool_calls_received.append(tc))
        agent.on("on_tool_result", lambda tr: tool_results_received.append(tr))
        agent.run("test task")

        assert len(tool_calls_received) == 1
        assert tool_calls_received[0].name == "read_file"
        assert len(tool_results_received) == 1
        assert "mock result" in tool_results_received[0].content

    def test_on_status_change_callback(self):
        status_changes = []
        agent = MockAgent(
            agent_id="test-9",
            name="TestAgent",
            think_responses=["done"],
            tool_calls_map={"done": []},
        )
        agent.on("on_status_change", lambda s: status_changes.append(s))
        agent.run("test")

        assert AgentStatus.THINKING in status_changes
        assert AgentStatus.FINISHED in status_changes


class TestRunFullLoop:
    """测试完整 run 流程"""

    def test_run_returns_context(self):
        agent = MockAgent(
            agent_id="test-10",
            name="TestAgent",
            think_responses=["done"],
            tool_calls_map={"done": []},
        )
        ctx = agent.run("test task")
        assert isinstance(ctx, AgentContext)
        assert ctx.task == "test task"
        assert ctx.status == AgentStatus.FINISHED

    def test_run_with_multiple_tool_calls(self):
        calls = [
            ToolCall(id=f"tc-{i}", name="step", arguments={})
            for i in range(3)
        ]
        agent = MockAgent(
            agent_id="test-11",
            name="TestAgent",
            think_responses=["step1", "step2", "step3", "done"],
            tool_calls_map={
                "step1": [calls[0]],
                "step2": [calls[1]],
                "step3": [calls[2]],
                "done": [],
            },
            max_steps=10,
        )
        ctx = agent.run("multi-step task")
        assert ctx.current_step == 3
        # system + user + 3 thinking + 3 tool results = 8 messages
        assert len(ctx.messages) == 8

    def test_get_messages_format(self):
        tool_call = ToolCall(id="tc-1", name="read_file", arguments={"path": "x.py"})
        agent = MockAgent(
            agent_id="test-12",
            name="TestAgent",
            system_prompt="You are a test agent.",
            think_responses=["read it", "done"],
            tool_calls_map={"read it": [tool_call], "done": []},
        )
        agent.run("test")
        formatted = agent.get_messages()

        # Should have system, user, assistant, tool, assistant messages
        roles = [m["role"] for m in formatted]
        assert "system" in roles
        assert "user" in roles
        assert "tool" in roles
