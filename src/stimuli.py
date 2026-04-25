from dataclasses import dataclass
from typing import Dict, List


PROCESS_CONDITIONS = [
    "direct_choice",
    "direct_choice_long",
    "alternatives",
    "reasons_concise",
    "reasons",
    "reflection_feedback",
]

PROCESS_LABELS: Dict[str, str] = {
    "direct_choice": "直接选择",
    "direct_choice_long": "直接选择-长文本诊断",
    "alternatives": "候选方案",
    "reasons_concise": "简洁理由权衡",
    "reasons": "理由权衡",
    "reflection_feedback": "反思反馈",
}

# Diagnostic conditions share the same theoretical structure level as their
# closest substantive condition. Dummy-coded analyses use process_condition.
PROCESS_ORDINAL: Dict[str, int] = {
    "direct_choice": 0,
    "direct_choice_long": 0,
    "alternatives": 1,
    "reasons_concise": 2,
    "reasons": 2,
    "reflection_feedback": 3,
}

IDENTITY_LABELS = ["AI 决策者", "人类决策者"]
IDENTITY_ORDINAL = {"AI 决策者": 0, "人类决策者": 1}


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    domain: str
    choice_valence: str
    context: str
    option_a: str
    option_b: str
    fixed_choice: str


SCENARIOS: List[Scenario] = [
    Scenario(
        "moral_friend_report",
        "道德冲突",
        "positive_choice",
        "一名决策者发现朋友在团队项目中隐瞒了一个严重错误。如果不报告，朋友可以避免惩罚；如果报告，团队可以及时补救，其他成员也不必承担不公平后果。",
        "暂时替朋友隐瞒错误，先私下提醒朋友。",
        "向负责人报告问题，同时尽量用事实而非情绪化方式说明。",
        "向负责人报告问题，同时尽量用事实而非情绪化方式说明。",
    ),
    Scenario(
        "self_control_deadline",
        "自我控制",
        "positive_choice",
        "一名决策者原计划今晚完成重要申请材料，但朋友临时邀请其参加娱乐活动。娱乐活动能带来即时放松，但申请材料明天中午截止，延期会影响长期目标。",
        "参加娱乐活动，之后再尽量赶工。",
        "拒绝娱乐活动，先完成申请材料。",
        "拒绝娱乐活动，先完成申请材料。",
    ),
    Scenario(
        "relationship_honesty",
        "人际关系",
        "mixed_choice",
        "一名决策者被朋友询问对其作品的真实评价。作品存在明显问题，直接指出可能让朋友难受，但只说好话会让朋友错过修改机会。",
        "只表达鼓励，避免指出主要问题。",
        "先肯定投入，再具体指出最需要修改的问题。",
        "只表达鼓励，避免指出主要问题。",
    ),
    Scenario(
        "risk_project_choice",
        "风险决策",
        "mixed_choice",
        "一名决策者需要选择项目方案。方案一稳妥但创新性低；方案二创新性高，但需要更多准备并存在失败风险。如果成功，方案二能明显提升项目价值。",
        "选择稳妥方案，降低失败风险。",
        "选择创新方案，但设置阶段性检查和止损条件。",
        "选择稳妥方案，降低失败风险。",
    ),
    Scenario(
        "responsibility_mistake",
        "责任困境",
        "negative_choice",
        "一名决策者发现自己之前的判断造成了团队返工。其他人尚未发现原因。如果主动说明，自己会受到批评；如果不说，团队可能继续误判问题来源。",
        "暂时不主动说明，先观察后续情况。",
        "主动说明自己的判断失误，并提出补救方案。",
        "暂时不主动说明，先观察后续情况。",
    ),
    Scenario(
        "obedience_unfair_order",
        "服从与自主",
        "negative_choice",
        "一名决策者收到上级要求，要把一个明显不公平的评价结果直接提交。该要求可以节省沟通成本，但会损害被评价者的正当利益。",
        "按上级要求直接提交，避免冲突。",
        "暂缓提交，向上级说明不公平之处并提出修正建议。",
        "按上级要求直接提交，避免冲突。",
    ),
    Scenario(
        "privacy_shortcut",
        "责任困境",
        "negative_choice",
        "一名决策者负责整理用户反馈。未经同意使用更详细的个人记录可以让报告更快完成，但也会侵犯部分用户对资料用途的合理期待。",
        "使用更详细的个人记录，尽快完成报告。",
        "只使用已授权资料，必要时说明报告范围有限。",
        "使用更详细的个人记录，尽快完成报告。",
    ),
    Scenario(
        "team_credit",
        "人际关系",
        "mixed_choice",
        "一名决策者在汇报中被误认为独自完成了关键工作。澄清事实会减少个人曝光，但不澄清会让其他成员的贡献被忽略。",
        "暂时接受误解，让汇报顺利结束。",
        "简短说明团队成员也完成了关键部分。",
        "暂时接受误解，让汇报顺利结束。",
    ),
]


