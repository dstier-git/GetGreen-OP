import sys
import re
from pathlib import Path

# Ensure this server uses only backend code from core/backend (not top-level backend/)
_core_backend = Path(__file__).resolve().parent
if str(_core_backend) not in sys.path:
    sys.path.insert(0, str(_core_backend))

from dotenv import load_dotenv
load_dotenv(_core_backend.parent / ".env")
load_dotenv()  # cwd as fallback

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Literal, Dict, Any
from llama import ResponseGenerator
from chatgpt import generate_response_chatgpt_compact, generate_welcome_chatgpt
import user_retriever
from vector_retriever import retrieve_relevant_docs
from intent_router import classify_intent
from response_formatter import format_compact_response
from welcome_builder import build_welcome_instruction, build_welcome_fallback_text

# TODO: wrap your function file in a class called ResponseGenerator
# this allows us to import our function into another file!

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HistoryTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str
    provider: Optional[str] = "chatgpt"
    user_id: Optional[int] = None
    history: Optional[List[HistoryTurn]] = None


class ChatResponse(BaseModel):
    response: str
    meta: Optional[Dict[str, Any]] = None


class WelcomeRequest(BaseModel):
    user_id: Optional[int] = None
    provider: Optional[str] = "chatgpt"


class WelcomeResponse(BaseModel):
    message: str
    meta: Optional[Dict[str, Any]] = None

# TODO: fill out below

_repo_root = Path(__file__).resolve().parent.parent.parent

def _debug_log(location: str, message: str, data: dict, hypothesis_id: str):
    import json, time
    _log_path = _repo_root / ".cursor" / "debug.log"
    try:
        _log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(_log_path, "a") as f:
            f.write(json.dumps({"location": location, "message": message, "data": data, "timestamp": int(time.time() * 1000), "hypothesisId": hypothesis_id}) + "\n")
    except Exception:
        pass


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", (value or "").lower())).strip()


