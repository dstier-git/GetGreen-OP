import os
import pandas as pd
from openai import OpenAI
import data_retriever
from vector_retriever import retrieve_relevant_docs
from llama import SYSTEM_PROMPT, EXAMPLES


def _get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPEN_AI_KEY")
    if not api_key:
        raise RuntimeError("Missing OpenAI API key. Set OPENAI_API_KEY (or OPEN_AI_KEY).")
    return OpenAI(api_key=api_key)


def generate_response_chatgpt(prompt, columns, user_id, history=None):
    print("\n[ChatGPT] ---- New query --------------------------------")
    print(f"[ChatGPT] Prompt: {prompt!r}")
    print(f"[ChatGPT] Columns requested: {columns}")
    print(f"[ChatGPT] User ID: {user_id}")

    # Convert tabular data into natural-language context
    def table_to_context(data):
        df = pd.DataFrame(data)
        if df.empty:
            return "No data found for this user."
        out = ["Here is the relevant user information:"]
        for _, row in df.iterrows():
            parts = [f"{col}: {row[col]}" for col in df.columns]
            out.append(" • " + ", ".join(parts))
        return "\n".join(out)

    # Retrieve relevant articles using vector search (RAG)
    print("[ChatGPT] Retrieving relevant articles via vector search...")
    article_context = retrieve_relevant_docs(prompt, k=2)
    if article_context:
        print("[ChatGPT] Articles context retrieved (non-empty).")
    else:
        print("[ChatGPT] No relevant articles found or empty context returned.")

    # Get user-specific data
    print("[ChatGPT] Fetching user data from database...")
    user_data = data_retriever.get_columns(columns, user_id)
    print(f"[ChatGPT] User data rows returned: {len(user_data) if hasattr(user_data, '__len__') else 'unknown'}")
    user_context = table_to_context(user_data)

    # Build conversation history string if provided
    convo = ""
    if history:
        for role, text in history:
            convo += f"{role}: {text}\n"
    else:
        convo = f"User: {prompt}\n"

    # Build the full prompt combining all contexts
    full_prompt = f"""
[Examples:]
{EXAMPLES}

[Relevant Articles:]
{article_context if article_context else "No relevant articles found."}

[User Information:]
{user_context}

[Conversation so far:]
{convo}

Assistant:"""

    print("[ChatGPT] Starting generation with OpenAI...")
    client = _get_openai_client()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    response = client.responses.create(
        model=model,
        input=full_prompt,
        instructions=SYSTEM_PROMPT,
    )

    assistant_response = response.output_text.strip() if response.output_text else ""
    assistant_response = assistant_response.split("You are GetGreen.AI")[0].strip()
    assistant_response = assistant_response.split("User:")[0].strip()
    assistant_response = " ".join(assistant_response.split())

    print("\n[ChatGPT] Generation complete. Returning response.\n")
    return assistant_response
