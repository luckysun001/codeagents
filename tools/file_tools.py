"""文件操作工具"""
import os
from typing import List, Dict, Any, Optional
from ..tools.registry import tool, ToolRegistry


@tool(name="read_file", description="读取文件内容", category="file")
def read_file(path: str, encoding: str = "utf-8") -> str:
    """读取文件内容"""
    if not os.path.exists(path):
        return f"Error: File not found: {path}"

    try:
        with open(path, "r", encoding=encoding) as f:
            content = f.read()
        return f"=== File: {path} ===\n{content}"
    except Exception as e:
        return f"Error reading file: {e}"


@tool(name="write_file", description="写入文件内容", category="file")
def write_file(path: str, content: str, encoding: str = "utf-8") -> str:
    """写入文件内容"""
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding=encoding) as f:
            f.write(content)
        return f"Successfully wrote to {path} ({len(content)} bytes)"
    except Exception as e:
        return f"Error writing file: {e}"


@tool(name="list_dir", description="列出目录内容", category="file")
def list_dir(path: str = ".", show_hidden: bool = False) -> str:
    """列出目录内容"""
    if not os.path.exists(path):
        return f"Error: Directory not found: {path}"

    try:
        entries = []
        for entry in sorted(os.listdir(path)):
            if not show_hidden and entry.startswith("."):
                continue

            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                entries.append(f"[DIR]  {entry}/")
            else:
                size = os.path.getsize(full_path)
                entries.append(f"[FILE] {entry} ({size} bytes)")

        return f"=== Directory: {path} ===\n" + "\n".join(entries)
    except Exception as e:
        return f"Error listing directory: {e}"


@tool(name="file_exists", description="检查文件是否存在", category="file")
def file_exists(path: str) -> str:
    """检查文件是否存在"""
    exists = os.path.exists(path)
    is_dir = os.path.isdir(path) if exists else False
    return f"Path: {path}\nExists: {exists}\nIs Directory: {is_dir}"


@tool(name="search_files", description="在目录中搜索文件", category="file")
def search_files(path: str = ".", pattern: str = "*.py") -> str:
    """搜索文件"""
    import glob

    try:
        files = glob.glob(os.path.join(path, "**", pattern), recursive=True)
        if not files:
            return f"No files found matching pattern: {pattern}"
        return f"Found {len(files)} files:\n" + "\n".join(files[:50])
    except Exception as e:
        return f"Error searching files: {e}"


@tool(name="grep_file", description="在文件中搜索内容", category="file")
def grep_file(path: str, pattern: str, ignore_case: bool = True) -> str:
    """在文件中搜索内容"""
    import re

    if not os.path.exists(path):
        return f"Error: File not found: {path}"

    try:
        flags = re.IGNORECASE if ignore_case else 0
        regex = re.compile(pattern, flags)

        matches = []
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f, 1):
                if regex.search(line):
                    matches.append(f"Line {i}: {line.rstrip()}")

        if not matches:
            return f"No matches found for '{pattern}' in {path}"

        return f"Found {len(matches)} matches:\n" + "\n".join(matches[:30])
    except Exception as e:
        return f"Error searching: {e}"


def get_file_tools() -> ToolRegistry:
    """获取文件工具注册表"""
    registry = ToolRegistry()
    registry.register(read_file)
    registry.register(write_file)
    registry.register(list_dir)
    registry.register(file_exists)
    registry.register(search_files)
    registry.register(grep_file)
    return registry
