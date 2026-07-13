"""测试工具系统"""
import pytest
from codeagents.tools.registry import Tool, ToolRegistry, tool


def test_tool_decorator():
    """测试工具装饰器"""
    @tool(name="test_tool", description="Test tool", category="test")
    def test_func(param1: str, param2: int = 10) -> str:
        return f"{param1}: {param2}"

    assert test_func.name == "test_tool"
    assert test_func.description == "Test tool"
    assert test_func.category == "test"
    assert len(test_func.parameters) == 2


def test_tool_registry():
    """测试工具注册表"""
    registry = ToolRegistry()

    @tool(name="add", description="Add two numbers", category="math")
    def add(a: int, b: int) -> int:
        return a + b

    registry.register(add)

    # 测试获取工具
    tool_def = registry.get_tool("add")
    assert tool_def is not None
    assert tool_def.name == "add"

    # 测试执行
    result = registry.execute("add", {"a": 1, "b": 2})
    assert result == 3

    # 测试列出工具
    tools = registry.list_tools()
    assert len(tools) == 1


def test_tool_registry_json():
    """测试JSON格式的工具调用"""
    registry = ToolRegistry()

    @tool(name="multiply", description="Multiply two numbers")
    def multiply(a: int, b: int) -> int:
        return a * b

    registry.register(multiply)

    result = registry.execute_json("multiply", '{"a": 3, "b": 4}')
    assert '"result": 12' in result


def test_tool_not_found():
    """测试工具不存在的情况"""
    registry = ToolRegistry()

    with pytest.raises(ValueError):
        registry.execute("nonexistent", {})


def test_tool_execution_error():
    """测试工具执行错误"""
    registry = ToolRegistry()

    @tool(name="bad_tool")
    def bad_tool():
        raise ValueError("Something went wrong")

    registry.register(bad_tool)

    with pytest.raises(RuntimeError):
        registry.execute("bad_tool", {})


def test_tool_openai_format():
    """测试OpenAI格式转换"""
    registry = ToolRegistry()

    @tool(name="search", description="Search the web")
    def search(query: str, num_results: int = 5) -> str:
        return f"results for {query}"

    registry.register(search)

    tools = registry.to_openai_format()
    assert len(tools) == 1
    assert tools[0]["type"] == "function"
    assert tools[0]["function"]["name"] == "search"


def test_list_tools_by_category():
    """测试按类别列出工具"""
    registry = ToolRegistry()

    @tool(name="tool1", category="cat1")
    def tool1():
        return "1"

    @tool(name="tool2", category="cat2")
    def tool2():
        return "2"

    registry.register(tool1)
    registry.register(tool2)

    cat1 = registry.list_tools("cat1")
    cat2 = registry.list_tools("cat2")

    assert len(cat1) == 1
    assert cat1[0].name == "tool1"
    assert len(cat2) == 1
    assert cat2[0].name == "tool2"
