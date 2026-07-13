"""多智能体调度器"""
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from .message_bus import MessageBus, SharedContext
from ..core.agent import BaseAgent


class ExecutionMode(str, Enum):
    """执行模式"""
    SEQUENTIAL = "sequential"  # 顺序执行
    PARALLEL = "parallel"      # 并行执行
    PIPELINE = "pipeline"      # 流水线模式
    ROUND_ROBIN = "round_robin"  # 轮询
    HIERARCHICAL = "hierarchical"  # 层级模式


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    """任务"""
    task_id: str
    description: str
    assigned_agent_id: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


@dataclass
class Workflow:
    """工作流"""
    workflow_id: str
    name: str
    tasks: List[Task] = field(default_factory=list)
    mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    metadata: Dict[str, Any] = field(default_factory=dict)


class Orchestrator:
    """多智能体编排器"""

    def __init__(
        self,
        message_bus: Optional[MessageBus] = None,
        shared_context: Optional[SharedContext] = None,
    ):
        self.message_bus = message_bus or MessageBus()
        self.shared_context = shared_context or SharedContext()
        self.agents: Dict[str, BaseAgent] = {}
        self.current_workflow: Optional[Workflow] = None
        self._callbacks: Dict[str, List[Callable]] = {
            "on_task_start": [],
            "on_task_complete": [],
            "on_task_failed": [],
            "on_workflow_complete": [],
        }

    def on(self, event: str, callback: Callable):
        """注册事件回调"""
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def _emit(self, event: str, *args, **kwargs):
        """触发事件"""
        for callback in self._callbacks.get(event, []):
            callback(*args, **kwargs)

    def register_agent(self, agent: BaseAgent):
        """注册智能体"""
        self.agents[agent.agent_id] = agent

        # 让智能体订阅消息总线
        def on_message(message):
            """消息处理"""
            pass  # 子类可以覆盖处理逻辑

        self.message_bus.subscribe_to_agent(agent.agent_id, on_message)

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """获取智能体"""
        return self.agents.get(agent_id)

    def list_agents(self) -> List[Dict[str, str]]:
        """列出所有智能体"""
        return [
            {"id": a.agent_id, "name": a.name, "description": a.description}
            for a in self.agents.values()
        ]

    def create_task(
        self,
        description: str,
        assigned_agent_id: Optional[str] = None,
        dependencies: List[str] = None,
        metadata: Dict[str, Any] = None,
    ) -> Task:
        """创建任务"""
        import uuid

        task = Task(
            task_id=str(uuid.uuid4()),
            description=description,
            assigned_agent_id=assigned_agent_id,
            dependencies=dependencies or [],
            metadata=metadata or {},
        )
        return task

    def create_workflow(
        self,
        name: str,
        tasks: List[Task] = None,
        mode: ExecutionMode = ExecutionMode.SEQUENTIAL,
    ) -> Workflow:
        """创建工作流"""
        import uuid

        workflow = Workflow(
            workflow_id=str(uuid.uuid4()),
            name=name,
            tasks=tasks or [],
            mode=mode,
        )
        self.current_workflow = workflow
        return workflow

    def _run_task(self, task: Task) -> Task:
        """运行单个任务"""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        self._emit("on_task_start", task)

        try:
            agent = self.get_agent(task.assigned_agent_id)
            if not agent:
                raise ValueError(f"Agent '{task.assigned_agent_id}' not found")

            context = agent.run(task.description)
            task.result = context
            task.status = TaskStatus.COMPLETED
            self._emit("on_task_complete", task)

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            self._emit("on_task_failed", task)

        task.completed_at = datetime.now()
        return task

    def _get_ready_tasks(self, workflow: Workflow) -> List[Task]:
        """获取准备好执行的任务"""
        ready = []
        for task in workflow.tasks:
            if task.status != TaskStatus.PENDING:
                continue

            # 检查依赖是否都完成
            deps_completed = all(
                t.status == TaskStatus.COMPLETED
                for t in workflow.tasks
                if t.task_id in task.dependencies
            )
            if deps_completed:
                ready.append(task)

        return ready

    def run_workflow(self, workflow: Workflow) -> Workflow:
        """运行工作流"""
        if workflow.mode == ExecutionMode.SEQUENTIAL:
            return self._run_sequential(workflow)
        elif workflow.mode == ExecutionMode.PARALLEL:
            return self._run_parallel(workflow)
        elif workflow.mode == ExecutionMode.PIPELINE:
            return self._run_pipeline(workflow)
        else:
            raise ValueError(f"Unsupported mode: {workflow.mode}")

    def _run_sequential(self, workflow: Workflow) -> Workflow:
        """顺序执行"""
        while True:
            ready = self._get_ready_tasks(workflow)
            if not ready:
                break

            for task in ready:
                self._run_task(task)

        self._emit("on_workflow_complete", workflow)
        return workflow

    def _run_parallel(self, workflow: Workflow) -> Workflow:
        """并行执行"""
        import concurrent.futures

        completed = set()
        while len(completed) < len(workflow.tasks):
            ready = [t for t in self._get_ready_tasks(workflow) if t.task_id not in completed]
            if not ready:
                break

            with concurrent.futures.ThreadPoolExecutor(max_workers=len(ready)) as executor:
                futures = {executor.submit(self._run_task, task): task for task in ready}
                for future in concurrent.futures.as_completed(futures):
                    task = futures[future]
                    completed.add(task.task_id)

        self._emit("on_workflow_complete", workflow)
        return workflow

    def _run_pipeline(self, workflow: Workflow) -> Workflow:
        """流水线执行：上一个任务的输出作为下一个的输入"""
        for i, task in enumerate(workflow.tasks):
            if i > 0:
                prev_task = workflow.tasks[i - 1]
                # 将前一个任务的结果加入上下文
                self.shared_context.set(f"task_{prev_task.task_id}_result", prev_task.result)
                task.description += f"\n\n前序任务结果参考: {prev_task.task_id}"

            self._run_task(task)

        self._emit("on_workflow_complete", workflow)
        return workflow

    def get_workflow_summary(self, workflow: Workflow) -> Dict[str, Any]:
        """获取工作流摘要"""
        completed = sum(1 for t in workflow.tasks if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in workflow.tasks if t.status == TaskStatus.FAILED)
        pending = sum(1 for t in workflow.tasks if t.status == TaskStatus.PENDING)

        return {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "mode": workflow.mode.value,
            "total_tasks": len(workflow.tasks),
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "success_rate": completed / len(workflow.tasks) if workflow.tasks else 0,
        }
