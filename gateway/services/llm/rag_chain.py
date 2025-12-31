"""RAG Chain - Knowledge Archive Integration with LangChain.

Provides a RAG chain that:
1. Retrieves context from Knowledge Archive
2. Sanitizes content before LLM exposure
3. Generates responses using xAI (Grok)
4. Traces everything in Phoenix

Usage:
    from gateway.services.llm import create_rag_chain
    
    chain = create_rag_chain()
    response = chain.invoke("What ADRs relate to data aggregation?")
"""

import logging
from typing import Any
from dataclasses import dataclass

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

from gateway.services.llm.xai_langchain import get_xai_chat_model

logger = logging.getLogger(__name__)


@dataclass
class RAGResponse:
    """Response from RAG chain.
    
    Attributes:
        answer: The generated answer.
        context: The retrieved context used.
        sources: List of source document IDs.
    """
    answer: str
    context: str
    sources: list[str]


# Default RAG prompt template
RAG_PROMPT_TEMPLATE = """You are a helpful assistant for the Engineering Tools platform.
Use the following context from the knowledge archive to answer the question.
If you don't know the answer based on the context, say so.

Context:
{context}

Question: {question}

Answer:"""


class RAGChain:
    """RAG Chain with Knowledge Archive integration.
    
    This chain retrieves relevant documents from the Knowledge Archive,
    sanitizes them, and uses xAI to generate responses.
    
    Attributes:
        llm: The LangChain chat model.
        retriever: Function to retrieve context.
        sanitizer: Function to sanitize content.
    """
    
    def __init__(
        self,
        model: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        retriever: Any = None,
        sanitizer: Any = None,
    ):
        """Initialize RAG chain.
        
        Args:
            model: xAI model to use.
            temperature: Sampling temperature (lower for factual).
            max_tokens: Maximum response tokens.
            retriever: Custom retriever function. Defaults to Knowledge Archive.
            sanitizer: Custom sanitizer function. Defaults to Knowledge Archive sanitizer.
        """
        self.llm = get_xai_chat_model(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        self._retriever = retriever
        self._sanitizer = sanitizer
        self._chain = None
        self._last_context = ""
        self._last_sources: list[str] = []
    
    def _get_retriever(self):
        """Get or create the retriever."""
        if self._retriever is not None:
            return self._retriever
        
        # Try to use Knowledge Archive
        try:
            from gateway.services.knowledge import get_context_builder
            builder = get_context_builder()
            
            def retrieve(query: str) -> str:
                result = builder.build_context(query, max_tokens=2000)
                self._last_context = result.context
                self._last_sources = [c.doc_id for c in result.chunks]
                return result.context
            
            self._retriever = retrieve
            return self._retriever
        except ImportError:
            logger.warning("Knowledge Archive not available, using dummy retriever")
            
            def dummy_retrieve(query: str) -> str:
                self._last_context = f"[No context available for: {query}]"
                self._last_sources = []
                return self._last_context
            
            self._retriever = dummy_retrieve
            return self._retriever
    
    def _get_sanitizer(self):
        """Get or create the sanitizer."""
        if self._sanitizer is not None:
            return self._sanitizer
        
        # Try to use Knowledge Archive sanitizer
        try:
            from gateway.services.knowledge.sanitizer import Sanitizer
            sanitizer = Sanitizer()
            self._sanitizer = lambda text: sanitizer.sanitize(text).content
            return self._sanitizer
        except ImportError:
            logger.warning("Sanitizer not available, using passthrough")
            self._sanitizer = lambda text: text
            return self._sanitizer
    
    def _build_chain(self):
        """Build the LangChain pipeline."""
        if self._chain is not None:
            return self._chain
        
        retriever = self._get_retriever()
        sanitizer = self._get_sanitizer()
        
        prompt = ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)
        
        # Build chain: retrieve -> sanitize -> prompt -> llm -> parse
        self._chain = (
            {
                "context": RunnableLambda(lambda x: sanitizer(retriever(x["question"]))),
                "question": RunnablePassthrough() | RunnableLambda(lambda x: x["question"]),
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        return self._chain
    
    def invoke(self, question: str) -> RAGResponse:
        """Invoke the RAG chain.
        
        Args:
            question: The question to answer.
            
        Returns:
            RAGResponse with answer, context, and sources.
        """
        chain = self._build_chain()
        answer = chain.invoke({"question": question})
        
        return RAGResponse(
            answer=answer,
            context=self._last_context,
            sources=self._last_sources,
        )
    
    async def ainvoke(self, question: str) -> RAGResponse:
        """Async invoke the RAG chain.
        
        Args:
            question: The question to answer.
            
        Returns:
            RAGResponse with answer, context, and sources.
        """
        chain = self._build_chain()
        answer = await chain.ainvoke({"question": question})
        
        return RAGResponse(
            answer=answer,
            context=self._last_context,
            sources=self._last_sources,
        )


def create_rag_chain(
    model: str | None = None,
    temperature: float = 0.3,
    **kwargs: Any,
) -> RAGChain:
    """Create a RAG chain with Knowledge Archive integration.
    
    Args:
        model: xAI model to use.
        temperature: Sampling temperature.
        **kwargs: Additional RAGChain arguments.
        
    Returns:
        Configured RAGChain instance.
        
    Example:
        chain = create_rag_chain()
        response = chain.invoke("What is ADR-0005 about?")
        print(response.answer)
        print(f"Sources: {response.sources}")
    """
    return RAGChain(model=model, temperature=temperature, **kwargs)
