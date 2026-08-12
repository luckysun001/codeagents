"""记忆系统"""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import os


@dataclass
class Conversation:
    """对话记录"""
    conversation_id: str
    messages: List[Dict[str, Any]]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class MemoryItem:
    """记忆条目"""
    key: str
    value: Any
    importance: float = 0.5  # 0.0 - 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


class Memory:
    """短期和长期记忆系统"""

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path
        self.conversations: Dict[str, Conversation] = {}
        self.knowledge: Dict[str, MemoryItem] = {}
        self._load()

    def _load(self):
        """从磁盘加载记忆"""
        if not self.storage_path or not os.path.exists(self.storage_path):
            return

        try:
            conv_path = os.path.join(self.storage_path, "conversations.json")
            if os.path.exists(conv_path):
                with open(conv_path, "r") as f:
                    data = json.load(f)
                    for cid, conv_data in data.items():
                        self.conversations[cid] = Conversation(
                            conversation_id=cid,
                            messages=conv_data["messages"],
                            metadata=conv_data.get("metadata", {}),
                            created_at=datetime.fromisoformat(conv_data["created_at"]),
                            updated_at=datetime.fromisoformat(conv_data["updated_at"]),
                        )

            know_path = os.path.join(self.storage_path, "knowledge.json")
            if os.path.exists(know_path):
                with open(know_path, "r") as f:
                    data = json.load(f)
                    for key, item_data in data.items():
                        self.knowledge[key] = MemoryItem(
                            key=key,
                            value=item_data["value"],
                            importance=item_data.get("importance", 0.5),
                            metadata=item_data.get("metadata", {}),
                            created_at=datetime.fromisoformat(item_data["created_at"]),
                        )
        except Exception as e:
            print(f"Warning: Failed to load memory: {e}")

    def _save(self):
        """保存记忆到磁盘"""
        if not self.storage_path:
            return

        os.makedirs(self.storage_path, exist_ok=True)

        # 保存对话
        conv_path = os.path.join(self.storage_path, "conversations.json")
        conv_data = {
            cid: {
                "messages": conv.messages,
                "metadata": conv.metadata,
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat(),
            }
            for cid, conv in self.conversations.items()
        }
        with open(conv_path, "w") as f:
            json.dump(conv_data, f, indent=2, ensure_ascii=False)

        # 保存知识库
        know_path = os.path.join(self.storage_path, "knowledge.json")
        know_data = {
            key: {
                "value": item.value,
                "importance": item.importance,
                "metadata": item.metadata,
                "created_at": item.created_at.isoformat(),
            }
            for key, item in self.knowledge.items()
        }
        with open(know_path, "w") as f:
            json.dump(know_data, f, indent=2, ensure_ascii=False)

    def add_conversation(
        self,
        conversation_id: str,
        messages: List[Dict[str, Any]],
        metadata: Dict[str, Any] = None,
    ):
        """添加或更新对话记录"""
        if conversation_id in self.conversations:
            conv = self.conversations[conversation_id]
            conv.messages = messages
            conv.updated_at = datetime.now()
            if metadata:
                conv.metadata.update(metadata)
        else:
            self.conversations[conversation_id] = Conversation(
                conversation_id=conversation_id,
                messages=messages,
                metadata=metadata or {},
            )
        self._save()

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """获取对话记录"""
        return self.conversations.get(conversation_id)

    def search_conversations(self, query: str, limit: int = 5) -> List[Conversation]:
        """搜索对话（简单关键词搜索）"""
        results = []
        query_lower = query.lower()
        for conv in self.conversations.values():
            text = json.dumps(conv.messages, ensure_ascii=False).lower()
            if query_lower in text:
                results.append(conv)
        return results[:limit]

    def remember(self, key: str, value: Any, importance: float = 0.5, metadata: Dict[str, Any] = None):
        """添加长期记忆"""
        self.knowledge[key] = MemoryItem(
            key=key,
            value=value,
            importance=importance,
            metadata=metadata or {},
        )
        self._save()

    def recall(self, key: str) -> Optional[Any]:
        """检索长期记忆"""
        item = self.knowledge.get(key)
        return item.value if item else None

    def search_knowledge(self, query: str, limit: int = 10) -> List[MemoryItem]:
        """搜索知识库"""
        results = []
        query_lower = query.lower()
        for item in self.knowledge.values():
            text = f"{item.key} {json.dumps(item.value, ensure_ascii=False)}".lower()
            if query_lower in text:
                results.append(item)

        # 按重要性排序
        results.sort(key=lambda x: x.importance, reverse=True)
        return results[:limit]

    def forget(self, key: str) -> bool:
        """删除记忆"""
        if key in self.knowledge:
            del self.knowledge[key]
            self._save()
            return True
        return False

    def get_recent_conversations(self, limit: int = 10) -> List[Conversation]:
        """获取最近的对话"""
        convs = sorted(self.conversations.values(), key=lambda c: c.updated_at, reverse=True)
        return convs[:limit]
