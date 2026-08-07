
# ******************** Importing Libraries *********************
import time
import logfire

from app.gateways.embeddings_client import get_langchain_embeddings
from app.config import settings


# ******************** Constants *********************
BATCH_SIZE = 50

_active_model = None
_model_type = None


# ******************** Initialize Model *********************
def initialize_embeddings():
    """
    Initialize embedding model only once.
    Now backed by Portkey Gateway (load balancing / fallback handled by Portkey Config).
    """

    global _active_model
    global _model_type

    if _active_model is not None:
        return

    with logfire.span("initialize_embeddings"):
        _active_model = get_langchain_embeddings()
        _model_type = "portkey"

        logfire.info(f"Embedding model initialized. Active model type: {_model_type}")


# ******************** Embed Batch *********************
def embed_batch(batch: list[str]) -> list[list[float]]:
    """
    Generate embeddings for a batch of texts.
    """

    # FIX: global declaration function ke start mein honi chahiye,
    # warna "_model_type" ka use uske pehle SyntaxError deta hai
    # ("name used prior to global declaration").
    global _active_model
    global _model_type

    initialize_embeddings()

    retries = 3

    with logfire.span("embed_batch", batch_size=len(batch), model_type=_model_type) as span:

        for attempt in range(1, retries + 1):

            with logfire.span(f"embed_batch_attempt_{attempt}", attempt=attempt, retries=retries):

                try:
                    embeddings = _active_model.embed_documents(batch)

                    logfire.info(
                        f"Embedded batch successfully using {_model_type}. "
                        f"Batch Size: {len(batch)}"
                    )

                    span.set_attribute("status", "success")
                    span.set_attribute("model_type_used", _model_type)

                    return embeddings

                except Exception as e:

                    logfire.error(
                        f"Embedding failed. Attempt {attempt}/{retries}. Error: {e}"
                    )

                    if attempt < retries:
                        wait_time = 2 ** attempt

                        logfire.info(
                            f"Retrying after {wait_time} seconds..."
                        )

                        time.sleep(wait_time)

        span.set_attribute("status", "failed")
        raise RuntimeError("Embedding generation failed.")


# ******************** Embed Single Query *********************
def embed_query(text: str) -> list[float]:
    """
    Generate embedding for a single query.
    """
    global _active_model
    global _model_type

    initialize_embeddings()

    with logfire.span("embed_query", model_type=_model_type, text_length=len(text)):
        try:
            return _active_model.embed_query(text)
        except Exception as e:
            logfire.error(f"Query embedding failed on {_model_type}: {e}")
            raise