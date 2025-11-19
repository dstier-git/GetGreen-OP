from transformers import pipeline
import torch
import pandas as pd
import funcTestSainik

# TODO: move your SQL (Python) file to this folder
# import ...
#  ^^^  uncomment and replace ... with the name of your file (NOT including .py)

# ----------------------------------------
# TEXT GENERATION EXAMPLE
# ----------------------------------------

generator = pipeline(
    "text-generation",
    model="meta-llama/Llama-3.2-1B",
    dtype="auto",
    device_map="auto"   # change to "cpu" if your computer is not Apple silicon (M_ Processor)
)

prompt = "Explain the difference between supervised and unsupervised learning."

# the (commented) lines below are what generates and prints model response
# uncomment blocks of code by highlighting and typing command + slash

# output = generator(
#     prompt,
#     max_new_tokens=200,
#     do_sample=True,
#     top_p=0.9,
#     temperature=0.7
# )

# print(output[0]["generated_text"])

# end of generation
# ----------------------------------------

# TODO; fill out generate_response

# generates a response from a given prompt (String), columns (list[String]), and user_id (String)
def generate_response(prompt, columns, user_id):
    
    print("Function is running\n\n")

    # you can pass in the table result to this function to format it with text 
    def table_to_context(data):
        df = pd.DataFrame(data)
        if df.empty:
            return "data was not found for our user"
        out = ['Here are the main stuff: ']
        for idx, row in data.iterrows():
            parts = [f"{col}: {row[col]}" for col in data.columns]
            out.append(" • " + ", ".join(parts))
        return "\n".join(out)
    
    print("Getting the data ...\n\n")

    # TODO: retrieve data for these columns and user_id, add it to the prompt input, and generate a response
        # to call your function from your file, do file_name.function_name(xyz) and do NOT include .py in the file name
        # you can use a similar output = generator(...) structure as seen above here
        # context comes BEFORE the prompt
        # remember to RETURN the output from the LLM
    
    # retrieve data from columns and show the columns and user_id
    data = funcTestSainik.get_columns(columns, user_id)
    # turn the new table into NLP 
    context = table_to_context(data)
    # Context before prompt
    full_prompt = f"{context}\n\n{prompt}"
    
    print("Generating output/data...\n\n")
    
    
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
    
    output = generator(
    full_prompt,
    max_new_tokens=200,
    do_sample=True,
    top_p=0.9,
    temperature=0.7
)

    return output[0]["generated_text"]
    

# This checks if the function works (will take a long time)

print(generate_response(
    prompt='As you can see, popular actions with leaf_values include ',
    columns=['action_name', 'leaf_value'],
    user_id='821ce161-3539-4b46-858a-437deb80e1b8')
)
    
    