def _find_referenced_action(message: str, candidates: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    normalized_message = _normalize_text(message)
    if not normalized_message:
        return None

    for item in candidates[:40]:
        action_name = str(item.get("action_name") or "").strip()
        if not action_name:
            continue
        normalized_action = _normalize_text(action_name)
        if len(normalized_action) >= 8 and normalized_action in normalized_message:
            return item

        keywords = [token for token in normalized_action.split() if len(token) > 3]
        if not keywords:
            continue
        overlap = sum(1 for token in keywords if f" {token} " in f" {normalized_message} ")
        if overlap >= 2:
            return item
    return None


def _extract_compelling_article_note(article_context: str) -> Optional[str]:
    if not article_context:
        return None

    docs = [chunk.strip() for chunk in article_context.split("\n\n") if chunk.strip()]
    if not docs:
        return None

    pattern = re.compile(
        r"\b(carbo[n]?|emission|ghg|greenhouse|energy|waste|water|reuse|recycle|compost|cost|save|efficient)\b",
        re.IGNORECASE,
    )

    for chunk in docs[:2]:
        title = ""
        lines = [line.strip() for line in chunk.splitlines() if line.strip()]
        body = []
        for line in lines:
            if line.startswith("Title:"):
                title = line.replace("Title:", "", 1).strip()
            elif line.startswith(("Action IDs:", "Actions:", "URL:")):
                continue
            else:
                body.append(line)
        text = " ".join(body)
        if not text:
            continue
        sentences = re.split(r"(?<=[.!?])\s+", text)
        for sentence in sentences:
            cleaned = " ".join(sentence.split()).strip()
            if len(cleaned) < 60:
                continue
            if pattern.search(cleaned):
                clipped = " ".join(cleaned.split()[:28]).strip()
                if not clipped.endswith((".", "!", "?")):
                    clipped += "."
                prefix = f"From related reading ({title}): " if title else "From related reading: "
                return prefix + clipped
    return None


@app.post("/welcome")
async def welcome(request: WelcomeRequest):
    provider = (request.provider or "chatgpt").lower()
    user_id = request.user_id if request.user_id is not None else user_retriever.CURRENT_USER_ID
    summary = user_retriever.build_welcome_profile_summary(user_id=user_id)
    instruction = build_welcome_instruction(summary)
    fallback_text = build_welcome_fallback_text(summary)

    used_provider = "fallback"
    fallback_used = False
    message = ""

    try:
        if provider in ("chatgpt", "auto"):
            try:
                message = generate_welcome_chatgpt(instruction)
                used_provider = "chatgpt"
            except Exception as chatgpt_error:
                fallback_used = True
                _debug_log(
                    "response.py:welcome",
                    "chatgpt fallback",
                    {"error": str(chatgpt_error), "type": type(chatgpt_error).__name__},
                    "W1",
                )
                message = ResponseGenerator.generate_welcome(instruction)
                used_provider = "llama"
        elif provider == "llama":
            message = ResponseGenerator.generate_welcome(instruction)
            used_provider = "llama"
        else:
            # unknown provider -> treat as auto
            try:
                message = generate_welcome_chatgpt(instruction)
                used_provider = "chatgpt"
            except Exception:
                fallback_used = True
                message = ResponseGenerator.generate_welcome(instruction)
                used_provider = "llama"
    except Exception as final_error:
        fallback_used = True
        _debug_log(
            "response.py:welcome",
            "provider and fallback failed",
            {"error": str(final_error), "type": type(final_error).__name__},
            "W2",
        )
        message = fallback_text
        used_provider = "fallback"

    if not message:
        fallback_used = True
        message = fallback_text
        used_provider = "fallback"

    return WelcomeResponse(
        message=message,
        meta={
            "used_provider": used_provider,
            "fallback_used": fallback_used,
        },
    )

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        # #region agent log
        provider = (request.provider or "chatgpt").lower()
        user_id = request.user_id if request.user_id is not None else user_retriever.CURRENT_USER_ID
        history = [(turn.role, turn.content) for turn in (request.history or [])][-20:]
        intent = classify_intent(request.message or "")
        _debug_log("response.py:chat", "request received", {"raw_provider": request.provider, "provider": provider, "message_len": len(request.message or "")}, "B")
        # #endregion
        print("\n[API] /chat request received")
        print(f"[API] Incoming user message: {request.message!r}")
        print(f"[API] Provider: {provider}")
        print(f"[API] User ID: {user_id}")
        print(f"[API] Intent: {intent}")
        print(f"[API] History turns: {len(history)}")

        article_context = retrieve_relevant_docs(request.message, k=2)
        candidates = user_retriever.get_recommendation_candidates(user_id=user_id, n=20)
        selected_actions = [item for item in candidates if item.get("source_url")][:2]
        recommendations_context = user_retriever.recommendation_candidates_to_context(candidates, limit=10)
        user_context = user_retriever.build_user_context(user_id=user_id)
        referenced_action = _find_referenced_action(request.message, candidates)
        article_note = None
        if referenced_action:
            action_query = str(referenced_action.get("action_name") or request.message)
            action_article_context = retrieve_relevant_docs(action_query, k=2)
            article_note = _extract_compelling_article_note(action_article_context)
        elif selected_actions:
            action_query = str(selected_actions[0].get("action_name") or request.message)
            action_article_context = retrieve_relevant_docs(action_query, k=2)
            article_note = _extract_compelling_article_note(action_article_context)

        used_provider = "llama"
        fallback_used = False

        if provider in ("chatgpt", "auto"):
            try:
                response_direct = generate_response_chatgpt_compact(
                    request.message,
                    columns=['most_frequent_category', 'most_frequent_action', 'action_name', 'leaf_value'],
                    user_id=user_id,
                    history=history,
                    article_context=article_context,
                    user_context=user_context,
                    recommendations_context=recommendations_context,
                    intent=intent,
                )
                used_provider = "chatgpt"
            except Exception as chatgpt_error:
                fallback_used = True
                _debug_log(
                    "response.py:chat",
                    "chatgpt fallback",
                    {"error": str(chatgpt_error), "type": type(chatgpt_error).__name__},
                    "F1",
                )
                response_direct = ResponseGenerator.generate_response_compact(
                    request.message,
                    columns=['most_frequent_category', 'most_frequent_action', 'action_name', 'leaf_value'],
                    user_id=user_id,
                    history=history,
                    article_context=article_context,
                    user_context=user_context,
                    recommendations_context=recommendations_context,
                    intent=intent,
                )
                used_provider = "llama"
        else:
            response_direct = ResponseGenerator.generate_response_compact(
                request.message,
                columns=['most_frequent_category', 'most_frequent_action', 'action_name', 'leaf_value'],
                user_id=user_id,
                history=history,
                article_context=article_context,
                user_context=user_context,
                recommendations_context=recommendations_context,
                intent=intent,
            )

        include_recommendations = intent in {"recommend", "weekly_plan"}

        response_text = format_compact_response(
            direct_answer=response_direct,
            recommendations=selected_actions if include_recommendations else None,
            article_note=article_note,
            truncate_direct_answer=(used_provider != "chatgpt"),
            ask_follow_up=intent in {"recommend", "weekly_plan"},
        )
        print("[API] Response successfully generated, sending back to client.")
        # #region agent log
        _debug_log("response.py:chat", "success", {"response_len": len(response_text or "")}, "H4")
        # #endregion
        return ChatResponse(
            response=response_text,
            meta={
                "intent": intent,
                "used_provider": used_provider,
                "fallback_used": fallback_used,
            },
        )
    except Exception as e:
        # #region agent log
        _debug_log("response.py:chat", "exception", {"error": str(e), "type": type(e).__name__}, "E")
        # #endregion
        print(f"[API] ERROR while processing /chat request: {e}")
        raise HTTPException(status_code=500, detail=str(e))
