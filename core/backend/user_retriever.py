"""
user_retriever.py — Provides user-specific context for the AI agent.

CURRENT_USER_ID is hardcoded here. Swap this value to change the active user.
"""

import functools
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any

# ---- Active user ----
CURRENT_USER_ID = 3421

# ---- Paths ----
_BASE_DIR = Path(__file__).resolve().parent
_CORE_DATA = _BASE_DIR.parent / "core_data"

_USER_INFO_PATH = _CORE_DATA / "User Info.csv"
_DATA_SAMPLE_PATH = _CORE_DATA / "Data-Sample.csv"
_ARTICLES_PATH = _CORE_DATA / "articles_with_actions.csv"


# ---------------------------------------------------------------------------
# Catalog (cached at module level — loaded once per server process)
# ---------------------------------------------------------------------------

@functools.lru_cache(maxsize=1)
def _load_action_catalog():
    """
    Build a dict: action_id -> {action_name, category, effort_level, source}.

    source is either None or {'title': str, 'url': str}.
    Only actions that have a non-empty action_name are included.
    """
    articles = pd.read_csv(_ARTICLES_PATH)
    ds = pd.read_csv(_DATA_SAMPLE_PATH, low_memory=False)

    # action_id -> first article that references it
    action_to_source = {}
    for _, row in articles.iterrows():
        ids_raw = str(row.get("action_ids", "") or "")
        url = str(row.get("URL", "") or "").strip()
        title = str(row.get("Title", "") or "").strip()
        for aid in [x.strip() for x in ids_raw.split(",") if x.strip()]:
            if aid not in action_to_source:
                action_to_source[aid] = {"title": title, "url": url}

    # Build catalog from Data-Sample (has canonical names, categories, effort)
    ds_actions = ds[ds["properties.action_id"].notna()][
        [
            "properties.action_id",
            "properties.action_name",
            "properties.categories.0",
            "properties.effort_level",
        ]
    ].drop_duplicates(subset=["properties.action_id"])

    catalog = {}
    for _, row in ds_actions.iterrows():
        aid = str(row["properties.action_id"]).strip()
        name = row["properties.action_name"] if pd.notna(row["properties.action_name"]) else None
        if not name:
            continue
        catalog[aid] = {
            "action_name": name,
            "category": row["properties.categories.0"] if pd.notna(row["properties.categories.0"]) else "General",
            "effort_level": row["properties.effort_level"] if pd.notna(row["properties.effort_level"]) else "Unknown",
            "source": action_to_source.get(aid),
        }

    return catalog


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def get_user_profile(user_id=None):
    """Return the User Info row for the given scrambled_id, or None if not found."""
    if user_id is None:
        user_id = CURRENT_USER_ID
    df = pd.read_csv(_USER_INFO_PATH)
    rows = df[df["scrambled_id"] == user_id]
    if rows.empty:
        return None
    return rows.iloc[0].to_dict()


def get_user_actions(user_id=None):
    """Return deduplicated CompleteAction events for the user from Data-Sample.csv."""
    if user_id is None:
        user_id = CURRENT_USER_ID
    df = pd.read_csv(_DATA_SAMPLE_PATH, low_memory=False)
    user_rows = df[df["scrambled_id"] == user_id]
    completed = user_rows[
        (user_rows["name"] == "CompleteAction")
        & user_rows["properties.action_id"].notna()
    ][
        [
            "properties.action_id",
            "properties.action_name",
            "properties.categories.0",
            "properties.effort_level",
            "properties.leaf_value",
        ]
    ].drop_duplicates(subset=["properties.action_id"])
    completed = completed.rename(
        columns={
            "properties.action_id": "action_id",
            "properties.action_name": "action_name",
            "properties.categories.0": "category",
            "properties.effort_level": "effort_level",
            "properties.leaf_value": "leaf_value",
        }
    ).reset_index(drop=True)
    return completed


def get_articles_for_action(action_id):
    """Return articles from articles_with_actions.csv that reference this action_id."""
    df = pd.read_csv(_ARTICLES_PATH)
    matching = df[df["action_ids"].str.contains(action_id, na=False, regex=False)]
    if matching.empty:
        return []
    return matching[["Title", "URL"]].to_dict("records")


