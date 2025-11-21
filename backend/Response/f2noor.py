import pandas as pd
import sqlite3

csv_file = 'simplified-data.csv'
db_file = 'data.db'
table_name = 'simplified_data'

df = pd.read_csv(csv_file)
conn = sqlite3.connect(db_file)

df.to_sql(table_name, conn, if_exists='replace', index=False)  # Fixed table name
conn.close()

def function_alt(columns, user_id):
    return function('data.db', 'simplified_data', columns, user_id)

def function(db_file, table_name, columns, user_id):
    col = ", ".join(columns)  # Safer column list construction
    q = f"SELECT {col} FROM {table_name} WHERE user_id = ?;"

    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute(q, (user_id,))  # Fixed: tuple parameter
    row = cur.fetchall()

    conn.close()
    result = f"Results for user {user_id}:\n{row}"

    print(result)
    return result