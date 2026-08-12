"""Git工具"""
import subprocess
import os
from typing import Optional
from ..tools.registry import tool, ToolRegistry


@tool(name="git_status", description="查看Git状态", category="git")
def git_status(cwd: str = ".") -> str:
    """查看Git仓库状态"""
    try:
        result = subprocess.run(
            ["git", "status"],
            capture_output=True,
            text=True,
            cwd=cwd,
        )
        return result.stdout + result.stderr
    except Exception as e:
        return f"Error: {e}"


@tool(name="git_diff", description="查看Git差异", category="git")
def git_diff(cwd: str = ".", staged: bool = False) -> str:
    """查看代码变更"""
    cmd = ["git", "diff", "--cached"] if staged else ["git", "diff"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
        output = result.stdout
        if not output:
            return "No changes found."
        return output
    except Exception as e:
        return f"Error: {e}"


@tool(name="git_log", description="查看Git提交历史", category="git")
def git_log(cwd: str = ".", max_count: int = 20) -> str:
    """查看提交历史"""
    try:
        result = subprocess.run(
            ["git", "log", f"--oneline", f"-n{max_count}"],
            capture_output=True,
            text=True,
            cwd=cwd,
        )
        return result.stdout or "No commits found."
    except Exception as e:
        return f"Error: {e}"


@tool(name="git_add", description="添加文件到暂存区", category="git")
def git_add(path: str = ".", cwd: str = ".") -> str:
    """添加文件到暂存区"""
    try:
        result = subprocess.run(
            ["git", "add", path],
            capture_output=True,
            text=True,
            cwd=cwd,
        )
        if result.returncode == 0:
            return f"Added: {path}"
        return result.stderr
    except Exception as e:
        return f"Error: {e}"


@tool(name="git_commit", description="提交代码", category="git")
def git_commit(message: str, cwd: str = ".") -> str:
    """提交代码"""
    try:
        result = subprocess.run(
            ["git", "commit", "-m", message],
            capture_output=True,
            text=True,
            cwd=cwd,
        )
        return result.stdout + result.stderr
    except Exception as e:
        return f"Error: {e}"


@tool(name="git_branch", description="创建或查看分支", category="git")
def git_branch(name: str = None, cwd: str = ".") -> str:
    """创建或查看分支"""
    cmd = ["git", "branch"]
    if name:
        cmd.append(name)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
        return result.stdout + result.stderr
    except Exception as e:
        return f"Error: {e}"


@tool(name="git_checkout", description="切换分支", category="git")
def git_checkout(branch: str, cwd: str = ".") -> str:
    """切换分支"""
    try:
        result = subprocess.run(
            ["git", "checkout", branch],
            capture_output=True,
            text=True,
            cwd=cwd,
        )
        return result.stdout + result.stderr
    except Exception as e:
        return f"Error: {e}"


@tool(name="git_init", description="初始化Git仓库", category="git")
def git_init(cwd: str = ".") -> str:
    """初始化Git仓库"""
    try:
        result = subprocess.run(
            ["git", "init"],
            capture_output=True,
            text=True,
            cwd=cwd,
        )
        return result.stdout + result.stderr
    except Exception as e:
        return f"Error: {e}"


def get_git_tools() -> ToolRegistry:
    """获取Git工具注册表"""
    registry = ToolRegistry()
    registry.register(git_status)
    registry.register(git_diff)
    registry.register(git_log)
    registry.register(git_add)
    registry.register(git_commit)
    registry.register(git_branch)
    registry.register(git_checkout)
    registry.register(git_init)
    return registry
