"""CLI 入口测试

`cli.main()` 无参数、直接解析 sys.argv，因此通过 monkeypatch 设置 sys.argv。
`run` 命令通过 monkeypatch 包级属性（CodeAgent/PlanningAgent/ReviewAgent/
get_llm/create_tool_registry）让其在无真实 LLM 与 API Key 下跑通；
同时覆盖 缺 Key 退出、--version、info、help 等分支。
"""

import sys
from unittest.mock import patch

import pytest

import codeagents
from codeagents import cli


class _FakeContext:
    def __init__(self):
        self.status = "finished"
        self.current_step = 3


class _FakeAgent:
    def __init__(self, *args, **kwargs):
        pass

    def run(self, prompt):
        return _FakeContext()


def _set_argv(monkeypatch, args):
    monkeypatch.setattr(sys, "argv", ["codeagents"] + args)


def test_cli_info(monkeypatch, capsys):
    _set_argv(monkeypatch, ["info"])
    cli.main()
    out = capsys.readouterr().out
    assert "CodeAgents" in out
    assert "CodeAgent" in out


def test_cli_help(monkeypatch, capsys):
    _set_argv(monkeypatch, [])
    cli.main()
    out = capsys.readouterr().out
    assert "codeagents" in out


def test_cli_version(monkeypatch):
    _set_argv(monkeypatch, ["--version"])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 0


def test_cli_run_missing_api_key(monkeypatch, capsys):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    _set_argv(monkeypatch, ["run", "do something"])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "OPENAI_API_KEY" in err or "ANTHROPIC_API_KEY" in err


def test_cli_run_with_fakes(monkeypatch, capsys):
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-key")
    _set_argv(monkeypatch, ["run", "my prompt", "--agent", "code", "--model", "gpt-4o"])
    with (
        patch.object(codeagents, "CodeAgent", _FakeAgent),
        patch.object(codeagents, "PlanningAgent", _FakeAgent),
        patch.object(codeagents, "ReviewAgent", _FakeAgent),
        patch.object(codeagents, "get_llm", lambda *a, **k: object()),
        patch.object(codeagents, "create_tool_registry", lambda *a, **k: object()),
    ):
        cli.main()
    out = capsys.readouterr().out
    assert "my prompt" in out
    assert "finished" in out
    assert "3" in out


def test_cli_run_import_error(monkeypatch, capsys):
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-key")
    _set_argv(monkeypatch, ["run", "x"])
    with patch.object(codeagents, "get_llm", side_effect=ImportError("boom")), pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 1
    assert "导入错误" in capsys.readouterr().err


def test_cli_run_generic_exception(monkeypatch, capsys):
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-key")
    _set_argv(monkeypatch, ["run", "x"])
    with patch.object(codeagents, "get_llm", side_effect=RuntimeError("boom")), pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 1
    assert "运行错误" in capsys.readouterr().err


def test_cli_run_planning_agent(monkeypatch, capsys):
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-key")
    calls = {}

    class _FakePlanning(_FakeAgent):
        def run(self, prompt):
            calls["prompt"] = prompt
            return _FakeContext()

    _set_argv(monkeypatch, ["run", "plan it", "--agent", "planning"])
    with (
        patch.object(codeagents, "CodeAgent", _FakePlanning),
        patch.object(codeagents, "PlanningAgent", _FakePlanning),
        patch.object(codeagents, "ReviewAgent", _FakePlanning),
        patch.object(codeagents, "get_llm", lambda *a, **k: object()),
        patch.object(codeagents, "create_tool_registry", lambda *a, **k: object()),
    ):
        cli.main()
    assert calls.get("prompt") == "plan it"
