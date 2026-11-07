"""Git 工具测试

通过工具注册表执行，使用临时目录中的真实本地 git 仓库，不联网。
依赖系统 PATH 中存在 git 可执行文件（CI 的 ubuntu-latest 与本地均满足）。
"""

import os
import subprocess
import tempfile

from codeagents.tools.git_tools import get_git_tools

REG = get_git_tools()


def _init_repo(path: str):
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, check=True)


def _commit_file(path: str, name: str, content: str = "hello"):
    with open(os.path.join(path, name), "w", encoding="utf-8") as f:
        f.write(content)
    subprocess.run(["git", "add", name], cwd=path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", f"add {name}"], cwd=path, check=True)


def test_git_init_creates_repo():
    with tempfile.TemporaryDirectory() as tmp:
        REG.execute("git_init", {"cwd": tmp})
        r = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=tmp,
            capture_output=True,
            text=True,
        )
        assert r.stdout.strip() == "true"


def test_git_status():
    with tempfile.TemporaryDirectory() as tmp:
        _init_repo(tmp)
        _commit_file(tmp, "a.txt")
        out = REG.execute("git_status", {"cwd": tmp})
        assert isinstance(out, str)
        assert "branch" in out.lower()


def test_git_diff_no_changes():
    with tempfile.TemporaryDirectory() as tmp:
        _init_repo(tmp)
        _commit_file(tmp, "a.txt")
        out = REG.execute("git_diff", {"cwd": tmp})
        assert "No changes found." in out


def test_git_diff_staged():
    with tempfile.TemporaryDirectory() as tmp:
        _init_repo(tmp)
        _commit_file(tmp, "a.txt")
        with open(os.path.join(tmp, "a.txt"), "w", encoding="utf-8") as f:
            f.write("changed")
        subprocess.run(["git", "add", "a.txt"], cwd=tmp, check=True)
        out = REG.execute("git_diff", {"cwd": tmp, "staged": True})
        assert "changed" in out


def test_git_log():
    with tempfile.TemporaryDirectory() as tmp:
        _init_repo(tmp)
        _commit_file(tmp, "a.txt")
        out = REG.execute("git_log", {"cwd": tmp})
        assert "add a.txt" in out


def test_git_add_and_commit():
    with tempfile.TemporaryDirectory() as tmp:
        _init_repo(tmp)
        with open(os.path.join(tmp, "new.txt"), "w", encoding="utf-8") as f:
            f.write("x")
        out_add = REG.execute("git_add", {"path": "new.txt", "cwd": tmp})
        assert "Added: new.txt" in out_add
        out_commit = REG.execute("git_commit", {"message": "add new", "cwd": tmp})
        assert isinstance(out_commit, str)
        assert "add new" in REG.execute("git_log", {"cwd": tmp})


def test_git_branch_list_and_create():
    with tempfile.TemporaryDirectory() as tmp:
        _init_repo(tmp)
        _commit_file(tmp, "a.txt")
        REG.execute("git_branch", {"cwd": tmp})
        REG.execute("git_branch", {"name": "feature", "cwd": tmp})
        r = subprocess.run(
            ["git", "branch", "--list", "feature"],
            cwd=tmp,
            capture_output=True,
            text=True,
        )
        assert "feature" in r.stdout


def test_git_checkout():
    with tempfile.TemporaryDirectory() as tmp:
        _init_repo(tmp)
        _commit_file(tmp, "a.txt")
        REG.execute("git_branch", {"name": "dev", "cwd": tmp})
        REG.execute("git_checkout", {"branch": "dev", "cwd": tmp})
        cur = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=tmp,
            capture_output=True,
            text=True,
        )
        assert cur.stdout.strip() == "dev"


def test_get_git_tools_registry():
    names = {t.name for t in REG.list_tools()}
    expected = {
        "git_status",
        "git_diff",
        "git_log",
        "git_add",
        "git_commit",
        "git_branch",
        "git_checkout",
        "git_init",
    }
    assert expected <= names
