from typing import List, Dict, Any, Optional


def _truncate_words(text: str, max_words: int = 140) -> str:
    tokens = text.split()
    if len(tokens) <= max_words:
        return text.strip()
    return " ".join(tokens[:max_words]).strip() + "…"


def format_compact_response(
    direct_answer: str,
    recommendations: Optional[List[Dict[str, Any]]] = None,
    article_note: Optional[str] = None,
    truncate_direct_answer: bool = True,
    cta_text: Optional[str] = "If you want, we can pick one easy next step together.",
    ask_follow_up: bool = False,
) -> str:
    lines = []
    base = (direct_answer or "").strip() or "Great question — here’s the most practical next step for you."
    lines.append(_truncate_words(base, max_words=45) if truncate_direct_answer else base)

    if recommendations:
        lines.append("")
        lines.append("Recommended actions:")
        for idx, rec in enumerate(recommendations[:2], start=1):
            source_title = (rec.get("source_title") or "Article").strip()
            source_url = (rec.get("source_url") or "").strip()
            source_suffix = f" | article: {source_title} — {source_url}" if source_url else ""
            lines.append(
                f"{idx}) {rec.get('action_name')} ({rec.get('category', 'General')}, effort: {rec.get('effort_level', 'Unknown')}){source_suffix}"
            )

    if article_note:
        lines.append("")
        lines.append(article_note.strip())

    if cta_text:
        lines.append("")
        lines.append(cta_text.strip())

    if ask_follow_up:
        lines.append("")
        lines.append("Want two more options in the same category?")

    return "\n".join(lines).strip()