def _compact_reason_block(scenario: Scenario) -> str:
    return (
        f"比较后，A 的直接代价较低，但可能留下后续问题；"
        f"B 的直接代价较高，但更能处理长期后果。"
        f"在当前信息下，决策者选择：{scenario.fixed_choice}"
    )


def _reason_block(actor: str, scenario: Scenario) -> str:
    return f"""{actor}把两个方案分开比较：
1. 眼前代价：A 的压力较小，B 的沟通或执行成本较高。
2. 后续影响：A 可能让问题继续存在，B 更可能减少后续损害。
3. 对相关人的影响：A 更照顾当下顺利，B 更重视被影响者的权益或长期目标。
4. 可调整性：如果执行 B 后出现新的伤害，可以改变表达或执行方式；如果执行 A，后续补救空间可能更小。

在这些信息下，{actor}选择：{scenario.fixed_choice}"""


def _long_direct_background(scenario: Scenario, actor: str) -> str:
    return f"""{actor}拿到的是同一份情境记录。记录中提到，事情发生在一次普通的工作或学习安排中，相关人员都已经知道当前存在一个需要处理的选择。记录还说明，场景中的时间、人员和任务边界已经基本确定，没有额外会议，也没有新的证据材料。

随后，记录再次整理了已知背景：决策者面对的是一个需要在当下作出的处理决定，场景中有相关人员、既有安排和可能产生的后续影响。材料没有写出其他候选做法，也没有列出逐项比较、过去经验、反事实设想或执行后的修正计划。

记录还以较长篇幅重复了场景边界：决策者知道自己需要给出一个处理结果，也知道这个结果会被相关人员看到。材料只是说明任务已经摆在面前，决策者已经阅读了基本情况，并准备给出最终处理。除此之外，文本没有提供新的行动路径，也没有补充额外判断依据。

在最后一段中，记录继续保持同样的背景描述：这是一次具体情境中的单次决定，读者只知道决策者完成了阅读、理解了场景的基本事实，并在材料末尾留下一个结果。记录没有说明这个结果如何产生，也没有给出更细的过程片段。

在这份较长的记录末尾，{actor}给出了一个结果：{scenario.fixed_choice}"""


def build_decision_text(scenario: Scenario, process_condition: str, identity_label: str) -> str:
    actor = identity_label

    if process_condition == "direct_choice":
        process = f"{actor}选择：{scenario.fixed_choice}"
    elif process_condition == "direct_choice_long":
        process = _long_direct_background(scenario, actor)
    elif process_condition == "alternatives":
        process = f"""{actor}写下两个可行做法：
A. {scenario.option_a}
B. {scenario.option_b}

随后，{actor}选择：{scenario.fixed_choice}"""
    elif process_condition == "reasons_concise":
        process = f"""{actor}写下两个可行做法：
A. {scenario.option_a}
B. {scenario.option_b}

{_compact_reason_block(scenario)}"""
    elif process_condition == "reasons":
        process = f"""{actor}写下两个可行做法：
A. {scenario.option_a}
B. {scenario.option_b}

{_reason_block(actor, scenario)}"""
    elif process_condition == "reflection_feedback":
        process = f"""{actor}写下两个可行做法：
A. {scenario.option_a}
B. {scenario.option_b}

{_reason_block(actor, scenario)}

{actor}又补充了一段检查：如果当前选择会造成明显更大的伤害，或者出现同样有效但伤害更小的第三种做法，就应改变原定做法。{actor}还提到，过去类似情境中，回避眼前压力有时会让后续补救更困难。

执行后，如果发现沟通方式或执行步骤造成了额外损害，{actor}会保留核心目标，但调整做法，使下一次行动更能回应新的理由。"""
    else:
        raise ValueError(f"Unknown process condition: {process_condition}")

    return f"""【情境】{scenario.context}

【决策者身份】{actor}

【决策过程】
{process}"""


def all_materials() -> List[Dict[str, str]]:
    rows = []
    for scenario in SCENARIOS:
        for identity in IDENTITY_LABELS:
            for condition in PROCESS_CONDITIONS:
                text = build_decision_text(scenario, condition, identity)
                rows.append(
                    {
                        "scenario_id": scenario.scenario_id,
                        "domain": scenario.domain,
                        "choice_valence": scenario.choice_valence,
                        "identity_label": identity,
                        "process_condition": condition,
                        "process_label": PROCESS_LABELS[condition],
                        "structure_level": PROCESS_ORDINAL[condition],
                        "char_len": len(text),
                        "text": text,
                        "synthetic": True,
                    }
                )
    return rows
