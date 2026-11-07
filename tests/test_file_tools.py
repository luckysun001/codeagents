"""文件操作工具测试

通过工具注册表（真实调用路径 registry.execute）执行，全部基于临时目录，
确定性、无网络依赖。
"""

import os
import tempfile

from codeagents.tools.file_tools import get_file_tools

REG = get_file_tools()


def _write(tmp: str, name: str, content: str) -> str:
    path = os.path.join(tmp, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def test_read_file_success():
    with tempfile.TemporaryDirectory() as tmp:
        p = _write(tmp, "a.txt", "hello world")
        out = REG.execute("read_file", {"path": p})
        assert "hello world" in out
        assert p in out


def test_read_file_not_found():
    out = REG.execute("read_file", {"path": "/nonexistent/path/xyz.txt"})
    assert "Error" in out and "not found" in out.lower()


def test_write_file_success():
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "sub", "out.txt")
        out = REG.execute("write_file", {"path": p, "content": "data"})
        assert "Successfully wrote" in out
        assert os.path.exists(p)
        with open(p, encoding="utf-8") as f:
            assert f.read() == "data"


def test_write_file_into_directory_errors():
    with tempfile.TemporaryDirectory() as tmp:
        out = REG.execute("write_file", {"path": tmp, "content": "x"})
        assert "Error writing file" in out


def test_list_dir_success():
    with tempfile.TemporaryDirectory() as tmp:
        _write(tmp, "a.txt", "1")
        os.mkdir(os.path.join(tmp, "subdir"))
        out = REG.execute("list_dir", {"path": tmp})
        assert "a.txt" in out
        assert "subdir" in out


def test_list_dir_hidden_filtering():
    with tempfile.TemporaryDirectory() as tmp:
        _write(tmp, ".hidden", "1")
        out = REG.execute("list_dir", {"path": tmp, "show_hidden": False})
        assert ".hidden" not in out
        out2 = REG.execute("list_dir", {"path": tmp, "show_hidden": True})
        assert ".hidden" in out2


def test_list_dir_not_found():
    out = REG.execute("list_dir", {"path": "/no/such/dir"})
    assert "Directory not found" in out


def test_file_exists_file_and_dir_and_missing():
    with tempfile.TemporaryDirectory() as tmp:
        p = _write(tmp, "f.txt", "1")
        out = REG.execute("file_exists", {"path": p})
        assert "Exists: True" in out
        assert "Is Directory: False" in out

        out2 = REG.execute("file_exists", {"path": tmp})
        assert "Is Directory: True" in out2

        out3 = REG.execute("file_exists", {"path": "/no/such"})
        assert "Exists: False" in out3


def test_search_files():
    with tempfile.TemporaryDirectory() as tmp:
        _write(tmp, "x.py", "1")
        _write(tmp, "y.py", "1")
        _write(tmp, "z.txt", "1")
        out = REG.execute("search_files", {"path": tmp, "pattern": "*.py"})
        assert "x.py" in out and "y.py" in out
        assert "z.txt" not in out

        out_empty = REG.execute("search_files", {"path": tmp, "pattern": "*.go"})
        assert "No files found" in out_empty


def test_grep_file_matches_and_case():
    with tempfile.TemporaryDirectory() as tmp:
        p = _write(tmp, "code.py", "def foo():\n    return 42\n")
        out = REG.execute("grep_file", {"path": p, "pattern": "def foo"})
        assert "Line 1" in out

        out_none = REG.execute("grep_file", {"path": p, "pattern": "nonexistent_pattern"})
        assert "No matches" in out_none

        out_case = REG.execute("grep_file", {"path": p, "pattern": "DEF FOO", "ignore_case": True})
        assert "Line 1" in out_case


def test_grep_file_not_found():
    out = REG.execute("grep_file", {"path": "/no/such/file.py", "pattern": "x"})
    assert "File not found" in out


def test_get_file_tools_registry():
    names = {t.name for t in REG.list_tools()}
    expected = {
        "read_file",
        "write_file",
        "list_dir",
        "file_exists",
        "search_files",
        "grep_file",
    }
    assert expected <= names
