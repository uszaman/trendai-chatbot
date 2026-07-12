"""
TrendAI Chatbot - Backend API
POST /api/chat  ->  accepts {"message": "..."}, calls an LLM,
stores the conversation in MongoDB, returns {"reply": "..."}.
"""
import os
import datetime
import logging

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("chatbot")

# --- Config (all via env vars / K8s secrets, never hard-coded) ---
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://mongodb:27017")
DB_NAME = os.environ.get("DB_NAME", "chatbot")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")

app = FastAPI(title="TrendAI Chatbot API")

# CORS: in production, lock allow_origins to your frontend domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
conversations = db["conversations"]


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@app.get("/healthz")
def healthz():
    """Liveness/readiness probe endpoint."""
    return {"status": "ok"}


async def call_llm(message: str) -> str:
    """Call the Anthropic Messages API. Falls back to an echo if no key set."""
    if not ANTHROPIC_API_KEY:
        return f"(no LLM key configured) You said: {message}"

    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": 1024,
        "messages": [{"role": "user", "content": message}],
    }
    async with httpx.AsyncClient(timeout=30) as http:
        r = await http.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
        )
        #r.raise_for_status()
        if r.status_code != 200:
                 log.error("Anthropic API error %s: %s", r.status_code, r.text)
            r.raise_for_status()
        
        data = r.json()
        return "".join(
            block["text"] for block in data.get("content", [])
            if block.get("type") == "text"
        )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="message cannot be empty")

    try:
        reply = await call_llm(req.message)
    except Exception as e:
        log.exception("LLM call failed")
        raise HTTPException(status_code=502, detail="LLM upstream error") from e

    conversations.insert_one({
        "message": req.message,
        "reply": reply,
        "ts": datetime.datetime.utcnow(),
    })
    return ChatResponse(reply=reply)
