import logfire
from app.agent.state import AgentState
from app.services.retrieval.qdrant_service import search_knowledge
from app.services.retrieval.ranking_service import rerank_documents
from langchain_core.tools import tool

@tool
def rag_search_tool(query:str):
    """
        Search the official PydanticAI documentation and return the most relevant documentation passages for the given query.
    """

    
    # Standard Retrieval Logic
    with logfire.span(" Knowledge Retrieval"):
        logfire.info(f"Searching Qdrant for: {query}")
        raw_results = search_knowledge(query, limit=15)
        logfire.info(f"Retrieved {len(raw_results)} candidates from Vector DB")
        
        if not raw_results:
            logfire.warning("No documentation found")
            return "No documentation found in the documentation."
        else:
            doc_contents = [doc['content'] for doc in raw_results]
        
        with logfire.span(" Semantic Reranking"):
            reranked_contents = rerank_documents(query, doc_contents, top_n=5)
            logfire.info("Reranking complete. Kept top 5 most relevant chunks.")
            
        formatted_docs = []

        for i, doc in enumerate(reranked_contents, 1):
            formatted_docs.append(
            f"Document {i}\n{doc}"
                    )
    
    return "\n\n".join(formatted_docs)