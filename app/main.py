
import os
from contextlib import asynccontextmanager

import logfire
from dotenv import load_dotenv
from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessageChunk
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware # for java script 
from app.agent.agent import rag_agent
from app.guardrails.rails import initialize_rails, guard


# Load Environment Variables
load_dotenv()


# Configure Logfire
logfire.configure(
    token=os.getenv("LOGFIRE_TOKEN"),
    service_name="pydocs-ai",
)



# FastAPI Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    with logfire.span("Application Startup"):
        logfire.info("Initializing NeMo Guardrails")

        initialize_rails()

        logfire.info("NeMo Guardrails initialized successfully")

    yield

    with logfire.span("Application Shutdown"):
        logfire.info("Application shutting down")



# FastAPI App
app = FastAPI(
    title="Pydocs AI Rag Agent",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Automatically logs:
# - HTTP requests
# - Latency
# - Status codes
# - Exceptions
logfire.instrument_fastapi(app)



# Request Model
class QueryRequest(BaseModel):
    q: str = Field(..., min_length=1, max_length=2000)
    thread_id: str = Field(
        default="default_user_thread",
        min_length=1,
        max_length=100,
    )



# Health Endpoint
@app.get("/health")
async def health():
    logfire.debug("Health endpoint called")
    return {"status": "healthy"}


# Home Endpoint
@app.get("/")
def home():
    logfire.debug("Home endpoint called")
    return {
        "message": "Pydocs AI Rag agent is live and running"
    }



# Graph Endpoint
@app.get("/graph")
def get_graph_image():
    """Endpoint to get LangGraph Mermaid PNG"""

    with logfire.span("Generate Graph Image"):
        try:
            logfire.info("Graph image requested")

            png_bytes = rag_agent.get_graph().draw_mermaid_png()

            logfire.info("Graph image generated successfully")

            return Response(
                content=png_bytes,
                media_type="image/png",
            )

        except Exception:
            logfire.exception("Failed to generate graph image")

            return {
                "error": "Could not generate graph image."
            }



# Query Endpoint
@app.post("/query")
async def query(request: QueryRequest):
    """Execute the LangGraph RAG flow with streaming output."""

    q = request.q
    thread_id = request.thread_id

    with logfire.span(
        "RAG Request",
        thread_id=thread_id,
    ):

        logfire.info(
            "New query received",
            thread_id=thread_id,
            query_length=len(q),
        )

        
        # Guardrails
        with logfire.span("Guardrails Check"):

            fired, rail_response = await guard(q)

            if fired:
                logfire.warning(
                    "Guardrail triggered",
                    thread_id=thread_id,
                )

                async def guard_stream():
                    yield rail_response

                return StreamingResponse(
                    guard_stream(),
                    media_type="text/plain",
                )

            logfire.info(
                "Guardrails passed",
                thread_id=thread_id,
            )

        
        # LangGraph Config
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

       
        # Streaming Generator
        async def generate_stream():

            chunk_count = 0

            with logfire.span(
                "LangGraph Streaming",
                thread_id=thread_id,
            ):

                try:
                    logfire.info(
                        "Starting streaming",
                        thread_id=thread_id,
                    )

                    async for chunk, metadata in rag_agent.astream(
                        {"messages": [("user", q)]},
                        config=config,
                        stream_mode="messages",
                    ):

                        if (
                            isinstance(chunk, AIMessageChunk)
                            and chunk.content
                        ):
                            chunk_count += 1
                            yield chunk.content

                    logfire.info(
                        "Streaming completed",
                        thread_id=thread_id,
                        chunks_streamed=chunk_count,
                    )

                except Exception:
                    logfire.exception(
                        "Streaming failed",
                        thread_id=thread_id,
                    )

                    yield "\n[Internal Server Error]"

        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
        )
