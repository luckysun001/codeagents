"""Orchestrator 多智能体编排测试

验证顺序/并行/流水线三种执行模式、任务依赖、回调机制。
"""
import pytest
from unittest.mock import MagicMock
from codeagents.orchestration.orchestrator import (
    Orchestrator, Task, Workflow,
    ExecutionMode, TaskStatus,
)
from codeagents.orchestration.message_bus import MessageBus, SharedContext
from codeagents.core.agent import BaseAgent
from codeagents.core.schema import AgentContext, AgentStatus


class MockAgent(BaseAgent):
    """Mock Agent，记录调用并返回简单结果"""

    def __init__(self, agent_id, name="Mock", run_result=None, **kwargs):
        super().__init__(agent_id=agent_id, name=name, **kwargs)
        self._run_result = run_result or "mock result"
        self.call_count = 0

    def think(self):
        return "done"

    def parse_tool_calls(self, thinking):
        return []

    def execute_tool_call(self, tool_call):
        pass

    def run(self, task: str) -> AgentContext:
        self.call_count += 1
        self.init_context(task)
        self.set_status(AgentStatus.FINISHED)
        self.context.metadata["result"] = self._run_result
        return self.context


class TestOrchestratorBasics:
    """测试编排器基础功能"""

    def test_register_and_get_agent(self):
        orch = Orchestrator()
        agent = MockAgent(agent_id="a1", name="Agent1")
        orch.register_agent(agent)

        assert orch.get_agent("a1") is agent
        assert orch.get_agent("nonexistent") is None

    def test_list_agents(self):
        orch = Orchestrator()
        orch.register_agent(MockAgent(agent_id="a1", name="Agent1", description="First"))
        orch.register_agent(MockAgent(agent_id="a2", name="Agent2", description="Second"))

        agents = orch.list_agents()
        assert len(agents) == 2
        assert {"id": "a1", "name": "Agent1", "description": "First"} in agents

    def test_create_task(self):
        orch = Orchestrator()
        task = orch.create_task("do something", assigned_agent_id="a1")
        assert task.description == "do something"
        assert task.assigned_agent_id == "a1"
        assert task.status == TaskStatus.PENDING

    def test_create_workflow(self):
        orch = Orchestrator()
        t1 = orch.create_task("task1", assigned_agent_id="a1")
        wf = orch.create_workflow("test-wf", tasks=[t1], mode=ExecutionMode.SEQUENTIAL)

        assert wf.name == "test-wf"
        assert len(wf.tasks) == 1
        assert wf.mode == ExecutionMode.SEQUENTIAL
        assert orch.current_workflow is wf


class TestSequentialExecution:
    """测试顺序执行模式"""

    def test_sequential_runs_all_tasks(self):
        orch = Orchestrator()
        orch.register_agent(MockAgent(agent_id="a1"))
        orch.register_agent(MockAgent(agent_id="a2"))

        t1 = orch.create_task("task1", assigned_agent_id="a1")
        t2 = orch.create_task("task2", assigned_agent_id="a2")
        wf = orch.create_workflow("seq", tasks=[t1, t2], mode=ExecutionMode.SEQUENTIAL)

        orch.run_workflow(wf)

        assert t1.status == TaskStatus.COMPLETED
        assert t2.status == TaskStatus.COMPLETED

    def test_sequential_with_dependencies(self):
        orch = Orchestrator()
        orch.register_agent(MockAgent(agent_id="a1"))

        t1 = orch.create_task("task1", assigned_agent_id="a1")
        t2 = orch.create_task("task2", assigned_agent_id="a1", dependencies=[t1.task_id])
        wf = orch.create_workflow("dep", tasks=[t1, t2], mode=ExecutionMode.SEQUENTIAL)

        orch.run_workflow(wf)

        assert t1.status == TaskStatus.COMPLETED
        assert t2.status == TaskStatus.COMPLETED

    def test_task_failure_sets_error(self):
        class FailingAgent(MockAgent):
            def run(self, task: str) -> AgentContext:
                raise RuntimeError("intentional failure")

        orch = Orchestrator()
        orch.register_agent(FailingAgent(agent_id="fail-agent"))

        t1 = orch.create_task("fail task", assigned_agent_id="fail-agent")
        wf = orch.create_workflow("fail-wf", tasks=[t1], mode=ExecutionMode.SEQUENTIAL)

        orch.run_workflow(wf)

        assert t1.status == TaskStatus.FAILED
        assert "intentional failure" in t1.error

    def test_missing_agent_fails_task(self):
        orch = Orchestrator()
        t1 = orch.create_task("orphan task", assigned_agent_id="nonexistent")
        wf = orch.create_workflow("orphan-wf", tasks=[t1], mode=ExecutionMode.SEQUENTIAL)

        orch.run_workflow(wf)

        assert t1.status == TaskStatus.FAILED
        assert "not found" in t1.error


