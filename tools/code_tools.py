"""代码执行工具"""
import subprocess
import tempfile
import os
import sys
from typing import Dict, Any, Optional
from ..tools.registry import tool, ToolRegistry


@tool(name="execute_python", description="执行Python代码", category="code")
def execute_python(code: str, timeout: int = 30) -> str:
    """执行Python代码"""
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        output = []
        if result.stdout:
            output.append(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            output.append(f"STDERR:\n{result.stderr}")
        output.append(f"Return Code: {result.returncode}")

        return "\n".join(output)
    except subprocess.TimeoutExpired:
        return f"Error: Execution timed out after {timeout} seconds"
    except Exception as e:
        return f"Error executing code: {e}"


@tool(name="execute_command", description="执行Shell命令", category="code")
def execute_command(command: str, cwd: str = ".", timeout: int = 60) -> str:
    """执行Shell命令"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout,
        )

        output = []
        if result.stdout:
            output.append(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            output.append(f"STDERR:\n{result.stderr}")
        output.append(f"Return Code: {result.returncode}")

        return "\n".join(output)
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds"
    except Exception as e:
        return f"Error executing command: {e}"


@tool(name="run_pytest", description="运行pytest测试", category="code")
def run_pytest(path: str = "tests", args: str = "-v", timeout: int = 120) -> str:
    """运行pytest测试"""
    try:
        cmd = f"python -m pytest {path} {args}"
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        output = []
        if result.stdout:
            output.append(result.stdout)
        if result.stderr:
            output.append(result.stderr)

        return "\n".join(output)
    except Exception as e:
        return f"Error running pytest: {e}"


@tool(name="check_pep8", description="检查Python代码风格", category="code")
def check_pep8(path: str) -> str:
    """使用flake8检查代码风格"""
    try:
        result = subprocess.run(
            ["python", "-m", "flake8", path, "--max-line-length=120"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return "PEP8 check passed! No issues found."
        else:
            return f"PEP8 issues found:\n{result.stdout}\n{result.stderr}"
    except FileNotFoundError:
        return "Warning: flake8 not installed. Install with: pip install flake8"
    except Exception as e:
        return f"Error checking PEP8: {e}"


@tool(name="check_type_hints", description="检查类型注解", category="code")
def check_type_hints(path: str) -> str:
    """使用mypy检查类型注解"""
    try:
        result = subprocess.run(
            ["python", "-m", "mypy", path, "--ignore-missing-imports"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return "Type check passed! No type errors found."
        else:
            return f"Type errors found:\n{result.stdout}\n{result.stderr}"
    except FileNotFoundError:
        return "Warning: mypy not installed. Install with: pip install mypy"
    except Exception as e:
        return f"Error checking types: {e}"


def get_code_tools() -> ToolRegistry:
    """获取代码工具注册表"""
    registry = ToolRegistry()
    registry.register(execute_python)
    registry.register(execute_command)
    registry.register(run_pytest)
    registry.register(check_pep8)
    registry.register(check_type_hints)
    return registry
