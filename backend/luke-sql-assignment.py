import sqlite3
import pandas as pd

def run_sql_query(cols, user_id):
    df = pd.read_csv("/Users/lukespencer/Downloads/simplified-data.csv", header=0)
    #print(df.head())
    conn = sqlite3.connect("database.db")
    df.to_sql("database", conn, if_exists='replace', index=False)
    col_string = ", ".join(cols)
    print(col_string)
    query = f"SELECT {col_string} FROM database WHERE user_id = {user_id}"
    result = pd.read_sql_query(query, conn)
    conn.close()
    return result

if __name__ == "__main__":
    while True:
        cols = []
        user_id = str(input("Enter user_id: ")) # ex: '62002cce-0993-4658-b6dd-ec2b10bd3337'
        while True:
            col = str(input("Enter column: "))
            cols.append(col) # cols = ['action_name', 'leaf_value', 'effort_level', 'time', 'user_id', 'categories']
            more_cols = str(input("Add more columns? (Y/N): "))
            if more_cols.lower() != 'y':
                break

        result = run_sql_query(cols, user_id)
        print(result)
        another = str(input("Run another query? (Y/N): "))
        if another.lower() != 'y':
            break
    