from llama_cpp import Llama


model_path = r"C:\LLM\Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"


slm = Llama(
    model_path=model_path,
    n_gpu_layers=0,
    n_ctx=4096,
    verbose=False,
    cache=True
)


SYSTEM_PROMPT = """You are GetGreen.AI — a friendly, practical chatbot that helps people
take small, realistic environmental actions every day.


Tone: upbeat, supportive, and action-oriented.
Focus areas: food, shopping, transportation, energy use, waste reduction.
Keep answers short and encouraging. Try to keep it less than 5 sentences.  Avoid using lists if possible
Do NOT include 'User:' or 'Assistant:' in your replies.
"""


EXAMPLES = """
Examples:
User: I'm going grocery shopping.
Assistant: Don't forget reusable bags and local produce!
User: I'm cooking dinner tonight.
Assistant: Try a meatless recipe — good for you and the planet!
User: I just filled out my sustainability interests.
Assistant: Awesome! Want ideas that match your favorite eco-categories?
---
"""


def build_prompt(history, first_turn):
    convo = ""
    for role, text in history:
        convo += f"{role}: {text}\n"


    if first_turn:
        # first turn: system + examples + convo
        return f"{SYSTEM_PROMPT}\n{EXAMPLES}{convo}Assistant: "
    else:
        # later turns: system + convo (no examples)
        return f"{SYSTEM_PROMPT}\n{convo}Assistant: "


history = []
first_turn = True


print("🌿 GetGreen.AI Chatbot (type 'exit' to quit)\n")


while True:
    user_input = input("You: ")
    if user_input.lower().strip() == "exit":
        break


    history.append(("User", user_input))


    prompt = build_prompt(history, first_turn)


    result = slm(
        prompt,
        max_tokens=200,
        temperature=0.6,
        top_p=0.95,
        repeat_penalty = 1.1,
        stop=["User:", "\nUser:", "<|eot_id|>"],
    )


    raw = result["choices"][0]["text"]
    assistant_response = raw.strip()


    history.append(("Assistant", assistant_response))


    first_turn = False


    print("\nAssistant:", assistant_response, "\n")

