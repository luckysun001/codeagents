"""
示例2: 多智能体协作 - 代码审查工作流
"""
import os
from codeagents import (
    CodeAgent,
    PlanningAgent,
    ReviewAgent,
    get_llm,
    create_tool_registry,
    Orchestrator,
    ExecutionMode,
)


def main():
    # 1. 初始化LLM
    llm = get_llm(
        provider="openai",
        model="gpt-4o",
    )

    # 2. 创建多个智能体
    planner = PlanningAgent(
        agent_id="planner",
        name="Planner",
        llm=llm,
    )

    coder = CodeAgent(
        agent_id="coder",
        name="Coder",
        llm=llm,
        tool_registry=create_tool_registry(["file", "code"]),
    )

    reviewer = ReviewAgent(
        agent_id="reviewer",
        name="Reviewer",
        llm=llm,
    )

    # 3. 创建编排器
    orchestrator = Orchestrator()
    orchestrator.register_agent(planner)
    orchestrator.register_agent(coder)
    orchestrator.register_agent(reviewer)

    # 4. 创建工作流任务
    task_description = """
    创建一个Python库，实现一个简单的数据结构：双向链表。
    要求：
    1. 完整的实现，包括插入、删除、查找操作
    2. 有单元测试
    3. 代码符合PEP8规范
    4. 有类型注解和文档字符串
    """

    # 5. 创建工作流：PLANNER -> CODER -> REVIEWER
    workflow = orchestrator.create_workflow(
        name="代码开发流水线",
        mode=ExecutionMode.PIPELINE,
    )

    # 任务1: 制定开发计划
    task1 = orchestrator.create_task(
        description=f"分析以下需求，制定详细的开发计划：\n{task_description}",
        assigned_agent_id="planner",
    )
    workflow.tasks.append(task1)

    # 任务2: 实现代码
    task2 = orchestrator.create_task(
        description="根据开发计划，实现双向链表代码和单元测试",
        assigned_agent_id="coder",
        dependencies=[task1.task_id],
    )
    workflow.tasks.append(task2)

    # 任务3: 代码审查
    task3 = orchestrator.create_task(
        description="审查实现的代码，给出改进建议",
        assigned_agent_id="reviewer",
        dependencies=[task2.task_id],
    )
    workflow.tasks.append(task3)

    # 6. 注册事件回调
    def on_task_start(task):
        print(f"🚀 开始任务: {task.description[:50]}...")

    def on_task_complete(task):
        print(f"✅ 任务完成: {task.description[:50]}...")

    def on_task_failed(task):
        print(f"❌ 任务失败: {task.error}")

    def on_workflow_complete(workflow):
        summary = orchestrator.get_workflow_summary(workflow)
        print(f"\n🎉 工作流完成: {summary['name']}")
        print(f"   成功率: {summary['success_rate']:.1%}")
        print(f"   完成: {summary['completed']}/{summary['total_tasks']}")

    orchestrator.on("on_task_start", on_task_start)
    orchestrator.on("on_task_complete", on_task_complete)
    orchestrator.on("on_task_failed", on_task_failed)
    orchestrator.on("on_workflow_complete", on_workflow_complete)

    # 7. 运行工作流
    print("=== 开始多智能体协作工作流 ===\n")
    orchestrator.run_workflow(workflow)

    # 8. 输出结果
    print("\n=== 最终结果 ===")
    for task in workflow.tasks:
        print(f"\n📋 任务: {task.description[:50]}...")
        print(f"   状态: {task.status}")
        if task.result:
            last_msg = task.result.messages[-1]
            print(f"   输出: {last_msg.content[:300]}...")


if __name__ == "__main__":
    main()
