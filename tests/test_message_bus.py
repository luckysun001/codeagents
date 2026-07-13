"""测试消息总线"""
import pytest
from codeagents.orchestration.message_bus import (
    MessageBus,
    SharedContext,
    MessagePriority,
)


def test_message_bus_basic():
    """测试基本消息发布订阅"""
    bus = MessageBus()

    received = []

    def callback(message):
        received.append(message)

    bus.subscribe("test_topic", callback)
    bus.publish("sender1", "hello world", topic="test_topic")

    assert len(received) == 1
    assert received[0].content == "hello world"
    assert received[0].sender_id == "sender1"


def test_message_bus_broadcast():
    """测试广播消息"""
    bus = MessageBus()

    received1 = []
    received2 = []

    def callback1(message):
        received1.append(message)

    def callback2(message):
        received2.append(message)

    bus.subscribe_to_agent("agent1", callback1)
    bus.subscribe_to_agent("agent2", callback2)

    # 广播消息（receiver_id=None）
    bus.publish("sender", "broadcast message", receiver_id=None, topic="general")

    # 两个订阅者都应该收到
    assert len(received1) == 1
    assert len(received2) == 1


def test_message_bus_specific_receiver():
    """测试特定接收者消息"""
    bus = MessageBus()

    received1 = []
    received2 = []

    def callback1(message):
        received1.append(message)

    def callback2(message):
        received2.append(message)

    bus.subscribe_to_agent("agent1", callback1)
    bus.subscribe_to_agent("agent2", callback2)

    # 只发送给 agent1
    bus.publish("sender", "direct message", receiver_id="agent1", topic="general")

    assert len(received1) == 1
    assert len(received2) == 0  # agent2 不应收到


def test_message_priority():
    """测试消息优先级"""
    bus = MessageBus()

    msg = bus.publish(
        "sender",
        "urgent message",
        priority=MessagePriority.URGENT,
    )

    assert msg.priority == MessagePriority.URGENT


def test_message_history():
    """测试消息历史"""
    bus = MessageBus()

    bus.publish("sender1", "message 1", topic="topic1")
    bus.publish("sender2", "message 2", topic="topic2")
    bus.publish("sender1", "message 3", topic="topic1")

    # 获取所有历史
    history = bus.get_history()
    assert len(history) == 3

    # 按发送者过滤
    history = bus.get_history(sender_id="sender1")
    assert len(history) == 2

    # 按主题过滤
    history = bus.get_history(topic="topic1")
    assert len(history) == 2

    # 限制数量
    history = bus.get_history(limit=2)
    assert len(history) == 2


def test_clear_history():
    """测试清空历史"""
    bus = MessageBus()

    bus.publish("sender", "message")
    assert len(bus.get_history()) == 1

    bus.clear_history()
    assert len(bus.get_history()) == 0


def test_shared_context_basic():
    """测试共享上下文"""
    ctx = SharedContext()

    ctx.set("key1", "value1")
    assert ctx.get("key1") == "value1"

    ctx.set("key2", 42)
    assert ctx.get("key2") == 42


def test_shared_context_default():
    """测试默认值"""
    ctx = SharedContext()
    assert ctx.get("nonexistent", "default") == "default"


def test_shared_context_append():
    """测试追加到列表"""
    ctx = SharedContext()

    ctx.append("list_key", "item1")
    ctx.append("list_key", "item2")

    result = ctx.get("list_key")
    assert isinstance(result, list)
    assert len(result) == 2
    assert "item1" in result


def test_shared_context_keys():
    """测试获取所有键"""
    ctx = SharedContext()

    ctx.set("a", 1)
    ctx.set("b", 2)
    ctx.set("c", 3)

    keys = ctx.keys()
    assert len(keys) == 3
    assert "a" in keys
    assert "b" in keys
    assert "c" in keys


def test_shared_context_to_dict():
    """测试转换为字典"""
    ctx = SharedContext()

    ctx.set("a", 1)
    ctx.set("b", 2)

    d = ctx.to_dict()
    assert d == {"a": 1, "b": 2}


def test_shared_context_clear():
    """测试清空"""
    ctx = SharedContext()

    ctx.set("a", 1)
    ctx.set("b", 2)
    assert len(ctx.keys()) == 2

    ctx.clear()
    assert len(ctx.keys()) == 0


def test_shared_context_no_overwrite():
    """测试不覆盖现有值"""
    ctx = SharedContext()

    ctx.set("key", "original")
    result = ctx.set("key", "new_value", overwrite=False)

    assert result is False
    assert ctx.get("key") == "original"


def test_message_metadata():
    """测试消息元数据"""
    bus = MessageBus()

    msg = bus.publish(
        "sender",
        "content",
        metadata={"type": "test", "priority": "high"},
    )

    assert "type" in msg.metadata
    assert msg.metadata["type"] == "test"
