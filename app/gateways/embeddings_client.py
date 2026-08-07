

import logfire
from portkey_ai import PORTKEY_GATEWAY_URL, createHeaders
from langchain_openai import OpenAIEmbeddings
from app.config import settings


def get_langchain_embeddings() -> OpenAIEmbeddings:
    """
    Initializes and returns a Portkey-backed OpenAIEmbeddings instance.
    Configured for single-provider load balancing and caching.
    """
    # Log the initialization process with context
    logfire.info(
        "Initializing Enterprise Portkey Embeddings gateway",
        feature="embeddings",
        config_id=settings.PORTKEY_EMBED_CONFIG_ID
    )

    # Create headers for Portkey Gateway routing
    headers = createHeaders(
        api_key=settings.PORTKEY_API_KEY,
        config=settings.PORTKEY_EMBED_CONFIG_ID,  # Dedicated Embedding Config ID
        metadata={
            "feature": "embeddings",
            "_user": "rag-system",
            "environment": "production"
        }
    )

    # Initialize OpenAI Embeddings client via Portkey
    embeddings = OpenAIEmbeddings(
        api_key=settings.PORTKEY_API_KEY,
        base_url=PORTKEY_GATEWAY_URL,
        model=settings.EMBEDDING_MODEL,  # Required by LangChain SDK
        max_retries=0,  # Retries are handled by Portkey Config
        default_headers=headers
    )

    logfire.debug("Successfully created OpenAIEmbeddings instance via Portkey Gateway.")

    return embeddings