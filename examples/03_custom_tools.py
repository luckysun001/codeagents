"""
示例3: 自定义工具
"""
from codeagents import tool, ToolRegistry, CodeAgent, get_llm
import requests
import json


# 使用装饰器定义自定义工具
@tool(name="search_web", description="在网络上搜索信息", category="web")
def search_web(query: str, num_results: int = 5) -> str:
    """搜索网络（使用DuckDuckGo API）"""
    try:
        # 这是一个简化示例，实际可能需要真正的搜索API
        url = f"https://api.duckduckgo.com/?q={query}&format=json"
        response = requests.get(url, timeout=10)
        data = response.json()

        results = []
        if data.get("AbstractText"):
            results.append(f"摘要: {data['AbstractText']}")

        for result in data.get("RelatedTopics", [])[:num_results]:
            if "Text" in result:
                results.append(f"- {result['Text']}")

        if not results:
            return f"No results found for: {query}"

        return f"Search results for '{query}':\n" + "\n".join(results)
    except Exception as e:
        return f"Error searching: {e}"


@tool(name="calculate", description="执行数学计算", category="math")
def calculate(expression: str) -> str:
    """执行数学计算"""
    try:
        # 安全的数学计算
        import ast
        import operator

        # 安全的操作符白名单
        operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
        }

        def eval_expr(node):
            if isinstance(node, ast.Constant):
                return node.n
            elif isinstance(node, ast.BinOp):
                return operators[type(node.op)](
                    eval_expr(node.left),
                    eval_expr(node.right),
                )
            elif isinstance(node, ast.UnaryOp):
                return operators[type(node.op)](eval_expr(node.operand))
            else:
                raise TypeError(node)

        result = eval_expr(ast.parse(expression, mode="eval").body)
        return f"Result: {expression} = {result}"
    except Exception as e:
        return f"Error calculating: {e}"


@tool(name="get_weather", description="获取天气信息", category="weather")
def get_weather(city: str) -> str:
    """获取城市天气（模拟）"""
    # 这是一个模拟API，实际应使用真实的天气API
    weather_data = {
        "北京": "晴朗，25°C，湿度45%",
        "上海": "多云，28°C，湿度60%",
        "深圳": "雷阵雨，30°C，湿度75%",
        "广州": "晴间多云，29°C，湿度65%",
    }

    if city in weather_data:
        return f"{city}的天气: {weather_data[city]}"
    else:
        return f"没有找到{city}的天气数据（这是模拟数据，仅支持北京、上海、深圳、广州）"


def main():
    # 1. 创建自定义工具注册表
    registry = ToolRegistry()
    registry.register(search_web)
    registry.register(calculate)
    registry.register(get_weather)

    # 列出已注册的工具
    print("已注册的工具:")
    for tool_def in registry.list_tools():
        print(f"  - {tool_def.name}: {tool_def.description}")

    # 2. 测试工具执行
    print("\n=== 工具测试 ===")
    result = registry.execute("calculate", {"expression": "2 * 3 + 5"})
    print(f"calculate 结果: {result}")

    result = registry.execute("get_weather", {"city": "北京"})
    print(f"get_weather 结果: {result}")

    # 3. 创建使用自定义工具的智能体
    print("\n=== 使用自定义工具的智能体 ===")
    llm = get_llm(provider="openai", model="gpt-4o")

    agent = CodeAgent(
        agent_id="custom-agent",
        name="Custom Agent",
        description="使用自定义工具的智能体",
        llm=llm,
        tool_registry=registry,
    )

    # 注册回调
    def on_tool_call(tool_call):
        print(f"🔧 调用工具: {tool_call.name}({tool_call.arguments})")

    def on_tool_result(result):
        status = "✅" if not result.is_error else "❌"
        print(f"{status} 结果: {result.content[:100]}")

    agent.on("on_tool_call", on_tool_call)
    agent.on("on_tool_result", on_tool_result)

    # 运行任务
    task = """
    请帮我计算：(10 + 5) * 3 的结果，然后告诉我北京今天的天气如何。
    """

    print(f"\n任务: {task.strip()}")
    context = agent.run(task)

    print(f"\n最终回答: {context.messages[-1].content}")


if __name__ == "__main__":
    main()