class TestParallelExecution:
    """测试并行执行模式"""

    def test_parallel_runs_all_tasks(self):
        orch = Orchestrator()
        orch.register_agent(MockAgent(agent_id="a1"))
        orch.register_agent(MockAgent(agent_id="a2"))
        orch.register_agent(MockAgent(agent_id="a3"))

        tasks = [orch.create_task(f"task{i}", assigned_agent_id=f"a{i}") for i in range(1, 4)]
        wf = orch.create_workflow("par", tasks=tasks, mode=ExecutionMode.PARALLEL)

        orch.run_workflow(wf)

        for t in tasks:
            assert t.status == TaskStatus.COMPLETED

    def test_parallel_with_dependency(self):
        """并行模式下有依赖的任务应先完成依赖"""
        orch = Orchestrator()
        orch.register_agent(MockAgent(agent_id="a1"))
        orch.register_agent(MockAgent(agent_id="a2"))

        t1 = orch.create_task("first", assigned_agent_id="a1")
        t2 = orch.create_task("second", assigned_agent_id="a2", dependencies=[t1.task_id])
        wf = orch.create_workflow("par-dep", tasks=[t1, t2], mode=ExecutionMode.PARALLEL)

        orch.run_workflow(wf)

        assert t1.status == TaskStatus.COMPLETED
        assert t2.status == TaskStatus.COMPLETED


class TestPipelineExecution:
    """测试流水线执行模式"""

    def test_pipeline_passes_results(self):
        orch = Orchestrator()
        orch.register_agent(MockAgent(agent_id="a1", run_result="step1 output"))

        t1 = orch.create_task("step1", assigned_agent_id="a1")
        t2 = orch.create_task("step2", assigned_agent_id="a1")
        wf = orch.create_workflow("pipe", tasks=[t1, t2], mode=ExecutionMode.PIPELINE)

        orch.run_workflow(wf)

        assert t1.status == TaskStatus.COMPLETED
        assert t2.status == TaskStatus.COMPLETED
        # Pipeline should append previous task reference to description
        assert "task_" in t2.description or "step2" in t2.description

    def test_pipeline_shared_context(self):
        orch = Orchestrator()
        orch.register_agent(MockAgent(agent_id="a1", run_result="pipeline data"))

        t1 = orch.create_task("first", assigned_agent_id="a1")
        t2 = orch.create_task("second", assigned_agent_id="a1")
        wf = orch.create_workflow("pipe-ctx", tasks=[t1, t2], mode=ExecutionMode.PIPELINE)

        orch.run_workflow(wf)

        # Shared context should contain the result of the first task
        result = orch.shared_context.get(f"task_{t1.task_id}_result")
        assert result is not None
        assert result.metadata.get("result") == "pipeline data"


class TestWorkflowSummary:
    """测试工作流摘要"""

    def test_summary_with_mixed_results(self):
        class FailingAgent(MockAgent):
            def run(self, task: str) -> AgentContext:
                raise RuntimeError("fail")

        orch = Orchestrator()
        orch.register_agent(MockAgent(agent_id="ok"))
        orch.register_agent(FailingAgent(agent_id="bad"))

        t1 = orch.create_task("good", assigned_agent_id="ok")
        t2 = orch.create_task("bad", assigned_agent_id="bad")
        wf = orch.create_workflow("mixed", tasks=[t1, t2], mode=ExecutionMode.SEQUENTIAL)

        orch.run_workflow(wf)

        summary = orch.get_workflow_summary(wf)
        assert summary["total_tasks"] == 2
        assert summary["completed"] == 1
        assert summary["failed"] == 1
        assert summary["pending"] == 0
        assert summary["success_rate"] == 0.5

    def test_summary_empty_workflow(self):
        orch = Orchestrator()
        wf = orch.create_workflow("empty", tasks=[], mode=ExecutionMode.SEQUENTIAL)
        summary = orch.get_workflow_summary(wf)
        assert summary["total_tasks"] == 0
        assert summary["success_rate"] == 0


class TestCallbacks:
    """测试编排器回调"""

    def test_task_start_and_complete_callbacks(self):
        events = []
        orch = Orchestrator()
        orch.register_agent(MockAgent(agent_id="a1"))
        orch.on("on_task_start", lambda t: events.append(("start", t.task_id)))
        orch.on("on_task_complete", lambda t: events.append(("complete", t.task_id)))
        orch.on("on_workflow_complete", lambda w: events.append(("wf_complete", w.workflow_id)))

        t1 = orch.create_task("task1", assigned_agent_id="a1")
        wf = orch.create_workflow("cb", tasks=[t1], mode=ExecutionMode.SEQUENTIAL)
        orch.run_workflow(wf)

        assert ("start", t1.task_id) in events
        assert ("complete", t1.task_id) in events
        assert any(e[0] == "wf_complete" for e in events)

    def test_task_failed_callback(self):
        class FailingAgent(MockAgent):
            def run(self, task: str) -> AgentContext:
                raise RuntimeError("fail")

        failed_events = []
        orch = Orchestrator()
        orch.register_agent(FailingAgent(agent_id="bad"))
        orch.on("on_task_failed", lambda t: failed_events.append(t))

        t1 = orch.create_task("fail", assigned_agent_id="bad")
        wf = orch.create_workflow("fail-cb", tasks=[t1], mode=ExecutionMode.SEQUENTIAL)
        orch.run_workflow(wf)

        assert len(failed_events) == 1
        assert failed_events[0].status == TaskStatus.FAILED
