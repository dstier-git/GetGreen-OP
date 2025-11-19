from transformers import pipeline
import torch, platform

model_id = "meta-llama/Llama-3.2-1B"

# Auto device + dtype
if torch.backends.mps.is_available():
    device_map = "mps"
    dtype = torch.float16
    print("Running on Apple MPS with float16")
elif torch.cuda.is_available():
    device_map = "cuda"
    dtype = torch.bfloat16
    print("Running on CUDA GPU with bfloat16")
else:
    device_map = "cpu"
    dtype = torch.bfloat16
    print("Running on CPU (bfloat16)")

slm = pipeline(
    "text-generation",
    model=model_id,
    model_kwargs={"torch_dtype": dtype},
    device_map=device_map
)


SYSTEM_PROMPT = """You are GetGreen.AI — a friendly, practical chatbot that helps people
take small, realistic environmental actions every day.

Tone: upbeat, supportive, and action-oriented.
Focus areas: food, shopping, transportation, energy use, waste reduction.
Keep answers short and encouraging — 1-3 sentences with clear suggestions.
"""

def create_few_shot(user_input):
    FEW_SHOT_PROMPT = f"""{SYSTEM_PROMPT}

Examples:
User: I'm going grocery shopping.
Assistant: Don't forget reusable bags and local produce!
User: I'm cooking dinner tonight.
Assistant: Try a meatless recipe — good for you and the planet!
User: I just filled out my sustainability interests.
Assistant: Awesome! Want ideas that match your favorite eco-categories?
---
Now respond in the same style.
User: {user_input}
Assistant:"""
    return FEW_SHOT_PROMPT

user_input = "What can I do this weekend to be more sustainable?"
prompt = create_few_shot(user_input)

result = slm(
    prompt,
    max_new_tokens=120,
    temperature=0.6,
    top_p=0.95,
    do_sample=True
)

output = result[0]["generated_text"]
assistant_reply = output.split("Assistant:")[-1].split("User:")[0].strip()
print(assistant_reply)
