from supabase_config import supabase

def run_sql_query_supabase(table_name, cols, user_id):
    col_string = ", ".join(cols)
    response = (
        supabase
        .table(table_name)
        .select(col_string)
        .eq("user_id", user_id)
        .limit(5)
        .execute()
    )
    return response.data

if __name__ == "__main__":
    print(run_sql_query_supabase("start-table", ["action_name", "leaf_value"], "62002cce-0993-4658-b6dd-ec2b10bd3337"))