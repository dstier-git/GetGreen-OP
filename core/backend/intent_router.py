import re
from typing import Dict


_INTENT_PATTERNS: Dict[str, list[str]] = {
    "compare": [
        r"\b(vs|versus|compare|better than|which is better)\b",
    ],
    "weekly_plan": [
        r"\b(weekly|week plan|meal plan|plan for (the )?week|planner)\b",
    ],
    "impact_explain": [
        r"\b(impact|difference|save|help the planet|how much)\b",
    ],
    "recommend": [
        r"\b(recommend|suggest|ideas|what should i do|next steps)\b",
    ],
    "recycle_text": [
        r"\b(recycle|recyclable|compost|trash|waste bin)\b",
    ],
}


def classify_intent(message: str) -> str:
    if not message:
        return "general_qa"

    text = message.lower()
    scores: Dict[str, int] = {name: 0 for name in _INTENT_PATTERNS}
    for intent, patterns in _INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text):
                scores[intent] += 1

    best_intent = max(scores, key=scores.get)
    best_score = scores.get(best_intent, 0)
    if best_score <= 0:
        return "general_qa"

    winners = [intent for intent, score in scores.items() if score == best_score]
    if len(winners) > 1:
        return "general_qa"
    return best_intent
