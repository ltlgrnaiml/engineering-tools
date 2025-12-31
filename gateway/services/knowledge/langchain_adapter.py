"""Langchain Adapter - DISC-003 decision.

Wrap Knowledge Archive for Langchain integration.
"""

from typing import Any

try:
    from langchain_core.callbacks import CallbackManagerForRetrieverRun
    from langchain_core.documents import Document as LCDocument
    from langchain_core.retrievers import BaseRetriever
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    BaseRetriever = object
    LCDocument = None



if LANGCHAIN_AVAILABLE:
    class KnowledgeRetriever(BaseRetriever):
        """Langchain-compatible retriever for Knowledge Archive."""

        search_service: Any = None
        embedding_service: Any = None
        top_k: int = 10
        use_embeddings: bool = False

        class Config:
            arbitrary_types_allowed = True

        def _get_relevant_documents(
            self,
            query: str,
            *,
            run_manager: CallbackManagerForRetrieverRun | None = None
        ) -> list[LCDocument]:
            """Retrieve relevant documents for query."""
            # Generate query embedding if service available
            query_vector = None
            if self.use_embeddings and self.embedding_service:
                result = self.embedding_service.embed(query)
                query_vector = result.vector

            # Search using hybrid search
            results = self.search_service.hybrid_search(
                query,
                query_vector=query_vector,
                top_k=self.top_k
            )

            # Convert to Langchain Document format
            return [
                LCDocument(
                    page_content=r.snippet,
                    metadata={
                        "source": r.doc_id,
                        "title": r.title,
                        "score": r.score,
                        "doc_type": r.doc_type
                    }
                )
                for r in results
            ]
else:
    class KnowledgeRetriever:
        """Stub when langchain not available."""
        def __init__(self, **kwargs):
            raise ImportError("langchain_core required. Install with: pip install langchain-core")
