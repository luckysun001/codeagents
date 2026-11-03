"""CodeAgent / PlanningAgent / ReviewAgent 具体实现测试

用最小 FakeLLM 替代真实模型，覆盖各 Agent 的 think / parse_tool_calls /
execute_tool_call 与实例化逻辑（这些具体实现未被 MockAgent 基类测试覆盖）。
"""
from codeagents.agents.code_agent import CodeAgent, PlanningAgent, ReviewAgent
from codeagents.core.schema import ToolCall
from codeagents.models.llm import BaseLLM


class FakeLLM(BaseLLM):
    def __init__(self, content="result"):
        super().__init__("fake-model")
        self._content = content
        self.chat_calls = 0

    def chat(self, messages, **kwargs):
        self.chat_calls += 1
        return {"content": self._content, "tool_calls": None, "usage": None}

    def chat_with_tools(self, messages, tools, **kwargs):
        return {"content": self._content, "tool_calls": [], "usage": None}


def test_planning_agent_think():
    llm = FakeLLM("step A\nstep B")
    agent = PlanningAgent(agent_id="p1", llm=llm)
    agent.init_context("build feature")
    out = agent.think()
    assert out == "step A\nstep B"
    assert llm.chat_calls == 1


def test_planning_agent_parse_and_execute():
    agent = PlanningAgent(agent_id="p2", llm=FakeLLM())
    assert agent.parse_tool_calls("anything") == []
    assert agent.execute_tool_call(ToolCall(id="x", name="y", arguments={})) is None


def test_review_agent_think():
    llm = FakeLLM("looks good")
    agent = ReviewAgent(agent_id="r1", llm=llm)
    agent.init_context("review this")
    assert agent.think() == "looks good"


def test_code_agent_instantiation():
    agent = CodeAgent(agent_id="c1", llm=FakeLLM())
    assert agent.llm is not None
    assert agent.name == "CodeAgent"
    assert agent.init_context("task") is not None
