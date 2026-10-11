"""LLM provider 测试

覆盖 OpenAI 兼容层（通义千问 / 豆包）的默认参数与工厂函数映射。
不发起任何真实网络请求：openai SDK 构造客户端是纯本地行为。
"""
import pytest

from codeagents.models.llm import (
    AnthropicLLM,
    DoubaoLLM,
    OpenAICompatibleLLM,
    OpenAILLM,
    QwenLLM,
    get_llm,
)


class TestOpenAICompatibleDefaults:
    """各 provider 的默认端点 / 模型 / 环境变量"""

    def test_qwen_defaults(self):
        llm = QwenLLM(api_key="test-key")
        assert llm.model == "qwen-plus"
        assert llm.base_url == "https://dashscope.aliyuncs.com/compatible-mode/v1"
        assert QwenLLM.API_KEY_ENV == "DASHSCOPE_API_KEY"

    def test_doubao_defaults(self):
        llm = DoubaoLLM(api_key="test-key")
        assert llm.model == "doubao-pro-32k"
        assert llm.base_url.startswith("https://ark.")
        assert DoubaoLLM.API_KEY_ENV == "ARK_API_KEY"

    def test_explicit_args_override_defaults(self):
        llm = QwenLLM(model="qwen-max", api_key="k", base_url="http://localhost:8000/v1")
        assert llm.model == "qwen-max"
        assert llm.base_url == "http://localhost:8000/v1"

    def test_compatible_llm_reads_provider_specific_env(self, monkeypatch):
        """未显式传 api_key 时，应读取该 provider 自己的环境变量"""
        monkeypatch.setenv("DASHSCOPE_API_KEY", "env-key")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        llm = QwenLLM()
        assert llm._client is not None
        # 客户端构建成功即说明取到了 DASHSCOPE_API_KEY
        assert llm.api_key is None  # 实例字段保持未设置，仅客户端使用 env 值

    def test_openai_llm_keeps_default_env(self):
        assert OpenAILLM.API_KEY_ENV == "OPENAI_API_KEY"
        assert OpenAILLM.BASE_URL_ENV == "OPENAI_BASE_URL"
        assert issubclass(QwenLLM, OpenAICompatibleLLM)
        assert issubclass(DoubaoLLM, OpenAICompatibleLLM)
        assert issubclass(OpenAICompatibleLLM, OpenAILLM)


class TestGetLLMFactory:
    """工厂函数路由"""

    @pytest.mark.parametrize(
        "provider,expected_cls",
        [
            ("openai", OpenAILLM),
            ("qwen", QwenLLM),
            ("dashscope", QwenLLM),
            ("doubao", DoubaoLLM),
            ("ark", DoubaoLLM),
        ],
    )
    def test_known_providers(self, provider, expected_cls):
        llm = get_llm(provider, api_key="test-key")
        assert isinstance(llm, expected_cls)

    def test_anthropic_provider(self):
        pytest.importorskip("anthropic")
        assert isinstance(get_llm("anthropic", api_key="test-key"), AnthropicLLM)

    def test_unknown_provider_raises(self):
        with pytest.raises(ValueError, match="Unknown provider"):
            get_llm("not-a-provider")

    def test_available_providers_listed_in_error(self):
        with pytest.raises(ValueError) as exc:
            get_llm("nope")
        message = str(exc.value)
        for name in ("openai", "anthropic", "qwen", "doubao"):
            assert name in message
