"""消息总线：智能体之间的通信"""
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid
from enum import Enum


class MessagePriority(int, Enum):
    """消息优先级"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


@dataclass
class BusMessage:
    """总线上的消息"""
    sender_id: str
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    receiver_id: Optional[str] = None  # None = 广播
    topic: str = "general"
    content: Any = None
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __lt__(self, other: "BusMessage") -> bool:
        """按优先级排序"""
        return self.priority > other.priority  # 高优先级在前


class MessageBus:
    """消息总线"""

    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._agent_subscribers: Dict[str, List[Callable]] = {}
        self._message_history: List[BusMessage] = []

    def subscribe(self, topic: str, callback: Callable):
        """订阅主题"""
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(callback)

    def subscribe_to_agent(self, agent_id: str, callback: Callable):
        """订阅特定智能体的所有消息"""
        if agent_id not in self._agent_subscribers:
            self._agent_subscribers[agent_id] = []
        self._agent_subscribers[agent_id].append(callback)

    def publish(
        self,
        sender_id: str,
        content: Any,
        receiver_id: Optional[str] = None,
        topic: str = "general",
        priority: MessagePriority = MessagePriority.NORMAL,
        metadata: Dict[str, Any] = None,
    ) -> BusMessage:
        """发布消息"""
        message = BusMessage(
            sender_id=sender_id,
            receiver_id=receiver_id,
            topic=topic,
            content=content,
            priority=priority,
            metadata=metadata or {},
        )

        self._message_history.append(message)
        self._deliver(message)
        return message

    def _deliver(self, message: BusMessage):
        """投递消息"""
        # 主题订阅者
        if message.topic in self._subscribers:
            for callback in self._subscribers[message.topic]:
                try:
                    callback(message)
                except Exception as e:
                    print(f"Error in subscriber callback: {e}")

        # 特定接收者
        if message.receiver_id and message.receiver_id in self._agent_subscribers:
            for callback in self._agent_subscribers[message.receiver_id]:
                try:
                    callback(message)
                except Exception as e:
                    print(f"Error in agent subscriber callback: {e}")

        # 广播：发送给所有智能体订阅者
        if message.receiver_id is None:
            for agent_id, callbacks in self._agent_subscribers.items():
                if agent_id != message.sender_id:  # 不发给自己
                    for callback in callbacks:
                        try:
                            callback(message)
                        except Exception as e:
                            print(f"Error in broadcast callback: {e}")

    def get_history(
        self,
        sender_id: Optional[str] = None,
        receiver_id: Optional[str] = None,
        topic: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[BusMessage]:
        """获取消息历史"""
        history = self._message_history

        if sender_id:
            history = [m for m in history if m.sender_id == sender_id]
        if receiver_id:
            history = [m for m in history if m.receiver_id == receiver_id]
        if topic:
            history = [m for m in history if m.topic == topic]

        if limit:
            history = history[-limit:]

        return history

    def clear_history(self):
        """清空历史"""
        self._message_history.clear()


class SharedContext:
    """多智能体共享上下文"""

    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._locks: Dict[str, bool] = {}

    def get(self, key: str, default: Any = None) -> Any:
        """获取数据"""
        return self._data.get(key, default)

    def set(self, key: str, value: Any, overwrite: bool = True) -> bool:
        """设置数据"""
        if not overwrite and key in self._data:
            return False
        self._data[key] = value
        return True

    def append(self, key: str, value: Any) -> bool:
        """追加到列表"""
        if key not in self._data:
            self._data[key] = []
        if isinstance(self._data[key], list):
            self._data[key].append(value)
            return True
        return False

    def keys(self) -> List[str]:
        """获取所有键"""
        return list(self._data.keys())

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self._data.copy()

    def clear(self):
        """清空"""
        self._data.clear()
