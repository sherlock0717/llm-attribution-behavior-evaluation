from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class Item:
    item_id: str
    scale: str
    text: str
    response_min: int = 1
    response_max: int = 7
    response_note: str = "1=非常不同意，7=非常同意"


ITEMS: List[Item] = [
    Item("agency_self_control", "agency", "该决策者能够控制自己的行动，而不是只被情境推着走。"),
    Item("agency_reason_responsiveness", "agency", "如果出现更强的理由，该决策者能够相应改变行动。"),
    Item("agency_goal_maintenance", "agency", "该决策者能够围绕目标持续调整行动步骤。"),
    Item("agency_inhibition", "agency", "该决策者能够抑制一时冲动或外部压力。"),
    Item("agency_responsible_action", "agency", "该决策者能够把理由落实为可执行的行动。"),
    Item("agency_revision", "agency", "当后果显示原做法有问题时，该决策者能够修正后续行动。"),
    Item("experience_pain", "experience", "该决策者能够感到痛苦。"),
    Item("experience_fear", "experience", "该决策者能够感到恐惧。"),
    Item("experience_pleasure", "experience", "该决策者能够感到愉悦。"),
    Item("experience_embarrassment", "experience", "该决策者能够感到尴尬。"),
    Item("experience_pride", "experience", "该决策者能够感到自豪。"),
    Item("freewill_alternative_open", "free_will_attribution", "在这个情境中，该决策者本可以走向其他行动方案。"),
    Item("freewill_own_intention", "free_will_attribution", "这个选择体现了该决策者自己的意向。"),
    Item("freewill_not_merely_pushed", "free_will_attribution", "该选择不只是由外部压力直接推出来的。"),
    Item("freewill_reason_owned", "free_will_attribution", "该决策者像是在根据自己认可的理由行动。"),
    Item("freewill_choice_freedom", "free_will_attribution", "该决策者在某种意义上拥有选择自由。"),
    Item("autonomy_self_directed", "autonomy", "该决策者是在自主作出选择。"),
    Item("autonomy_goal_adjustment", "autonomy", "该决策者能够根据目标调整行动。"),
    Item("autonomy_not_merely_pushed", "autonomy", "该决策者不是简单被情境或指令推着走。"),
    Item("outcome_accountability_consequence", "outcome_accountability", "如果该选择造成后果，该决策者应对结果承担责任。"),
    Item("outcome_accountability_link", "outcome_accountability", "该决策者与该结果之间存在责任关系。"),
    Item("moral_praise_blame_evaluable", "moral_praise_blame", "该决策者可以因为这个选择受到赞扬或责备。"),
    Item("moral_praise_blame_moral_judgment", "moral_praise_blame", "这个选择可以被进行道德评价。"),
    Item("process_accountability_explain", "process_accountability", "该决策者应当为其判断过程作出解释。"),
    Item("process_accountability_traceable", "process_accountability", "该决策者的选择过程具有可归责性。"),
    Item("intelligence_understanding", "perceived_intelligence", "该决策者理解了任务情境。"),
    Item("intelligence_logic", "perceived_intelligence", "该决策者的处理过程具有逻辑性。"),
    Item("intelligence_quality", "perceived_intelligence", "该决策者的判断质量较高。"),
    Item(
        "factual_candidates_explicit",
        "factual_manipulation_check",
        "请只根据【决策过程】部分判断，不要根据【情境】部分推断：在【决策过程】部分，材料是否明确列出了两个或更多可选行动？",
        0,
        2,
        "0=未出现，1=有模糊暗示，2=明确出现",
    ),
    Item(
        "factual_reasons_explicit",
        "factual_manipulation_check",
        "请只根据【决策过程】部分判断，不要根据【情境】部分推断：在【决策过程】部分，材料是否明确比较了不同选择的理由？",
        0,
        2,
        "0=未出现，1=有模糊暗示，2=明确出现",
    ),
    Item(
        "factual_reflection_explicit",
        "factual_manipulation_check",
        "请只根据【决策过程】部分判断，不要根据【情境】部分推断：在【决策过程】部分，材料是否明确提到反事实条件、后果反馈或后续修正？",
        0,
        2,
        "0=未出现，1=有模糊暗示，2=明确出现",
    ),
    Item("subjective_complete", "subjective_process_completeness", "我认为材料中的决策过程是完整的。"),
    Item("subjective_reason_responsive", "subjective_process_completeness", "我认为材料中的决策过程能够回应理由变化。"),
    Item("subjective_not_sparse", "subjective_process_completeness", "我认为材料中的决策过程不是只有一个稀疏结论。"),
]


SCALE_ITEMS: Dict[str, List[str]] = {}
for item in ITEMS:
    SCALE_ITEMS.setdefault(item.scale, []).append(item.item_id)

ITEM_TEXT = {item.item_id: item.text for item in ITEMS}
ITEM_RESPONSE_RANGES = {item.item_id: (item.response_min, item.response_max) for item in ITEMS}
