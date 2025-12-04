from llama_cpp import Llama
import pandas as pd
from sentence_transformers import SentenceTransformer
import faiss
import os

model_path = r"C:\LLM\Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
df = pd.read_csv("articles_cleaned_filtered.csv")


documents = (
    df["Title"].fillna("") + "\n\n" + df["scraped_text"].fillna("")
).tolist()

EMBED_DIM = 384    
INDEX_PATH = "faiss_index.bin"
EMBED_MODEL = SentenceTransformer("all-MiniLM-L6-v2")

if os.path.exists(INDEX_PATH):
    index = faiss.read_index(INDEX_PATH)
else:
    embeddings = EMBED_MODEL.encode(documents)
    index = faiss.IndexFlatL2(EMBED_DIM)
    index.add(embeddings)
    faiss.write_index(index, INDEX_PATH)

def retrieve_relevant_docs(query, k=2):
    q_emb = EMBED_MODEL.encode([query])
    D, I = index.search(q_emb, k)
    return "\n\n".join(documents[idx] for idx in I[0] if idx < len(documents))

slm = Llama(
    model_path=model_path,
    n_gpu_layers=0,
    n_ctx=4096,
    verbose=False,
    cache=True
)


SYSTEM_PROMPT = """You are GetGreen.AI — a friendly, practical chatbot that helps people take small, realistic environmental actions every day.

Tone: upbeat, supportive, conversational, and action-oriented.
Focus areas: food, shopping, transportation, energy use, waste reduction.
Keep replies short (2–4 sentences), encouraging, and simple. Avoid lists unless necessary.
Offer small, realistic tips — never extreme or guilt-inducing. 
Do not give technical, medical, or legal advice.
Do not always ask a question at the end. Ask one brief follow-up question only when it helps keep the conversation going. 
Do NOT include "User:" or "Assistant:" in your replies.
"""


EXAMPLES = """
Examples:
User: I'm going grocery shopping.
Assistant: Nice! Grab reusable bags and look for local produce — easy win for the planet.

User: I'm cooking dinner tonight.
Assistant: Fun! Try swapping in a plant-based protein this time. Even one meal makes a difference.

User: I just filled out my sustainability interests.
Assistant: Awesome! Want a few quick ideas that match what you’re into?

User: I'm heading to work now.
Assistant: If it's doable, try walking or biking part of the way. Little shifts add up fast!

User: I'm cleaning out my closet.
Assistant: Sweet! Consider donating or reselling pieces you don’t wear. It keeps them in use and out of the trash.
---
"""


def build_prompt(history, context):
    convo = ""
    for role, text in history:
        convo += f"{role}: {text}\n"

    return f"""
{SYSTEM_PROMPT}

[Examples:]
{EXAMPLES}

[Relevant Information:]
{context}

[Conversation so far:]
{convo}

Assistant:"""



history = []


print("🌿 GetGreen.AI Chatbot (type 'exit' to quit)\n")


while True:
    user_input = input("You: ")
    if user_input.lower().strip() == "exit":
        break


    history.append(("User", user_input))

    retrieved = retrieve_relevant_docs(user_input)
    prompt = build_prompt(history, context=retrieved)


    result = slm(
        prompt,
        max_tokens=200,
        temperature=0.6,
        top_p=0.95,
        repeat_penalty = 1.1,
        stop=["\n\n", "User:", "\nUser:", "<|eot_id|>"],
    )


    raw = result["choices"][0]["text"]
    assistant_response = raw.strip().split("You are GetGreen.AI")[0].strip()
    assistant_response = assistant_response.split("User:")[0].strip()
    assistant_response = " ".join(assistant_response.split())
    
    history.append(("Assistant", assistant_response))

    print("\nAssistant:", assistant_response, "\n")

