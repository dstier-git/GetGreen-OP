from typing import Dict


def build_welcome_instruction(summary: Dict[str, str]) -> str:
    top_category = summary.get("top_category", "everyday sustainability")
    top_action_name = summary.get("top_action_name", "small daily eco-actions")
    interest_suggestion = summary.get("interest_suggestion", "a simple low-effort action this week")
    recent_style_hint = summary.get("recent_style_hint", "practical steps")

    return (
        "Write a single friendly welcome message for first app load.\n"
        "Hard requirements:\n"
        "1) 2-4 sentences only.\n"
        "2) Start with: 'Hi John — I’m GiGi'.\n"
        "3) Include one statement in the form 'I can see you’ve been doing ...'.\n"
        "4) Include one statement in the form 'You seem to like ...'.\n"
        "5) Include one statement in the form 'You might be interested in ...'.\n"
        "6) No bullet points, no labels, no IDs, no internal data terms.\n"
        "7) Keep tone warm, concise, and personable.\n\n"
        f"User pattern context: top category = {top_category}; top completed action style = {top_action_name}; "
        f"recent style hint = {recent_style_hint}; likely-interest suggestion = {interest_suggestion}."
    )


def build_welcome_fallback_text(summary: Dict[str, str]) -> str:
    top_category = summary.get("top_category", "everyday sustainability")
    top_action_name = summary.get("top_action_name", "small daily eco-actions")
    interest_suggestion = summary.get("interest_suggestion", "a simple low-effort action this week")

    return (
        f"Hi John — I’m GiGi, your personal sustainability assistant. "
        f"I can see you’ve been doing great work around {top_category}, especially with actions like {top_action_name}. "
        f"You seem to like practical, realistic improvements, and you might be interested in trying {interest_suggestion} next."
    )
