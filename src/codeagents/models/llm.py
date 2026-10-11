"""LLM模型包装器"""
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod
import json
import os


class BaseLLM(ABC):
    """LLM抽象基类"""

    #: API Key 环境变量名（子类可覆盖，用于通义千问/豆包等 provider）
    API_KEY_ENV: str = "OPENAI_API_KEY"
    #: Base URL 环境变量名
    BASE_URL_ENV: str = "OPENAI_BASE_URL"

    def __init__(self, model: str, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url

    @abstractmethod
    def chat(self, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """聊天补全"""
        pass

    @abstractmethod
    def chat_with_tools(
        self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], **kwargs
    ) -> Dict[str, Any]:
        """带工具调用的聊天"""
        pass


class OpenAILLM(BaseLLM):
    """OpenAI兼容API"""

    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        super().__init__(model, api_key, base_url)
        self._client = None
        self._init_client()

    def _init_client(self):
        """初始化客户端"""
        try:
            from openai import OpenAI

            api_key = self.api_key or os.getenv(self.API_KEY_ENV)
            base_url = self.base_url or os.getenv(self.BASE_URL_ENV)

            self._client = OpenAI(api_key=api_key, base_url=base_url)
        except ImportError:
            raise ImportError(
                "openai package not installed. Install with: pip install openai"
            )

    def chat(self, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            **kwargs,
        )
        return {
            "content": response.choices[0].message.content,
            "tool_calls": response.choices[0].message.tool_calls,
            "usage": response.usage.model_dump() if response.usage else None,
        }

    def chat_with_tools(
        self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], **kwargs
    ) -> Dict[str, Any]:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            **kwargs,
        )
        message = response.choices[0].message

        tool_calls = []
        if message.tool_calls:
            for tc in message.tool_calls:
                try:
                    arguments = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    arguments = {}

                tool_calls.append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": arguments,
                })

        return {
            "content": message.content,
            "tool_calls": tool_calls,
            "usage": response.usage.model_dump() if response.usage else None,
        }


class OpenAICompatibleLLM(OpenAILLM):
    """OpenAI 协议兼容的通用 LLM

    通义千问（DashScope）、豆包（火山方舟）等国产大模型均提供 OpenAI 兼容端点，
    因此这里只覆盖默认的 base_url / 模型名 / API Key 环境变量即可复用 OpenAI 的
    消息格式与 function calling 逻辑。
    """

    #: 兼容端点地址
    DEFAULT_BASE_URL: Optional[str] = None
    #: 默认模型
    DEFAULT_MODEL: str = ""
    #: API Key 环境变量
    API_KEY_ENV: str = "OPENAI_API_KEY"
    #: Base URL 环境变量（provider 专属，优先级低于显式传参）
    BASE_URL_ENV: str = "OPENAI_BASE_URL"

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        super().__init__(
            model=model or self.DEFAULT_MODEL,
            api_key=api_key,
            base_url=base_url or self.DEFAULT_BASE_URL,
        )


class QwenLLM(OpenAICompatibleLLM):
    """通义千问（阿里云 DashScope OpenAI 兼容模式）"""

    DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    DEFAULT_MODEL = "qwen-plus"
    API_KEY_ENV = "DASHSCOPE_API_KEY"
    BASE_URL_ENV = "DASHSCOPE_BASE_URL"


class DoubaoLLM(OpenAICompatibleLLM):
    """豆包（火山方舟 Ark OpenAI 兼容模式）

    注意：Ark 平台的 model 需填写接入点 ID（endpoint id），
    形如 ``doubao-pro-32k`` 或控制台创建的 ``ep-xxxxxx``。
    """

    DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
    DEFAULT_MODEL = "doubao-pro-32k"
    API_KEY_ENV = "ARK_API_KEY"
    BASE_URL_ENV = "ARK_BASE_URL"


class AnthropicLLM(BaseLLM):
    """Anthropic Claude API"""

    def __init__(
        self,
        model: str = "claude-3-5-sonnet-20240620",
        api_key: Optional[str] = None,
    ):
        super().__init__(model, api_key)
        self._client = None
        self._init_client()

    def _init_client(self):
        try:
            from anthropic import Anthropic

            api_key = self.api_key or os.getenv("ANTHROPIC_API_KEY")
            self._client = Anthropic(api_key=api_key)
        except ImportError:
            raise ImportError(
                "anthropic package not installed. Install with: pip install anthropic"
            )

    def chat(self, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        # 提取system消息
        system_prompt = ""
        filtered_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                filtered_messages.append(msg)

        response = self._client.messages.create(
            model=self.model,
            system=system_prompt if system_prompt else None,
            messages=filtered_messages,
            max_tokens=kwargs.get("max_tokens", 4096),
        )

        return {
            "content": response.content[0].text if response.content else "",
            "tool_calls": None,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
        }

    def chat_with_tools(
        self, messages: List[Dict[str, Any]], tools: List[Dict[str, Any]], **kwargs
    ) -> Dict[str, Any]:
        # 转换工具格式
        anthropic_tools = []
        for t in tools:
            func = t["function"]
            anthropic_tools.append({
                "name": func["name"],
                "description": func["description"],
                "input_schema": func["parameters"],
            })

        # 提取system消息
        system_prompt = ""
        filtered_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                filtered_messages.append(msg)

        response = self._client.messages.create(
            model=self.model,
            system=system_prompt if system_prompt else None,
            messages=filtered_messages,
            tools=anthropic_tools,
            max_tokens=kwargs.get("max_tokens", 4096),
        )

        tool_calls = []
        content_text = ""

        for block in response.content:
            if block.type == "text":
                content_text += block.text
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "arguments": block.input,
                })

        return {
            "content": content_text,
            "tool_calls": tool_calls,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
        }


def get_llm(provider: str = "openai", **kwargs) -> BaseLLM:
    """工厂函数获取LLM实例

    支持的 provider：
    - ``openai``：OpenAI 及任何 OpenAI 兼容服务
    - ``anthropic``：Anthropic Claude
    - ``qwen`` / ``dashscope``：通义千问
    - ``doubao`` / ``ark``：豆包（火山方舟）
    """
    providers = {
        "openai": OpenAILLM,
        "anthropic": AnthropicLLM,
        "qwen": QwenLLM,
        "dashscope": QwenLLM,
        "doubao": DoubaoLLM,
        "ark": DoubaoLLM,
    }

    if provider not in providers:
        raise ValueError(f"Unknown provider: {provider}. Available: {list(providers.keys())}")

    return providers[provider](**kwargs)
