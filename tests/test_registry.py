"""工具注册表测试

验证工具装饰器、注册、执行、OpenAI 格式转换、冲突处理。
"""
import pytest
import json
from codeagents.tools.registry import (
    Tool, ToolDefinition, ToolParameter, ToolRegistry, tool,
)


class TestToolDecorator:
    """测试 @tool 装饰器"""

    def test_basic_decoration(self):
        @tool(name="greet", description="Say hello")
        def greet(name: str) -> str:
            """Greet someone"""
            return f"Hello, {name}!"

        assert isinstance(greet, ToolDefinition)
        assert greet.name == "greet"
        assert greet.description == "Say hello"
        assert greet.function("World") == "Hello, World!"

    def test_auto_name_from_function(self):
        @tool()
        def calculate(x: int, y: int) -> int:
            return x + y

        assert calculate.name == "calculate"

    def test_auto_description_from_docstring(self):
        @tool()
        def search(query: str):
            """Search for something"""
            return query

        assert search.description == "Search for something"

    def test_parameter_extraction(self):
        @tool(name="test_params")
        def func(required_param: str, optional_param: int = 42):
            return required_param

        params = {p.name: p for p in func.parameters}
        assert "required_param" in params
        assert params["required_param"].required is True
        assert params["required_param"].type == "string"

        assert "optional_param" in params
        assert params["optional_param"].required is False
        assert params["optional_param"].type == "integer"
        assert params["optional_param"].default == 42

    def test_category(self):
        @tool(name="t", category="custom")
        def f(x: str):
            return x

        assert f.category == "custom"

    def test_skips_self_parameter(self):
        class MyClass:
            @tool(name="method")
            def my_method(self, x: str):
                return x

        obj = MyClass()
        params = [p.name for p in obj.my_method.parameters]
        assert "self" not in params
        assert "x" in params


class TestToolRegistry:
    """测试工具注册表"""

    def test_register_and_get(self):
        registry = ToolRegistry()

        @tool(name="my_tool")
        def my_tool(x: str):
            return x

        registry.register(my_tool)
        assert registry.get_tool("my_tool") is my_tool

    def test_get_nonexistent(self):
        registry = ToolRegistry()
        assert registry.get_tool("nope") is None

    def test_list_all_tools(self):
        registry = ToolRegistry()

        @tool(name="t1", category="a")
        def t1(x: str): return x

        @tool(name="t2", category="b")
        def t2(x: str): return x

        registry.register(t1)
        registry.register(t2)

        all_tools = registry.list_tools()
        assert len(all_tools) == 2

    def test_list_by_category(self):
        registry = ToolRegistry()

        @tool(name="t1", category="file")
        def t1(x: str): return x

        @tool(name="t2", category="git")
        def t2(x: str): return x

        @tool(name="t3", category="file")
        def t3(x: str): return x

        registry.register(t1)
        registry.register(t2)
        registry.register(t3)

        file_tools = registry.list_tools(category="file")
        assert len(file_tools) == 2
        git_tools = registry.list_tools(category="git")
        assert len(git_tools) == 1

    def test_register_function_directly(self):
        registry = ToolRegistry()

        def my_func(x: str):
            return x.upper()

        registry.register_function(my_func, name="upper_case", description="Upper case")
        tool_def = registry.get_tool("upper_case")
        assert tool_def is not None
        assert tool_def.function("hello") == "HELLO"

    def test_overwrite_on_duplicate_name(self):
        registry = ToolRegistry()

        @tool(name="dup")
        def v1(x: str):
            return "v1"

        @tool(name="dup")
        def v2(x: str):
            return "v2"

        registry.register(v1)
        registry.register(v2)

        result = registry.execute("dup", {"x": "test"})
        assert result == "v2"


class TestToolExecution:
    """测试工具执行"""

    def test_execute_with_correct_args(self):
        registry = ToolRegistry()

        @tool(name="add")
        def add(a: int, b: int) -> int:
            return a + b

        registry.register(add)
        result = registry.execute("add", {"a": 3, "b": 5})
        assert result == 8

    def test_execute_nonexistent_raises(self):
        registry = ToolRegistry()
        with pytest.raises(ValueError, match="not found"):
            registry.execute("nonexistent", {})

    def test_execute_with_wrong_args_raises(self):
        registry = ToolRegistry()

        @tool(name="needs_arg")
        def func(x: str):
            return x

        registry.register(func)
        with pytest.raises(RuntimeError, match="Tool execution failed"):
            registry.execute("needs_arg", {})

    def test_execute_json_valid(self):
        registry = ToolRegistry()

        @tool(name="echo")
        def echo(msg: str):
            return msg

        registry.register(echo)
        result = registry.execute_json("echo", json.dumps({"msg": "hello"}))
        parsed = json.loads(result)
        assert parsed["result"] == "hello"

    def test_execute_json_invalid_json(self):
        registry = ToolRegistry()
        result = registry.execute_json("any", "not valid json{{{")
        parsed = json.loads(result)
        assert "error" in parsed

    def test_execute_json_tool_error(self):
        registry = ToolRegistry()

        @tool(name="fail_tool")
        def fail_tool(x: str):
            raise ValueError("boom")

        registry.register(fail_tool)
        result = registry.execute_json("fail_tool", json.dumps({"x": "test"}))
        parsed = json.loads(result)
        assert "error" in parsed


class TestOpenAIFormat:
    """测试 OpenAI function calling 格式转换"""

    def test_to_openai_format(self):
        @tool(name="read_file", description="Read a file")
        def read_file(path: str, encoding: str = "utf-8"):
            return "content"

        fmt = read_file.to_openai_format()
        assert fmt["type"] == "function"
        assert fmt["function"]["name"] == "read_file"
        assert fmt["function"]["description"] == "Read a file"
        assert "path" in fmt["function"]["parameters"]["properties"]
        assert "encoding" in fmt["function"]["parameters"]["properties"]
        assert "path" in fmt["function"]["parameters"]["required"]
        assert "encoding" not in fmt["function"]["parameters"]["required"]

    def test_registry_to_openai_format(self):
        registry = ToolRegistry()

        @tool(name="t1")
        def t1(x: str): return x

        @tool(name="t2")
        def t2(y: int): return y

        registry.register(t1)
        registry.register(t2)

        formats = registry.to_openai_format()
        assert len(formats) == 2
        names = [f["function"]["name"] for f in formats]
        assert "t1" in names
        assert "t2" in names

    def test_empty_registry_openai_format(self):
        registry = ToolRegistry()
        assert registry.to_openai_format() == []

    def test_type_mapping(self):
        @tool(name="type_test")
        def type_test(s: str, i: int, f: float, b: bool, l: list, d: dict):
            return None

        props = type_test.to_openai_format()["function"]["parameters"]["properties"]
        assert props["s"]["type"] == "string"
        assert props["i"]["type"] == "integer"
        assert props["f"]["type"] == "number"
        assert props["b"]["type"] == "boolean"
        assert props["l"]["type"] == "array"
        assert props["d"]["type"] == "object"
