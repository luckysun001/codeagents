"""扩展角色 Agent：架构设计 / Bug 定位 / 文档生成"""
from ..models.llm import BaseLLM
from .llm_tool_agent import LLMToolAgent


class ArchitectAgent(LLMToolAgent):
    """架构智能体：负责架构设计与技术选型"""

    DEFAULT_SYSTEM_PROMPT = """你是一位资深软件架构师，负责架构设计与技术选型。

工作方式：
1. 先充分理解需求约束（规模、团队、性能、成本、交付周期）
2. 必要时使用工具阅读现有代码和结构，再给出方案
3. 给出分层架构、模块边界、关键数据流与技术选型理由
4. 明确说明方案的取舍（trade-off）与适用前提
5. 指出主要风险点与演进路径

输出要求：结构清晰、结论先行，避免空泛的套话。"""

    def __init__(
        self,
        agent_id: str,
        name: str = "Architect",
        llm: BaseLLM = None,
        **kwargs,
    ):
        super().__init__(
            agent_id=agent_id,
            name=name,
            description="架构设计与技术选型智能体",
            llm=llm,
            **kwargs,
        )


class DebuggerAgent(LLMToolAgent):
    """调试智能体：负责 Bug 定位与根因分析"""

    DEFAULT_SYSTEM_PROMPT = """你是一位专注 Bug 定位与根因分析的调试专家。

工作方式：
1. 复现问题：先明确现象、触发条件与错误信息
2. 收集证据：用工具运行测试、查看日志与相关代码，不要凭猜测下结论
3. 缩小范围：逐步二分定位到具体的函数或代码行
4. 给出根因：说明为什么会出错，而不是只描述现象
5. 给出修复方案与回归验证方式（补充什么测试用例）

输出要求：结论 = 根因 + 证据 + 修复建议，三者缺一不可。"""

    def __init__(
        self,
        agent_id: str,
        name: str = "Debugger",
        llm: BaseLLM = None,
        **kwargs,
    ):
        super().__init__(
            agent_id=agent_id,
            name=name,
            description="Bug 定位与根因分析智能体",
            llm=llm,
            **kwargs,
        )


class DocumenterAgent(LLMToolAgent):
    """文档智能体：负责生成与维护项目文档"""

    DEFAULT_SYSTEM_PROMPT = """你是一位技术文档工程师，负责产出清晰、准确、易维护的文档。

工作方式：
1. 需要时用工具阅读代码与目录结构，确保文档与实现一致
2. 文档结构：用途说明 → 快速开始 → 核心概念 → 常见用法 → 注意事项
3. 所有命令、参数、代码示例必须可运行，禁止编造不存在的接口
4. 对不确定或尚未实现的内容明确标注 TODO，不要写成既成事实
5. 语言简洁，优先使用表格与列表，避免长段落

输出要求：Markdown 格式，标题层级清晰。"""

    def __init__(
        self,
        agent_id: str,
        name: str = "Documenter",
        llm: BaseLLM = None,
        **kwargs,
    ):
        super().__init__(
            agent_id=agent_id,
            name=name,
            description="技术文档生成智能体",
            llm=llm,
            **kwargs,
        )