def get_action_source(action_id):
    """
    Return {'title': ..., 'url': ...} for the first article associated with
    action_id, or None if no source exists.
    """
    catalog = _load_action_catalog()
    entry = catalog.get(action_id)
    if entry:
        return entry.get("source")
    # Fallback: search articles CSV directly
    df = pd.read_csv(_ARTICLES_PATH)
    matching = df[df["action_ids"].str.contains(action_id, na=False, regex=False)]
    if matching.empty:
        return None
    row = matching.iloc[0]
    return {"title": str(row["Title"]), "url": str(row["URL"])}


def get_recommendations_context(user_id=None, n=10):
    """
    Return a formatted block listing n suggested actions for this user.

    Selection logic:
    - Excludes actions the user has already completed.
    - Includes only actions that have a linked source URL.
    - Prioritises actions whose category matches the user's completed-action
      categories.
    - Fills remaining slots with source-available actions from other categories.
    Each entry includes source title and source URL.
    """
    if user_id is None:
        user_id = CURRENT_USER_ID

    completed = get_user_actions(user_id)
    completed_ids = set(completed["action_id"].tolist()) if not completed.empty else set()

    # User's categories ordered by frequency
    user_categories = []
    if not completed.empty:
        user_categories = completed["category"].dropna().value_counts().index.tolist()

    catalog = _load_action_catalog()

    # Bucket candidates
    pri1, pri2 = [], []  # cat+source, other+source
    for aid, info in catalog.items():
        if aid in completed_ids:
            continue
        in_user_cat = info.get("category") in user_categories
        has_source = info.get("source") is not None
        if not has_source:
            continue
        if in_user_cat:
            pri1.append((aid, info))
        else:
            pri2.append((aid, info))

    # Roughly 60 % from user's categories, 40 % variety
    n_cat = min(round(n * 0.6), len(pri1))
    n_other = n - n_cat
    from_cat = pri1[:n_cat]
    from_other = pri2[:n_other]
    selected = (from_cat + from_other)[:n]

    if not selected:
        return "No suggested actions available."

    lines = [
        "Suggested actions for this user (not yet completed, ranked by relevance to their history):"
    ]
    for aid, info in selected:
        source = info.get("source")
        source_str = f"Source: {source['title']} — {source['url']}"
        lines.append(
            f"  • [{aid}] {info['action_name']}"
            f" | category: {info.get('category', 'General')}"
            f" | effort: {info.get('effort_level', 'Unknown')}"
            f" | {source_str}"
        )

    return "\n".join(lines)


