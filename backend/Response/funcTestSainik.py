import pandas as pd
import sqlite3
csv_file = 'data_with_stats-copy.csv'
db_file = 'data_with_stats.db'
table_name = 'simplified'
df = pd.read_csv(csv_file)
conn = sqlite3.connect(db_file)
df.to_sql(table_name, conn, if_exists='replace', index=False)

# print(df.head())

# takes in a list of column name(s) and uses the sqlite3 api to read a query retrieving them
def get_columns(columns, user_id):
    
    String_col1 = ""
    for i, cols in enumerate(columns):
        String_col1 += cols
        if i < len(columns) - 1:
            String_col1 += ", "
    queryUser = f"SELECT {String_col1} FROM {table_name} WHERE user_id = '{user_id}'"
    df_result = pd.read_sql_query(queryUser, conn)
    return df_result
    
# # example case calling the function
# columns_getting = ['user_id', 'leaf_value']
# user_id_value = '821ce161-3539-4b46-858a-437deb80e1b8'
# final_answer = get_columns(columns_getting, user_id_value)
# print(final_answer)








