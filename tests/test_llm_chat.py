"""LLM 客户端 chat / chat_with_tools 测试

不发起任何真实网络请求：用 MagicMock 替换底层 SDK 客户端，覆盖
- OpenAI 兼容层：普通回复、带 tool_calls、坏 JSON、无 usage
- Anthropic：通过注入假的 anthropic 模块覆盖 chat / chat_with_tools
"""
import sys
from unittest.mock import MagicMock

import pytest

from codeagents.models.llm import AnthropicLLM, OpenAILLM


def _openai_response(content="hi", tool_calls=None, usage=True):
    resp = MagicMock()
    msg = MagicMock()
    msg.content = content
    msg.tool_calls = tool_calls
    resp.choices = [MagicMock(message=msg)]
    if usage:
        u = MagicMock()
        u.model_dump.return_value = {"prompt_tokens": 1, "completion_tokens": 2}
        resp.usage = u
    else:
        resp.usage = None
    return resp


def test_openai_chat_basic():
    llm = OpenAILLM(model="gpt-4o", api_key="k")
    llm._client = MagicMock()
    llm._client.chat.completions.create.return_value = _openai_response(content="hello")
    out = llm.chat([{"role": "user", "content": "hi"}])
    assert out["content"] == "hello"
    assert out["usage"] == {"prompt_tokens": 1, "completion_tokens": 2}
    assert out["tool_calls"] is None


def test_openai_chat_no_usage():
    llm = OpenAILLM(model="gpt-4o", api_key="k")
    llm._client = MagicMock()
    llm._client.chat.completions.create.return_value = _openai_response(usage=False)
    out = llm.chat([{"role": "user", "content": "hi"}])
    assert out["usage"] is None


def test_openai_chat_with_tools():
    tc = MagicMock()
    tc.function.name = "get_weather"
    tc.function.arguments = '{"city": "Beijing"}'
    tc.id = "call_1"
    llm = OpenAILLM(model="gpt-4o", api_key="k")
    llm._client = MagicMock()
    llm._client.chat.completions.create.return_value = _openai_response(
        content=None, tool_calls=[tc]
    )
    out = llm.chat_with_tools(
        [{"role": "user", "content": "weather"}],
        [{"type": "function", "function": {"name": "get_weather"}}],
    )
    assert out["content"] is None
    assert len(out["tool_calls"]) == 1
    assert out["tool_calls"][0]["name"] == "get_weather"
    assert out["tool_calls"][0]["arguments"] == {"city": "Beijing"}


def test_openai_chat_with_tools_bad_json():
    tc = MagicMock()
    tc.function.name = "f"
    tc.function.arguments = "not-json{"
    tc.id = "c1"
    llm = OpenAILLM(model="gpt-4o", api_key="k")
    llm._client = MagicMock()
    llm._client.chat.completions.create.return_value = _openai_response(tool_calls=[tc])
    out = llm.chat_with_tools([{"role": "user", "content": "x"}], [])
    assert out["tool_calls"][0]["arguments"] == {}


def _fake_anthropic_client(text="hi there", tool_blocks=None, in_tok=5, out_tok=6):
    fake_anthropic = MagicMock()
    fake_client = MagicMock()
    fake_anthropic.Anthropic.return_value = fake_client

    msg_resp = MagicMock()
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = text
    blocks = [text_block]
    if tool_blocks:
        blocks.extend(tool_blocks)
    msg_resp.content = blocks
    usage = MagicMock()
    usage.input_tokens = in_tok
    usage.output_tokens = out_tok
    msg_resp.usage = usage
    fake_client.messages.create.return_value = msg_resp
    return fake_anthropic, fake_client


def test_anthropic_chat_mocked(monkeypatch):
    fake_anthropic, fake_client = _fake_anthropic_client()
    with monkeypatch.context() as mp:
        mp.setitem(sys.modules, "anthropic", fake_anthropic)
        llm = AnthropicLLM(model="claude-x", api_key="k")
    llm._client = fake_client
    out = llm.chat(
        [{"role": "system", "content": "sys"}, {"role": "user", "content": "hi"}]
    )
    assert out["content"] == "hi there"
    assert out["usage"]["input_tokens"] == 5
    assert out["tool_calls"] is None


def test_anthropic_chat_with_tools_mocked(monkeypatch):
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.id = "t1"
    tool_block.name = "f"
    tool_block.input = {"a": 1}
    fake_anthropic, fake_client = _fake_anthropic_client(
        text="ok", tool_blocks=[tool_block]
    )
    with monkeypatch.context() as mp:
        mp.setitem(sys.modules, "anthropic", fake_anthropic)
        llm = AnthropicLLM(model="claude-x", api_key="k")
    llm._client = fake_client
    out = llm.chat_with_tools(
        [{"role": "user", "content": "x"}],
        [{"type": "function", "function": {"name": "f", "description": "d", "parameters": {}}}],
    )
    assert out["content"] == "ok"
    assert out["tool_calls"][0]["name"] == "f"
    assert out["tool_calls"][0]["arguments"] == {"a": 1}
