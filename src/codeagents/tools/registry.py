"""工具注册与调用框架"""
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
import inspect
import json


@dataclass
class ToolParameter:
    """工具参数定义"""
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None


@dataclass
class ToolDefinition:
    """工具定义"""
    name: str
    description: str
    parameters: List[ToolParameter] = field(default_factory=list)
    function: Callable = None
    category: str = "general"

    def to_openai_format(self) -> Dict[str, Any]:
        """转换为OpenAI函数调用格式"""
        properties = {}
        required = []

        for param in self.parameters:
            properties[param.name] = {
                "type": param.type,
                "description": param.description,
            }
            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }


class Tool:
    """工具基类装饰器"""

    def __init__(
        self,
        name: Optional[str] = None,
        description: str = "",
        category: str = "general",
    ):
        self.name = name
        self.description = description
        self.category = category

    def __call__(self, func: Callable) -> ToolDefinition:
        tool_name = self.name or func.__name__

        # 解析函数签名获取参数
        sig = inspect.signature(func)
        parameters = []

        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue

            param_type = "string"
            if param.annotation != inspect.Parameter.empty:
                type_mapping = {
                    str: "string",
                    int: "integer",
                    float: "number",
                    bool: "boolean",
                    list: "array",
                    dict: "object",
                }
                param_type = type_mapping.get(param.annotation, "string")

            required = param.default == inspect.Parameter.empty

            parameters.append(
                ToolParameter(
                    name=param_name,
                    type=param_type,
                    description=f"Parameter: {param_name}",
                    required=required,
                    default=None if required else param.default,
                )
            )

        return ToolDefinition(
            name=tool_name,
            description=self.description or func.__doc__ or "",
            parameters=parameters,
            function=func,
            category=self.category,
        )


class ToolRegistry:
    """工具注册表"""

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    def register(self, tool_def: ToolDefinition):
        """注册工具"""
        self._tools[tool_def.name] = tool_def

    def register_function(self, func: Callable, name: str = None, description: str = ""):
        """直接注册函数"""
        tool = Tool(name=name, description=description)
        self.register(tool(func))

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """获取工具定义"""
        return self._tools.get(name)

    def list_tools(self, category: Optional[str] = None) -> List[ToolDefinition]:
        """列出所有工具"""
        tools = list(self._tools.values())
        if category:
            tools = [t for t in tools if t.category == category]
        return tools

    def to_openai_format(self) -> List[Dict[str, Any]]:
        """转换为OpenAI工具格式列表"""
        return [t.to_openai_format() for t in self._tools.values()]

    def execute(self, name: str, arguments: Dict[str, Any]) -> Any:
        """执行工具"""
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found")

        try:
            return tool.function(**arguments)
        except Exception as e:
            raise RuntimeError(f"Tool execution failed: {e}") from e

    def execute_json(self, name: str, arguments_json: str) -> str:
        """执行工具并返回JSON结果"""
        try:
            arguments = json.loads(arguments_json)
        except json.JSONDecodeError as e:
            return json.dumps({"error": f"Invalid JSON: {e}"}, ensure_ascii=False)

        try:
            result = self.execute(name, arguments)
            return json.dumps({"result": result}, ensure_ascii=False)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)


# 便捷装饰器
def tool(name: str = None, description: str = "", category: str = "general"):
    """装饰器：将函数注册为工具"""
    return Tool(name=name, description=description, category=category)
