import time
from flashrank import Ranker, RerankRequest
import logfire

# Global variable for lazy initialization
_ranker = None


def _get_ranker() -> Ranker:
    """Lazy initializes the FlashRank model to speed up startup time."""
    global _ranker
    if _ranker is None:
        # Trace model loading process in Logfire
        with logfire.span("Initializing FlashRank model"):
            try:
                # Custom cache directory to prevent permission issues
                _ranker = Ranker(cache_dir="/tmp/flashrank")
            except Exception as e:
                logfire.warning("Custom cache path failed, falling back to default", error=str(e))
                _ranker = Ranker()
    return _ranker


def rerank_documents(query: str, documents: list[str], top_n: int = 5) -> list[str]:
    """Reranks a list of text documents based on relevance to the query."""
    if not documents:
        return []

    # Wrap reranking process with logfire span for observability
    with logfire.span("Reranking documents", query=query, total_docs=len(documents)):
        ranker = _get_ranker()

        # Format input documents into FlashRank expected format
        passages = [{"id": idx, "text": doc} for idx, doc in enumerate(documents)]
        rerank_request = RerankRequest(query=query, passages=passages)

        # Perform reranking
        results = ranker.rerank(rerank_request)

        # Extract top N relevant document texts
        top_results = [item["text"] for item in results[:top_n]]
        
        return top_results