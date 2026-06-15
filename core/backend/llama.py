import requests
import json
import pandas as pd
import data_retriever
import user_retriever
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

SYSTEM_PROMPT = """You are GiGi from GetGreen.AI — a friendly, practical sustainability assistant that helps people take small, realistic environmental actions every day.

Tone: upbeat, supportive, conversational, and action-oriented.
Focus areas: food, shopping, transportation, energy use, waste reduction.
Keep replies short (2–4 sentences), encouraging, and simple. Avoid lists unless necessary.
Offer small, realistic tips — never extreme or guilt-inducing.
Do not give technical, medical, or legal advice.
Do not always ask a question at the end. Ask one brief follow-up question only when it helps keep the conversation going.
Do NOT include "User:" or "Assistant:" in your replies.
Address the user as John when natural.

When recommending actions:
- Only recommend actions from the [Suggested Actions] list provided in the prompt.
- Personalize recommendations based on the user's completed actions and categories shown in [User Information].
- Sources are optional. Only reference a source when it adds meaningful metrics (like carbon/emissions numbers) or clear personal relevance for John's life.
- Do not invent source information.
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
        - Personalized user context with completed actions and article sources
        - Pre-filtered action recommendations with source status
        - System prompt and examples
        - Ollama model for text generation
        """
        print("\n[ResponseGenerator] ---- New query --------------------------------")
        print(f"[ResponseGenerator] Prompt: {prompt!r}")
        print(f"[ResponseGenerator] Columns requested: {columns}")
        print(f"[ResponseGenerator] User ID: {user_id}")

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
        print("[ResponseGenerator] Retrieving relevant articles via vector search...")
        article_context = retrieve_relevant_docs(prompt, k=2)
        if article_context:
            print("[ResponseGenerator] Articles context retrieved (non-empty).")
        else:
            print("[ResponseGenerator] No relevant articles found or empty context returned.")

        # Build rich personalized user context (profile + completed actions + article sources)
        print("[ResponseGenerator] Building personalized user context...")
        user_context = user_retriever.build_user_context(user_id)
        print(f"[ResponseGenerator] User context built ({len(user_context)} chars).")

        # Supplement with stats rows from data_with_stats if available
        user_data = data_retriever.get_columns(columns, user_id)
        stats_context = table_to_context(user_data)
        if stats_context:
            user_context += "\n\nAdditional stats:\n" + stats_context

        # Build recommendations list (filtered against user history, with source status)
        print("[ResponseGenerator] Building action recommendations...")
        recommendations_context = user_retriever.get_recommendations_context(user_id)
        print(f"[ResponseGenerator] Recommendations built ({len(recommendations_context)} chars).")

        # Build conversation history string if provided
        convo = ""
        if history:
            for role, text in history:
                convo += f"{role}: {text}\n"
        else:
            convo = f"User: {prompt}\n"

        full_prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"[Examples:]\n{EXAMPLES}\n\n"
            f"[Relevant Articles:]\n"
            f"{article_context if article_context else 'No relevant articles found.'}\n\n"
            f"[User Information:]\n{user_context}\n\n"
            f"[Suggested Actions:]\n{recommendations_context}\n\n"
            f"[Conversation so far:]\n{convo}\n\n"
            f"Assistant:"
        )

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
                    "num_predict": 200,
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

        assistant_response = generated_text.strip()
        assistant_response = assistant_response.split("You are GetGreen.AI")[0].strip()
        assistant_response = assistant_response.split("User:")[0].strip()
        assistant_response = " ".join(assistant_response.split())

        print("\n[ResponseGenerator] Generation complete. Returning response.\n")
        return assistant_response

    @staticmethod
    def generate_response_compact(
        prompt,
        columns,
        user_id,
        history=None,
        article_context=None,
        user_context=None,
        recommendations_context=None,
        intent="general_qa",
    ):
        print("\n[ResponseGenerator] ---- Compact mode query -----------------------")
        print(f"[ResponseGenerator] Intent: {intent}")

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

        if article_context is None:
            article_context = retrieve_relevant_docs(prompt, k=2)
        if user_context is None:
            user_context = user_retriever.build_user_context(user_id)
        if recommendations_context is None:
            recommendations_context = user_retriever.get_recommendations_context(user_id)

        user_data = data_retriever.get_columns(columns, user_id)
        stats_context = table_to_context(user_data)
        if stats_context:
            user_context += "\n\nAdditional stats:\n" + stats_context

        convo = ""
        if history:
            for role, text in history:
                convo += f"{role}: {text}\n"
        else:
            convo = f"User: {prompt}\n"

        intent_instruction = {
            "compare": "Provide a practical comparison and choose the better option for this user's profile.",
            "weekly_plan": "Answer like a short weekly-plan intro with realistic and repeatable behavior.",
            "impact_explain": "Explain impact qualitatively using user profile and article evidence without numeric estimates.",
            "recommend": "Recommend practical next steps based on user profile.",
            "recycle_text": "Give conservative recycling guidance and mention uncertainty when needed.",
        }.get(intent, "Give a concise practical answer tailored to this user.")

        full_prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"[Intent]\n{intent}\n"
            f"[Instruction]\n{intent_instruction}\n\n"
            f"[Relevant Articles]\n"
            f"{article_context if article_context else 'No relevant articles found.'}\n\n"
            f"[User Information]\n{user_context}\n\n"
            f"[Suggested Actions]\n{recommendations_context}\n\n"
            f"[Conversation so far]\n{convo}\n\n"
            f"Return only a friendly direct answer in 2-4 sentences, plain text, no list, no labels. "
            f"Do not repeat exact phrasing used in recent assistant turns.\n\n"
            f"Assistant:"
        )

        with requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": full_prompt,
                "options": {
                    "temperature": 0.6,
                    "top_p": 0.95,
                    "num_predict": 140,
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

        assistant_response = generated_text.strip()
        assistant_response = assistant_response.split("You are GetGreen.AI")[0].strip()
        assistant_response = assistant_response.split("User:")[0].strip()
        assistant_response = " ".join(assistant_response.split())
        return assistant_response

    @staticmethod
    def generate_welcome(instruction: str):
        full_prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"{instruction}\n\n"
            f"Assistant:"
        )
        with requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": full_prompt,
                "options": {
                    "temperature": 0.6,
                    "top_p": 0.95,
                    "num_predict": 140,
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

        assistant_response = generated_text.strip()
        assistant_response = assistant_response.split("User:")[0].strip()
        assistant_response = " ".join(assistant_response.split())
        return assistant_response
