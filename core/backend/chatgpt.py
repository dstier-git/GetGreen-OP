import os
import json
import time
from pathlib import Path
import pandas as pd
from openai import OpenAI
import data_retriever
import user_retriever
from vector_retriever import retrieve_relevant_docs
from llama import SYSTEM_PROMPT, EXAMPLES

_repo_root = Path(__file__).resolve().parent.parent.parent


def _debug_log(location: str, message: str, data: dict, hypothesis_id: str):
    _log_path = _repo_root / ".cursor" / "debug.log"
    try:
        _log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(_log_path, "a") as f:
            f.write(json.dumps({"location": location, "message": message, "data": data, "timestamp": int(time.time() * 1000), "hypothesisId": hypothesis_id}) + "\n")
    except Exception:
        pass


def _get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPEN_AI_KEY")
    if not api_key:
        raise RuntimeError("Missing OpenAI API key. Set OPENAI_API_KEY (or OPEN_AI_KEY).")
    return OpenAI(api_key=api_key)


def generate_response_chatgpt(prompt, columns, user_id, history=None):
    # #region agent log
    _debug_log("chatgpt.py:generate_response_chatgpt", "entry", {"prompt_len": len(prompt or ""), "columns": columns}, "B")
    # #endregion
    print("\n[ChatGPT] ---- New query --------------------------------")
    print(f"[ChatGPT] Prompt: {prompt!r}")
    print(f"[ChatGPT] Columns requested: {columns}")
    print(f"[ChatGPT] User ID: {user_id}")

    # Convert tabular stats rows into natural-language text (supplemental)
    def table_to_context(data):
        df = pd.DataFrame(data)
        if df.empty:
            return ""
        out = []
        for _, row in df.iterrows():
            parts = [f"{col}: {row[col]}" for col in df.columns if pd.notna(row[col])]
            if parts:
                out.append(" • " + ", ".join(parts))
        return "\n".join(out)

    # Retrieve relevant articles using vector search (RAG)
    print("[ChatGPT] Retrieving relevant articles via vector search...")
    # #region agent log
    try:
        article_context = retrieve_relevant_docs(prompt, k=2)
        _debug_log("chatgpt.py:generate_response_chatgpt", "after retrieve_relevant_docs", {"has_context": bool(article_context)}, "E")
    except Exception as e_rag:
        _debug_log("chatgpt.py:generate_response_chatgpt", "retrieve_relevant_docs failed", {"error": str(e_rag), "type": type(e_rag).__name__}, "E")
        raise
    # #endregion
    if article_context:
        print("[ChatGPT] Articles context retrieved (non-empty).")
    else:
        print("[ChatGPT] No relevant articles found or empty context returned.")

    # Build rich personalized user context (profile + completed actions + article sources)
    print("[ChatGPT] Building personalized user context...")
    personalized_context = user_retriever.build_user_context(user_id)
    print(f"[ChatGPT] User context built ({len(personalized_context)} chars).")

    # Supplement with stats rows from data_with_stats if available
    user_data = data_retriever.get_columns(columns, user_id)
    stats_context = table_to_context(user_data)
    if stats_context:
        personalized_context += "\n\nAdditional stats:\n" + stats_context

    # Build recommendations list (filtered against user history, with source status)
    print("[ChatGPT] Building action recommendations...")
    recommendations_context = user_retriever.get_recommendations_context(user_id)
    print(f"[ChatGPT] Recommendations built ({len(recommendations_context)} chars).")

    # Build conversation history string if provided
    convo = ""
    if history:
        for role, text in history:
            convo += f"{role}: {text}\n"
    else:
        convo = f"User: {prompt}\n"

    full_prompt = (
        f"[Examples:]\n{EXAMPLES}\n\n"
        f"[Relevant Articles:]\n"
        f"{article_context if article_context else 'No relevant articles found.'}\n\n"
        f"[User Information:]\n{personalized_context}\n\n"
        f"[Suggested Actions:]\n{recommendations_context}\n\n"
        f"[Conversation so far:]\n{convo}\n\n"
        f"Assistant:"
    )

    print("[ChatGPT] Starting generation with OpenAI...")
    # #region agent log
    try:
        client = _get_openai_client()
        _debug_log("chatgpt.py:generate_response_chatgpt", "openai client ok", {}, "C")
    except Exception as e0:
        _debug_log("chatgpt.py:generate_response_chatgpt", "openai client failed", {"error": str(e0), "type": type(e0).__name__}, "C")
        raise
    # #endregion
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # #region agent log
    _debug_log("chatgpt.py:generate_response_chatgpt", "before chat.completions.create", {"model": model}, "D")
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": full_prompt},
            ],
        )
        _debug_log("chatgpt.py:generate_response_chatgpt", "after chat.completions.create", {"choices_len": len(response.choices) if response.choices else 0}, "D")
    except Exception as e1:
        _debug_log("chatgpt.py:generate_response_chatgpt", "chat.completions.create failed", {"error": str(e1), "type": type(e1).__name__}, "D")
        raise
    # #endregion

    raw = ""
    if response.choices and len(response.choices) > 0 and getattr(response.choices[0].message, "content", None):
        raw = response.choices[0].message.content
    assistant_response = raw.strip() if raw else ""
    assistant_response = assistant_response.split("You are GetGreen.AI")[0].strip()
    assistant_response = assistant_response.split("User:")[0].strip()
    assistant_response = " ".join(assistant_response.split())

    print("\n[ChatGPT] Generation complete. Returning response.\n")
    return assistant_response
