"""测试记忆系统"""
import pytest
import os
import tempfile
from codeagents.memory.memory import Memory


def test_memory_basic():
    """测试基本记忆功能"""
    memory = Memory()

    memory.remember("key1", "value1")
    assert memory.recall("key1") == "value1"

    memory.remember("key2", {"a": 1, "b": 2})
    assert memory.recall("key2") == {"a": 1, "b": 2}


def test_memory_importance():
    """测试记忆重要性"""
    memory = Memory()

    memory.remember("important", "very important data", importance=1.0)
    memory.remember("normal", "normal important data", importance=0.5)

    results = memory.search_knowledge("important")
    assert len(results) >= 2
    # 高重要性的应排在前面
    assert results[0].importance >= results[1].importance


def test_memory_forget():
    """测试删除记忆"""
    memory = Memory()

    memory.remember("to_delete", "value")
    assert memory.recall("to_delete") == "value"

    assert memory.forget("to_delete") is True
    assert memory.recall("to_delete") is None
    assert memory.forget("nonexistent") is False


def test_memory_search():
    """测试搜索记忆"""
    memory = Memory()

    memory.remember("python_key", "Python is great")
    memory.remember("java_key", "Java is also good")
    memory.remember("rust_key", "Rust is fast")

    results = memory.search_knowledge("Python")
    assert len(results) >= 1

    results = memory.search_knowledge("is")
    assert len(results) >= 3


def test_conversation_memory():
    """测试对话记忆"""
    memory = Memory()

    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
    ]

    memory.add_conversation("conv1", messages)

    conv = memory.get_conversation("conv1")
    assert conv is not None
    assert len(conv.messages) == 2


def test_conversation_search():
    """测试搜索对话"""
    memory = Memory()

    memory.add_conversation("conv1", [
        {"role": "user", "content": "How to write Python code?"},
        {"role": "assistant", "content": "Let me help you with Python."},
    ])

    memory.add_conversation("conv2", [
        {"role": "user", "content": "How to bake bread?"},
        {"role": "assistant", "content": "Bread baking is easy."},
    ])

    results = memory.search_conversations("Python")
    assert len(results) == 1
    assert results[0].conversation_id == "conv1"


def test_recent_conversations():
    """测试获取最近对话"""
    memory = Memory()

    for i in range(5):
        memory.add_conversation(f"conv{i}", [{"role": "user", "content": f"message {i}"}])

    recent = memory.get_recent_conversations(3)
    assert len(recent) == 3


def test_memory_persistence():
    """测试记忆持久化"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建记忆并保存
        mem1 = Memory(storage_path=tmpdir)
        mem1.remember("test_key", "test_value")
        mem1.add_conversation("test_conv", [{"role": "user", "content": "test"}])

        # 重新加载记忆
        mem2 = Memory(storage_path=tmpdir)
        assert mem2.recall("test_key") == "test_value"
        assert mem2.get_conversation("test_conv") is not None


def test_memory_nonexistent_key():
    """测试不存在的键"""
    memory = Memory()
    assert memory.recall("nonexistent") is None


def test_memory_metadata():
    """测试记忆元数据"""
    memory = Memory()

    memory.remember(
        "key_with_meta",
        "value",
        metadata={"source": "test", "version": 1},
    )

    # 搜索应该也能工作
    results = memory.search_knowledge("key_with_meta")
    assert len(results) >= 1
