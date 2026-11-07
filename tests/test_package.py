"""包级公共 API 测试

覆盖 create_tool_registry 工厂函数：默认包含全部工具、include 过滤。
"""

from codeagents import create_tool_registry

FILE_TOOLS = {
    "read_file",
    "write_file",
    "list_dir",
    "file_exists",
    "search_files",
    "grep_file",
}
CODE_TOOLS = {
    "execute_python",
    "execute_command",
    "run_pytest",
    "check_pep8",
    "check_type_hints",
}
GIT_TOOLS = {
    "git_status",
    "git_diff",
    "git_log",
    "git_add",
    "git_commit",
    "git_branch",
    "git_checkout",
    "git_init",
}


def test_create_tool_registry_all():
    reg = create_tool_registry()
    names = {t.name for t in reg.list_tools()}
    assert names >= FILE_TOOLS | CODE_TOOLS | GIT_TOOLS
    # 6 + 5 + 8 = 19
    assert len(names) == 19


def test_create_tool_registry_include_filter():
    reg = create_tool_registry(include=["file"])
    names = {t.name for t in reg.list_tools()}
    assert names == FILE_TOOLS

    reg2 = create_tool_registry(include=["code", "git"])
    names2 = {t.name for t in reg2.list_tools()}
    assert names2 == (CODE_TOOLS | GIT_TOOLS)
