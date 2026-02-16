import requests
import json
import pandas as pd
import funcTestSainik
from vector_retriever import retrieve_relevant_docs

# ----------------------------------------
# TEXT GENERATION SETUP (using Ollama)
# ----------------------------------------

# Name of your locally registered Ollama model
MODEL_NAME = "llama3.2-11b-instruct-local"

# Local Ollama server URL
OLLAMA_URL = "http://localhost:11434/api/generate"

# end of setup
# ----------------------------------------

# System prompt from dylan-script.py
SYSTEM_PROMPT = """You are GetGreen.AI — a friendly, practical chatbot that helps people take small, realistic environmental actions every day.

Tone: upbeat, supportive, conversational, and action-oriented.
Focus areas: food, shopping, transportation, energy use, waste reduction.
Keep replies short (2–4 sentences), encouraging, and simple. Avoid lists unless necessary.
Offer small, realistic tips — never extreme or guilt-inducing. 
Do not give technical, medical, or legal advice.
Do not always ask a question at the end. Ask one brief follow-up question only when it helps keep the conversation going. 
Do NOT include "User:" or "Assistant:" in your replies.
"""

# Examples from dylan-script.py
EXAMPLES = """
Examples:
User: I'm going grocery shopping.
Assistant: Nice! Grab reusable bags and look for local produce — easy win for the planet.

User: I'm cooking dinner tonight.
Assistant: Fun! Try swapping in a plant-based protein this time. Even one meal makes a difference.

User: I just filled out my sustainability interests.
Assistant: Awesome! Want a few quick ideas that match what you're into?

User: I'm heading to work now.
Assistant: If it's doable, try walking or biking part of the way. Little shifts add up fast!

User: I'm cleaning out my closet.
Assistant: Sweet! Consider donating or reselling pieces you don't wear. It keeps them in use and out of the trash.
---
"""


class ResponseGenerator:
    @staticmethod
    def generate_response(prompt, columns, user_id, history=None):
        """
        Generate a response combining:
        - Vector retrieval from articles (RAG)
        - User-specific data from database
        - System prompt and examples from dylan-script.py
        - Ollama model for text generation
        
        Args:
            prompt: User's message/query
            columns: List of column names to retrieve from user data
            user_id: User ID for data retrieval
            history: Optional list of (role, text) tuples for conversation history
        """
        print("\n[ResponseGenerator] ---- New query --------------------------------")
        print(f"[ResponseGenerator] Prompt: {prompt!r}")
        print(f"[ResponseGenerator] Columns requested: {columns}")
        print(f"[ResponseGenerator] User ID: {user_id}")

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
        print("[ResponseGenerator] Retrieving relevant articles via vector search...")
        article_context = retrieve_relevant_docs(prompt, k=2)
        if article_context:
            print("[ResponseGenerator] Articles context retrieved (non-empty).")
        else:
            print("[ResponseGenerator] No relevant articles found or empty context returned.")
        
        # Get user-specific data
        print("[ResponseGenerator] Fetching user data from database...")
        user_data = funcTestSainik.get_columns(columns, user_id)
        print(f"[ResponseGenerator] User data rows returned: {len(user_data) if hasattr(user_data, '__len__') else 'unknown'}")
        user_context = table_to_context(user_data)

        # Build conversation history string if provided
        convo = ""
        if history:
            for role, text in history:
                convo += f"{role}: {text}\n"
        else:
            # If no history, just show the current user message
            convo = f"User: {prompt}\n"

        # Build the full prompt combining all contexts
        full_prompt = f"""
{SYSTEM_PROMPT}

[Examples:]
{EXAMPLES}

[Relevant Articles:]
{article_context if article_context else "No relevant articles found."}

[User Information:]
{user_context}

[Conversation so far:]
{convo}

Assistant:"""

        print("[ResponseGenerator] Starting generation with Ollama...")

        # Stream generation from Ollama
        with requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": full_prompt,
                "options": {
                    "temperature": 0.6,
                    "top_p": 0.95,
                    "num_predict": 200,  # Increased to match dylan-script.py
                    "repeat_penalty": 1.1,
                },
            },
            stream=True,
        ) as r:
            generated_text = ""
            for line in r.iter_lines():
                if line:
                    data = json.loads(line.decode("utf-8"))
                    token = data.get("response", "")
                    generated_text += token
                    print(token, end="", flush=True)

        # Clean up the response (similar to dylan-script.py)
        assistant_response = generated_text.strip()
        # Remove any unwanted prefixes or artifacts
        assistant_response = assistant_response.split("You are GetGreen.AI")[0].strip()
        assistant_response = assistant_response.split("User:")[0].strip()
        assistant_response = " ".join(assistant_response.split())

        print("\n[ResponseGenerator] Generation complete. Returning response.\n")
        return assistant_response

# Example test call
# Uncomment to verify (takes a moment on first load):
# print(
#     ResponseGenerator.generate_response(
#         prompt="As you can see, popular actions with leaf_values include:",
#         columns=["action_name", "leaf_value"],
#         user_id="821ce161-3539-4b46-858a-437deb80e1b8",
#     )
# )
