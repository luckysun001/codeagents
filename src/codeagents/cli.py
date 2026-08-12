#!/usr/bin/env python
"""CodeAgents CLI - 命令行入口"""

import argparse
import sys

from . import __version__


def main():
    """CLI 主入口"""
    parser = argparse.ArgumentParser(
        prog="codeagents",
        description="CodeAgents - 面向代码的轻量级多智能体框架",
    )
    parser.add_argument(
        "-V", "--version",
        action="version",
        version=f"codeagents {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # info 命令
    subparsers.add_parser("info", help="显示框架信息")

    # run 命令
    run_parser = subparsers.add_parser("run", help="运行单个 Agent")
    run_parser.add_argument(
        "prompt",
        type=str,
        help="Agent 执行提示词",
    )
    run_parser.add_argument(
        "--agent", "-a",
        type=str,
        default="code",
        choices=["code", "planning", "review"],
        help="Agent 类型 (默认: code)",
    )
    run_parser.add_argument(
        "--model", "-m",
        type=str,
        default="gpt-4o",
        help="LLM 模型名称 (默认: gpt-4o)",
    )
    run_parser.add_argument(
        "--provider", "-p",
        type=str,
        default="openai",
        choices=["openai", "anthropic"],
        help="LLM 提供商 (默认: openai)",
    )
    run_parser.add_argument(
        "--max-steps",
        type=int,
        default=10,
        help="最大执行步数 (默认: 10)",
    )

    args = parser.parse_args()

    if args.command == "info":
        _show_info()
    elif args.command == "run":
        _run_agent(args)
    else:
        parser.print_help()


def _show_info():
    """显示框架信息"""
    from . import __author__

    print(f"CodeAgents v{__version__}")
    print(f"Author: {__author__}")
    print()
    print("已实现的 Agent:")
    print("  - CodeAgent      代码生成、功能实现")
    print("  - PlanningAgent   任务拆分、步骤规划")
    print("  - ReviewAgent     代码审查、质量评估")
    print()
    print("工具系统:")
    print("  - 文件操作 (6 个工具)")
    print("  - 代码分析 (5 个工具)")
    print("  - Git 操作  (8 个工具)")
    print()
    print("编排模式:")
    print("  - 顺序 (SEQUENTIAL)")
    print("  - 并行 (PARALLEL)")
    print("  - 流水线 (PIPELINE)")
    print()
    print("使用 'codeagents run --help' 查看运行帮助")


def _run_agent(args):
    """运行单个 Agent"""
    import os

    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("错误: 请设置 OPENAI_API_KEY 或 ANTHROPIC_API_KEY 环境变量", file=sys.stderr)
        sys.exit(1)

    try:
        from . import (
            CodeAgent,
            PlanningAgent,
            ReviewAgent,
            get_llm,
            create_tool_registry,
        )

        # 初始化 LLM
        llm = get_llm(provider=args.provider, model=args.model)

        # 创建工具注册表
        tool_registry = create_tool_registry()

        # 选择 Agent
        agent_classes = {
            "code": CodeAgent,
            "planning": PlanningAgent,
            "review": ReviewAgent,
        }
        agent_class = agent_classes[args.agent]
        agent = agent_class(
            agent_id=f"{args.agent}-cli",
            name=f"{args.agent.title()} Agent",
            llm=llm,
            tool_registry=tool_registry,
            max_steps=args.max_steps,
        )

        print(f"运行 {args.agent} Agent (模型: {args.model})...")
        print(f"提示词: {args.prompt}")
        print("-" * 60)

        context = agent.run(args.prompt)

        print("-" * 60)
        print(f"状态: {context.status}")
        print(f"步数: {context.current_step}")

    except ImportError as e:
        print(f"导入错误: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"运行错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
