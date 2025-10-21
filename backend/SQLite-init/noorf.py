import sqlite3
import pandas as pd 

csv_file = 'simplified-data.csv'
db_file = 'data.db'
table_name = 'simplified_data'

df = pd.read_csv(csv_file)
conn = sqlite3.connect(db_file)
df.to_sql(table_name, conn, if_exists='replace', index=False)
#conn.close()


def function(columns:list[str], id: str):
    if(len(columns) == 0):
        return None
    
    col = columns[0]
    for i in range(1, len(columns)):
        col = col + f", {columns[i]}"
    q = f"SELECT {col} FROM {table_name} where user_id = '{id}'"
    
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute(q)

    row = cur.fetchall()

    result = ''
    for r in row:
        result = result + f"\n{r}"
    print(result)

    conn.close()

function(["action_name"], "62002cce-0993-4658-b6dd-ec2b10bd3337")
