
import logfire
from portkey_ai import PORTKEY_GATEWAY_URL, createHeaders
from langchain_openai import ChatOpenAI
from app.config import settings


def get_langchain_llm(feature: str = "rag") -> ChatOpenAI:
    """
    Initializes and returns an enterprise-grade Portkey-backed LangChain ChatOpenAI instance.

    Features configured via Portkey Gateway Config:
    - Load balancing across multiple API keys/slugs
    - Automatic fallbacks (e.g., primary OpenAI to Grok/secondary targets)
    - Automatic retries on rate limits (429) & server errors (5xx)
    - Request caching & request timeouts

    Args:
        feature (str): The feature context using this LLM instance (default: 'rag').

    Returns:
        ChatOpenAI: Configured LangChain chat model routing through Portkey AI Gateway.
    """
    # Log initialization start with feature context
    logfire.info(
        "Initializing Enterprise Portkey Chat LLM gateway",
        feature=feature,
        config_id=settings.PORTKEY_CHAT_CONFIG_ID
    )

    # Construct request headers for Portkey AI Gateway routing and tracking
    headers = createHeaders(
        api_key=settings.PORTKEY_API_KEY,
        config=settings.PORTKEY_CHAT_CONFIG_ID,  # Portkey Chat Dashboard Config ID
        metadata={
            "feature": feature,
            "_user": "rag-system",
            "environment": "production",
            
        }
    )

    # Initialize LangChain ChatOpenAI instance connected to Portkey Gateway
    llm = ChatOpenAI(
        api_key=settings.PORTKEY_API_KEY,
        base_url=PORTKEY_GATEWAY_URL,
        model=settings.CHAT_MODEL,  # Fallback configs dynamically override model per target
        temperature=0,
        max_retries=0,  # Retries are handled directly by Portkey Gateway Config
        default_headers=headers
    )

    logfire.debug("Successfully created ChatOpenAI instance via Portkey Gateway.")
    
    return llm