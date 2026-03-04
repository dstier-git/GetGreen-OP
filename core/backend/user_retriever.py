"""
user_retriever.py — Provides user-specific context for the AI agent.

CURRENT_USER_ID is hardcoded here. Swap this value to change the active user.
"""

import functools
import pandas as pd
from pathlib import Path

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
    - Prioritises actions whose category matches the user's completed-action
      categories, with sources-available entries ranked first.
    - Fills remaining slots with source-available actions from other categories.
    Each entry explicitly states its source URL or "No source available."
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
    pri1, pri2, pri3 = [], [], []  # cat+source, cat-only, other+source
    for aid, info in catalog.items():
        if aid in completed_ids:
            continue
        in_user_cat = info.get("category") in user_categories
        has_source = info.get("source") is not None
        if in_user_cat and has_source:
            pri1.append((aid, info))
        elif in_user_cat:
            pri2.append((aid, info))
        elif has_source:
            pri3.append((aid, info))

    # Roughly 60 % from user's categories, 40 % variety
    n_cat = min(round(n * 0.6), len(pri1) + len(pri2))
    n_other = n - n_cat
    from_cat = (pri1 + pri2)[:n_cat]
    from_other = pri3[:n_other]
    selected = (from_cat + from_other)[:n]

    if not selected:
        return "No suggested actions available."

    lines = [
        "Suggested actions for this user (not yet completed, ranked by relevance to their history):"
    ]
    for aid, info in selected:
        source = info.get("source")
        source_str = (
            f"Source: {source['title']} — {source['url']}"
            if source
            else "No source available."
        )
        lines.append(
            f"  • [{aid}] {info['action_name']}"
            f" | category: {info.get('category', 'General')}"
            f" | effort: {info.get('effort_level', 'Unknown')}"
            f" | {source_str}"
        )

    return "\n".join(lines)


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
