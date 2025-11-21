from transformers import pipeline
import torch
import pandas as pd

#TODO: move your SQL (Python) file to this folder
import f2noor

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
        data = pd.DataFrame(data)
        out = ['Here are the main details: ']
        for idx, row in data.iterrows():
            parts = [f"{col}: {row[col]}" for col in data.columns]
            out.append(" • " + ", ".join(parts))
        return "\n".join(out)
    
    print("Generating output...\n\n")

    # TODO: retrieve data for these columns and user_id, add it to the prompt input, and generate a response
        # to call your function from your file, do file_name.function_name(xyz) and do NOT include .py in the file name
        # you can use a similar output = generator(...) structure as seen above here
        # context comes BEFORE the prompt
        # remember to RETURN the output from the LLM
    
    c = table_to_context(f2noor.function_alt(user_id, columns))
    prompt2 = c + "\n\n" + prompt
    output = generator(
        prompt2,
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
    
    