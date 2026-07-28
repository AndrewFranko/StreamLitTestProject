"""
RAG Pipeline for MCP Ticket Server

Uses LangChain to index ticket descriptions and find similar past tickets
when creating new ones. Helps identify related issues and reduce duplicates.

Integrates with LangSmith for tracing and visualization.
"""

import json
import os
from typing import List, Dict, Any, Optional
from langchain_text_splitters import CharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.callbacks import tracing_v2_enabled_if_api_key_set
import logging

# Setup LangSmith tracing
try:
    from src.langsmith_config import LANGSMITH_ENABLED
except ImportError:
    LANGSMITH_ENABLED = False

logger = logging.getLogger(__name__)


class TicketRAGPipeline:
    """RAG pipeline for searching similar tickets."""

    def __init__(self, tickets_path: str = None):
        """Initialize RAG pipeline with ticket data."""
        self.tickets_path = tickets_path or "c:/StreamLit/data/maintenance_tickets.json"
        self.vectorstore = None
        self.embeddings = None
        self._initialize()

    def _initialize(self):
        """Load tickets and create vector store."""
        try:
            # Initialize embeddings
            self.embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": False}
            )

            # Load and index tickets
            tickets = self._load_tickets()
            if tickets:
                self._build_vectorstore(tickets)
                logger.info(f"✓ RAG Pipeline initialized with {len(tickets)} tickets")
            else:
                logger.warning("No tickets found to index")
        except Exception as e:
            logger.error(f"Failed to initialize RAG pipeline: {e}")
            self.embeddings = None

    def _load_tickets(self) -> List[Dict[str, Any]]:
        """Load tickets from JSON file."""
        try:
            if os.path.exists(self.tickets_path):
                with open(self.tickets_path) as f:
                    return json.load(f) or []
            return []
        except Exception as e:
            logger.error(f"Failed to load tickets: {e}")
            return []

    def _build_vectorstore(self, tickets: List[Dict[str, Any]]):
        """Build FAISS vector store from ticket data."""
        try:
            # Create documents from tickets
            documents = []
            for ticket in tickets:
                doc_content = f"""
Ticket ID: {ticket.get('ticket_id', 'N/A')}
Machine: {ticket.get('machine_id', 'N/A')}
Error Code: {ticket.get('error_code', 'N/A')}
Severity: {ticket.get('severity') or ticket.get('priority', 'N/A')}
Description: {ticket.get('description', '')}
Status: {ticket.get('status', 'N/A')}
"""
                doc = Document(
                    page_content=doc_content,
                    metadata={
                        "ticket_id": ticket.get("ticket_id"),
                        "machine_id": ticket.get("machine_id"),
                        "error_code": ticket.get("error_code"),
                        "severity": ticket.get("severity") or ticket.get("priority")
                    }
                )
                documents.append(doc)

            # Split documents
            splitter = CharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50,
                separator="\n"
            )
            split_docs = splitter.split_documents(documents)

            # Create vector store
            if split_docs:
                self.vectorstore = FAISS.from_documents(split_docs, self.embeddings)
                logger.info(f"✓ Vector store built with {len(split_docs)} document chunks")
        except Exception as e:
            logger.error(f"Failed to build vector store: {e}")

    def find_similar_tickets(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Find similar past tickets using semantic search.

        This method is traced by LangSmith if configured.
        """
        if not self.vectorstore or not self.embeddings:
            return []

        try:
            # Search similar documents (traced by LangChain)
            results = self.vectorstore.similarity_search_with_score(query, k=k)

            # Extract unique ticket IDs
            seen_tickets = set()
            similar_tickets = []

            for doc, score in results:
                ticket_id = doc.metadata.get("ticket_id")
                if ticket_id and ticket_id not in seen_tickets:
                    seen_tickets.add(ticket_id)
                    similar_tickets.append({
                        "ticket_id": ticket_id,
                        "machine_id": doc.metadata.get("machine_id"),
                        "error_code": doc.metadata.get("error_code"),
                        "severity": doc.metadata.get("severity"),
                        "similarity_score": float(score)
                    })

            return similar_tickets[:k]
        except Exception as e:
            logger.error(f"Failed to search similar tickets: {e}")
            return []

    def refresh(self):
        """Refresh the vector store with latest tickets."""
        self._initialize()


# Global RAG pipeline instance
_rag_pipeline: Optional[TicketRAGPipeline] = None


def get_rag_pipeline() -> TicketRAGPipeline:
    """Get or create the global RAG pipeline instance."""
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = TicketRAGPipeline()
    return _rag_pipeline


def find_similar_tickets(query: str, k: int = 3) -> List[Dict[str, Any]]:
    """Find similar tickets using RAG pipeline."""
    pipeline = get_rag_pipeline()
    return pipeline.find_similar_tickets(query, k=k)


def refresh_rag_pipeline():
    """Refresh RAG pipeline when tickets change."""
    pipeline = get_rag_pipeline()
    pipeline.refresh()
