"""
Shared configuration and HTTP client for talking to the real Enterprise
RAG backend (LangGraph + NeMo Guardrails + Qdrant + FlashRank + Portkey).

Every attack module in this red-teaming suite sends its payloads through
`query_rag_system()` so we are always testing the actual deployed
`/query` endpoint end-to-end (Guardrails -> LangGraph -> LLM -> stream),
instead of mocking the target with a raw OpenAI call.
"""

import asyncio
import os
import uuid
from typing import Optional

import httpx
from dotenv import load_dotenv

# PyRIT requires its memory backend to be initialized once, globally,
# before any PromptTarget (OpenAIChatTarget, our EnterpriseRagTarget,
# etc.) is constructed anywhere in the process — otherwise you get
# "Central memory instance has not been set". Every attack module
# imports rag_client first, so doing it here guarantees it runs exactly
# once before any scorer or target is built.
#
# NOTE: this is the PyRIT 1.1.0 API (`pyrit.setup.initialize_pyrit_async`,
# async-only). Older PyRIT releases expose a sync `initialize_pyrit()`
# under `pyrit.common` instead — if `pyrit.setup` doesn't exist in your
# installed version, switch to that form.
from pyrit.setup import initialize_pyrit_async, IN_MEMORY

asyncio.run(initialize_pyrit_async(memory_db_type=IN_MEMORY))

load_dotenv()

RAG_ENDPOINT = os.getenv("RAG_ENDPOINT", "http://127.0.0.1:8000/query")
RAG_REQUEST_KEY = os.getenv("RAG_REQUEST_KEY", "q")
RAG_RESPONSE_KEY = os.getenv("RAG_RESPONSE_KEY", "response")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
REQUEST_TIMEOUT_SECONDS = 30.0


async def query_rag_system(payload: str, thread_id: Optional[str] = None) -> str:
    """
    Send one query to the real Enterprise RAG `/query` endpoint and return
    the fully concatenated streamed response as plain text.

    Parameters
    ----------
    payload:
        The (possibly malicious) text sent as the user query. This is
        exactly how every attack in this suite is delivered — through the
        real request body, not a mocked target.
    thread_id:
        LangGraph checkpointing thread id. Reuse the same id across calls
        to preserve conversational memory for multi-turn attacks
        (Crescendo / Orchestrator). Leave as None to get a fresh session
        for single-shot attacks.
    """
    body = {
        RAG_REQUEST_KEY: payload,
        "thread_id": thread_id or str(uuid.uuid4()),
    }

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            async with client.stream("POST", RAG_ENDPOINT, json=body) as response:
                response.raise_for_status()
                text_chunks = [chunk async for chunk in response.aiter_text()]
                return "".join(text_chunks).strip()
    except httpx.HTTPError as exc:
        # Surface connection/HTTP failures as a visible result instead of
        # crashing the whole test run — the dashboard can then flag the
        # module as "Failed" (infra issue) instead of "SAFE" (false negative).
        return f"[RAG_CONNECTION_ERROR] Could not reach {RAG_ENDPOINT}: {exc}"