import pandas as pd
import sqlite3
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent
_CORE_DATA = _BASE_DIR.parent / "core_data"
csv_file = str(_CORE_DATA / "data_with_stats-copy.csv")
db_file = str(_CORE_DATA / "data_with_stats.db")
table_name = 'simplified'
df = pd.read_csv(csv_file)
conn = sqlite3.connect(db_file)
df.to_sql(table_name, conn, if_exists='replace', index=False)


def get_columns(columns, user_id):
    String_col1 = ", ".join(columns)
    # user_id in this table is a scrambled_id integer; compare without quotes
    queryUser = f"SELECT {String_col1} FROM {table_name} WHERE user_id = {int(user_id)}"
    df_result = pd.read_sql_query(queryUser, conn)
    return df_result
