"""
示例1: 单个代码智能体的基本使用
"""
import os
from codeagents import CodeAgent, get_llm, create_tool_registry

# 确保设置了API密钥
# os.environ["OPENAI_API_KEY"] = "your-api-key"
# 或者使用兼容的本地模型
# os.environ["OPENAI_BASE_URL"] = "http://localhost:8000/v1"


def main():
    # 1. 初始化LLM
    llm = get_llm(
        provider="openai",
        model="gpt-4o",  # 可以换成其他模型
    )

    # 2. 创建工具注册表（包含文件、代码、Git工具）
    tool_registry = create_tool_registry()

    # 3. 创建代码智能体
    agent = CodeAgent(
        agent_id="coder-1",
        name="Python Coder",
        description="专业的Python代码助手",
        llm=llm,
        tool_registry=tool_registry,
        max_steps=5,
    )

    # 4. 注册事件回调
    def on_message(message):
        print(f"[{message.role}] {message.content[:100]}...")

    def on_tool_call(tool_call):
        print(f"🔧 调用工具: {tool_call.name}({tool_call.arguments})")

    def on_tool_result(result):
        status = "✅" if not result.is_error else "❌"
        print(f"{status} 工具结果: {result.content[:100]}...")

    agent.on("on_message", on_message)
    agent.on("on_tool_call", on_tool_call)
    agent.on("on_tool_result", on_tool_result)

    # 5. 运行智能体
    task = """
    请帮我创建一个简单的Python函数，用于计算斐波那契数列。
    要求：
    1. 使用递归实现
    2. 有类型注解
    3. 有适当的文档字符串
    4. 有边界条件处理

    将代码写入到 fibonacci.py 文件中。
    """

    print("=== 开始执行任务 ===")
    print(f"任务: {task.strip()}\n")

    context = agent.run(task)

    print("\n=== 执行完成 ===")
    print(f"状态: {context.status}")
    print(f"步数: {context.current_step}")

    print("\n=== 完整对话历史 ===")
    for msg in context.messages:
        print(f"\n[{msg.role}] {msg.content[:200]}...")


if __name__ == "__main__":
    main()
