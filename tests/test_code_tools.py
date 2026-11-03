"""代码执行工具测试

通过工具注册表执行：
- execute_python / execute_command：真实运行（确定性、无外部依赖）
- run_pytest：在临时目录跑一个会通过的最小测试套件（需要 PATH 中有 python）
- check_pep8 / check_type_hints：通过 mock subprocess.run 覆盖 通过 / 有告警 / 未安装 三条分支
"""
import os
import shutil
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from codeagents.tools.code_tools import get_code_tools

REG = get_code_tools()


def test_execute_python_stdout():
    out = REG.execute("execute_python", {"code": "print('hello from exec')"})
    assert "hello from exec" in out
    assert "Return Code: 0" in out


def test_execute_python_stderr_and_return_code():
    out = REG.execute(
        "execute_python", {"code": "import sys; sys.stderr.write('boom'); sys.exit(3)"}
    )
    assert "boom" in out
    assert "Return Code: 3" in out


def test_execute_python_timeout():
    out = REG.execute("execute_python", {"code": "import time; time.sleep(5)", "timeout": 1})
    assert "timed out" in out


def test_execute_command_success():
    out = REG.execute("execute_command", {"command": "echo cli-test-output"})
    assert "cli-test-output" in out
    assert "Return Code: 0" in out


@pytest.mark.skipif(shutil.which("python") is None, reason="python not on PATH")
def test_run_pytest_on_temp_tests():
    with tempfile.TemporaryDirectory() as tmp:
        test_file = os.path.join(tmp, "test_dummy.py")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("def test_ok():\n    assert 1 + 1 == 2\n")
        out = REG.execute("run_pytest", {"path": tmp, "args": "-q"})
        assert isinstance(out, str)
        assert "passed" in out.lower()


def test_check_pep8_passed():
    fake = MagicMock()
    fake.returncode = 0
    fake.stdout = ""
    fake.stderr = ""
    with patch("codeagents.tools.code_tools.subprocess.run", return_value=fake):
        out = REG.execute("check_pep8", {"path": "x.py"})
    assert "PEP8 check passed" in out


def test_check_pep8_issues():
    fake = MagicMock()
    fake.returncode = 1
    fake.stdout = "x.py:1:1: E1 something"
    fake.stderr = ""
    with patch("codeagents.tools.code_tools.subprocess.run", return_value=fake):
        out = REG.execute("check_pep8", {"path": "x.py"})
    assert "PEP8 issues found" in out


def test_check_pep8_not_installed():
    def _raise(*_a, **_k):
        raise FileNotFoundError("No flake8")

    with patch("codeagents.tools.code_tools.subprocess.run", side_effect=_raise):
        out = REG.execute("check_pep8", {"path": "x.py"})
    assert "flake8 not installed" in out


def test_check_type_hints_passed():
    fake = MagicMock()
    fake.returncode = 0
    fake.stdout = ""
    fake.stderr = ""
    with patch("codeagents.tools.code_tools.subprocess.run", return_value=fake):
        out = REG.execute("check_type_hints", {"path": "x.py"})
    assert "Type check passed" in out


def test_check_type_hints_errors():
    fake = MagicMock()
    fake.returncode = 1
    fake.stdout = "x.py:1: error: int has no attr"
    fake.stderr = ""
    with patch("codeagents.tools.code_tools.subprocess.run", return_value=fake):
        out = REG.execute("check_type_hints", {"path": "x.py"})
    assert "Type errors found" in out


def test_check_type_hints_not_installed():
    def _raise(*_a, **_k):
        raise FileNotFoundError("No mypy")

    with patch("codeagents.tools.code_tools.subprocess.run", side_effect=_raise):
        out = REG.execute("check_type_hints", {"path": "x.py"})
    assert "mypy not installed" in out


def test_get_code_tools_registry():
    names = {t.name for t in REG.list_tools()}
    expected = {
        "execute_python",
        "execute_command",
        "run_pytest",
        "check_pep8",
        "check_type_hints",
    }
    assert expected <= names
