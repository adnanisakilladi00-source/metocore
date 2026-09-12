"""
METO CORE — production FastAPI backend for NEXORA.
AI provider: official Groq API.

Start (Render):
  uvicorn main:app --host 0.0.0.0 --port $PORT
"""

from __future__ import annotations

import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

VERSION = "2.1.0"

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip() or "llama-3.3-70b-versatile"
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").strip() or "*"
METO_AI_TOKEN = os.getenv("METO_AI_TOKEN", "").strip()  # optional; unused unless you extend auth

app = FastAPI(title="METO CORE", version=VERSION, docs_url=None, redoc_url=None)

_origins = ["*"] if ALLOWED_ORIGINS == "*" else [o.strip() for o in ALLOWED_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=_origins != ["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=32000)


@app.get("/api/health")
def health():
    return {
        "success": True,
        "service": "METO CORE Brain",
        "status": "online",
        "version": VERSION,
        "provider": "groq",
        "groq_key_configured": bool(GROQ_API_KEY),
        "auth_required": bool(METO_AI_TOKEN),
    }


@app.get("/api/capabilities")
def capabilities():
    return {
        "success": True,
        "chat": True,
        "vision": False,
        "image_generation": False,
        "image_editing": False,
        "video": False,
        "model": GROQ_MODEL,
        "provider": "groq",
    }


@app.post("/api/chat")
def chat(body: ChatRequest):
    message = body.message.strip()
    if not message:
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": {"code": "INVALID_REQUEST", "message": "message is required."},
            },
        )

    if not GROQ_API_KEY:
        raise HTTPException(
            status_code=503,
            detail={
                "success": False,
                "error": {
                    "code": "GROQ_KEY_MISSING",
                    "message": "GROQ_API_KEY is not configured on the server.",
                },
            },
        )

    try:
        from groq import Groq
    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": {
                    "code": "DEPENDENCY_ERROR",
                    "message": "groq package is not installed.",
                },
            },
        ) from e

    client = Groq(api_key=GROQ_API_KEY)

    try:
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are METO, a helpful AI assistant. Be clear and concise.",
                },
                {"role": "user", "content": message},
            ],
        )
    except Exception as e:
        err = str(e).lower()
        if "authentication" in err or "api key" in err or "unauthorized" in err:
            raise HTTPException(
                status_code=502,
                detail={
                    "success": False,
                    "error": {
                        "code": "GROQ_AUTH_ERROR",
                        "message": "Groq rejected the API key. Check GROQ_API_KEY on the server.",
                    },
                },
            ) from e
        if "rate" in err and "limit" in err:
            raise HTTPException(
                status_code=429,
                detail={
                    "success": False,
                    "error": {
                        "code": "RATE_LIMITED",
                        "message": "Groq rate limit exceeded. Try again later.",
                    },
                },
            ) from e
        safe = str(e)
        if len(safe) > 180:
            safe = safe[:180] + "…"
        if "gsk_" in safe:
            safe = "Groq API error (details withheld)."
        raise HTTPException(
            status_code=502,
            detail={
                "success": False,
                "error": {"code": "GROQ_API_ERROR", "message": safe},
            },
        ) from e

    reply = ""
    try:
        reply = (completion.choices[0].message.content or "").strip()
    except (IndexError, AttributeError):
        reply = ""
    if not reply:
        reply = "(No text returned)"

    return {
        "success": True,
        "reply": reply,
        "model": getattr(completion, "model", None) or GROQ_MODEL,
    }


@app.exception_handler(HTTPException)
async def http_exc_handler(_, exc: HTTPException):
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": {"code": "ERROR", "message": str(exc.detail)}},
    )


@app.exception_handler(Exception)
async def unhandled(_, __):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred.",
            },
        },
    )