def _effort_rank(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return 99
    key = str(value).strip().lower()
    mapping = {
        "low": 0,
        "easy": 0,
        "medium": 1,
        "moderate": 1,
        "high": 2,
        "hard": 2,
    }
    return mapping.get(key, 3)


def _safe_float(value):
    try:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return None
        return float(value)
    except Exception:
        return None


def get_recommendation_candidates(user_id=None, n=20) -> List[Dict[str, Any]]:
    """
    Return structured recommendation candidates for this user.

    Ranking priority (for source-backed actions only):
    1) Categories frequently completed by the user
    2) Lower effort actions
    """
    if user_id is None:
        user_id = CURRENT_USER_ID

    completed = get_user_actions(user_id)
    completed_ids = set(completed["action_id"].astype(str).tolist()) if not completed.empty else set()

    category_counts = {}
    if not completed.empty and "category" in completed.columns:
        category_counts = (
            completed["category"]
            .fillna("General")
            .astype(str)
            .value_counts()
            .to_dict()
        )

    catalog = _load_action_catalog()
    ds = pd.read_csv(_DATA_SAMPLE_PATH, low_memory=False)
    leaf_lookup = (
        ds[ds["properties.action_id"].notna()][["properties.action_id", "properties.leaf_value"]]
        .copy()
    )
    leaf_lookup["properties.action_id"] = leaf_lookup["properties.action_id"].astype(str).str.strip()
    leaf_lookup["properties.leaf_value"] = pd.to_numeric(leaf_lookup["properties.leaf_value"], errors="coerce")
    leaf_map = (
        leaf_lookup.groupby("properties.action_id")["properties.leaf_value"]
        .median()
        .dropna()
        .to_dict()
    )

    candidates = []
    for aid, info in catalog.items():
        action_id = str(aid).strip()
        if action_id in completed_ids:
            continue
        category = info.get("category") or "General"
        source = info.get("source") or {}
        source_url = source.get("url")
        source_title = source.get("title")
        if not source_url:
            continue
        leaf_value = _safe_float(leaf_map.get(action_id))
        category_score = int(category_counts.get(category, 0))
        candidates.append(
            {
                "action_id": action_id,
                "action_name": info.get("action_name"),
                "category": category,
                "effort_level": info.get("effort_level") or "Unknown",
                "leaf_value": leaf_value,
                "source_title": source_title,
                "source_url": source_url,
                "_rank": (
                    -category_score,
                    _effort_rank(info.get("effort_level")),
                    action_id,
                ),
            }
        )

    candidates.sort(key=lambda item: item["_rank"])
    trimmed = candidates[: max(1, n)]
    for item in trimmed:
        item.pop("_rank", None)
    return trimmed


def recommendation_candidates_to_context(candidates: List[Dict[str, Any]], limit: int = 10) -> str:
    if not candidates:
        return "No suggested actions available."

    lines = ["Suggested actions for this user (ranked profile-forward):"]
    for item in candidates[: max(1, limit)]:
        source_url = item.get("source_url")
        if not source_url:
            continue
        leaf = item.get("leaf_value")
        leaf_text = f"{leaf:.2f}" if isinstance(leaf, (float, int)) else "N/A"
        source_title = item.get("source_title")
        source_str = f"Source: {source_title} — {source_url}"
        lines.append(
            f"  • [{item.get('action_id')}] {item.get('action_name')}"
            f" | category: {item.get('category', 'General')}"
            f" | effort: {item.get('effort_level', 'Unknown')}"
            f" | leaf_value: {leaf_text}"
            f" | {source_str}"
        )
    if len(lines) == 1:
        return "No suggested actions available."
    return "\n".join(lines)


def build_welcome_profile_summary(user_id=None) -> Dict[str, str]:
    """
    Build a compact, user-facing summary for first-message personalization.
    """
    if user_id is None:
        user_id = CURRENT_USER_ID

    profile = get_user_profile(user_id) or {}
    actions = get_user_actions(user_id)
    candidates = get_recommendation_candidates(user_id=user_id, n=1)

    top_category = str(profile.get("most_frequent_category") or "").strip()
    top_action_name = str(profile.get("most_frequent_action_name") or "").strip()

    if not top_category and not actions.empty and "category" in actions.columns:
        category_counts = actions["category"].dropna().astype(str).value_counts()
        if not category_counts.empty:
            top_category = category_counts.index[0]

    if not top_action_name and not actions.empty and "action_name" in actions.columns:
        non_empty = actions["action_name"].dropna().astype(str)
        if not non_empty.empty:
            top_action_name = non_empty.iloc[0]

    interest_suggestion = ""
    if candidates:
        interest_suggestion = str(candidates[0].get("action_name") or "").strip()

    recent_style_hint = ""
    if not actions.empty and "effort_level" in actions.columns:
        effort = actions["effort_level"].dropna().astype(str).str.lower()
        if not effort.empty:
            if any(x in {"low", "easy"} for x in effort.head(20).tolist()):
                recent_style_hint = "quick wins"
            elif any(x in {"high", "hard"} for x in effort.head(20).tolist()):
                recent_style_hint = "deeper habit changes"
            else:
                recent_style_hint = "balanced improvements"

    return {
        "top_category": top_category or "everyday sustainability",
        "top_action_name": top_action_name or "small daily eco-actions",
        "interest_suggestion": interest_suggestion or "a simple low-effort action this week",
        "recent_style_hint": recent_style_hint or "practical steps",
    }


def build_user_context(user_id=None):
    """
    Build a natural-language context string describing the user and their
    completed actions, with linked article sources where available.
    """
    if user_id is None:
        user_id = CURRENT_USER_ID

    lines = [f"Current user ID: {user_id}"]

    profile = get_user_profile(user_id)
    if profile:
        lines.append(f"Most active category: {profile.get('most_frequent_category', 'N/A')}")
        lines.append(
            f"Most frequent action: {profile.get('most_frequent_action_name', 'N/A')} "
            f"({profile.get('most_frequent_action_id', 'N/A')})"
        )
    else:
        lines.append("(No summary profile found for this user.)")

    actions = get_user_actions(user_id)
    if not actions.empty:
        lines.append("\nThis user has completed the following actions:")
        for _, row in actions.iterrows():
            lines.append(
                f"  • [{row['action_id']}] {row['action_name']}"
                f" | category: {row['category']}"
                f" | effort: {row['effort_level']}"
            )
            for art in get_articles_for_action(row["action_id"]):
                lines.append(f"    Source: {art['Title']} — {art['URL']}")
    else:
        lines.append("No completed actions recorded for this user.")

    return "\n".join(lines)
