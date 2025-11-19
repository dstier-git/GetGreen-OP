import pandas as pd
import sqlite3

csv_file = 'simplified-data.csv'
db_file = 'data.db'
table_name = 'simplified_data'

df = pd.read_csv(csv_file)
conn = sqlite3.connect(db_file)

df.to_sql("my_table", conn, if_exists='replace', index=False)
conn.close()


def function(db_file, table_name, columns, user_id):

    col = columns[0]
    for i in range(1, len(columns)):
        col = col + f", {columns[i]}"
    q = f"SELECT {col} FROM {table_name} WHERE user_id = ?;"

    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute(q, (user_id,))
    row = cur.fetchall()

    conn.close()
    result = f"Results for user {user_id}:\n{row}"

    print(result)
    return result


if __name__ == "__main__":
    db_path = "data.db"
    table = "my_table"
    function(db_path, table, ["name", "score"], 42)
