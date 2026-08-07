import logfire
from qdrant_client import QdrantClient
from qdrant_client.http import models

from app.config import settings
from app.services.retrieval.embeddings import embed_query

# Initialize Qdrant Client
client = QdrantClient(
    url=settings.QDRANT_ENDPOINT,
    api_key=settings.QDRANT_API_KEY,
    timeout=60.0
)


def search_knowledge(query: str, limit: int = 8):
    """
    Performs a high-precision search in the official PydanticAI
    documentation stored in Qdrant.

    Only searches:
    - core_docs
    - advanced_docs
    - model_docs

    Any noisy_data is automatically ignored.
    """
    try:
        # Generate embedding for user query
        query_vector = embed_query(query)

        # Filter to search ONLY official documentation
        official_docs_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="category",
                    match=models.MatchAny(
                        any=[
                            "core_docs",
                            "advanced_docs",
                            "model_docs",
                        ]
                    ),
                )
            ]
        )

        # Search Qdrant
        response = client.query_points(
            collection_name=settings.QDRANT_COLLECTION_NAME,
            query=query_vector,
            query_filter=official_docs_filter,
            limit=limit,
            with_payload=True,
        )

        results = []

        for res in response.points:
            results.append(
                {
                    "content": res.payload.get("content", ""),
                    "source": res.payload.get("source", "Unknown"),
                    "category": res.payload.get("category", "Unknown"),
                    "score": res.score,
                }
            )

        return results

    except Exception as e:
        logfire.error(f" Qdrant Search Failed: {e}")
        return []