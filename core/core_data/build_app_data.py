"""One-off: build articles.csv and user_stats.csv from moved CSVs. Run from repo root: python core/core_data/build_app_data.py"""
import pandas as pd
from pathlib import Path

CORE_DATA = Path(__file__).resolve().parent

# articles.csv: vector_retriever needs Title + scraped_text
ext = pd.read_csv(CORE_DATA / "External-Links-Basic.csv")
ext["scraped_text"] = ext.get("URL", "")
ext[["Title", "scraped_text"]].to_csv(CORE_DATA / "articles.csv", index=False)
print("Created articles.csv with", len(ext), "rows")

# user_stats.csv: data_retriever needs user_id; get_columns wants most_frequent_category, most_frequent_action, action_name, leaf_value
df = pd.read_csv(CORE_DATA / "Data-Sample.csv")
if "scrambled_id" in df.columns:
    df = df.rename(columns={"scrambled_id": "user_id"})
col_map = {}
for c in df.columns:
    if c == "properties.action_name":
        col_map[c] = "action_name"
    elif c == "properties.leaf_value":
        col_map[c] = "leaf_value"
    elif c == "properties.category":
        col_map[c] = "most_frequent_category"
df = df.rename(columns=col_map)
for col in ["most_frequent_category", "most_frequent_action", "action_name", "leaf_value"]:
    if col not in df.columns:
        df[col] = ""
df.to_csv(CORE_DATA / "user_stats.csv", index=False)
print("Created user_stats.csv with", len(df), "rows")
