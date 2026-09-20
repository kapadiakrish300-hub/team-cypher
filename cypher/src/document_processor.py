"""
Document Processor for Patient Record Simplifier & Health Companion Agent.
Handles document extraction (PDF/text), section-aware text splitting, vector store generation,
and session-scoped retriever creation.
"""

import os
import uuid
import zlib
from typing import List, Tuple, Dict, Any, Optional
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

# ---------------------------------------------------------------------------
# Ultra-Fast, Zero-Dependency Embeddings (Deterministic Vectorizer)
# ---------------------------------------------------------------------------
class FastLocalEmbeddings(Embeddings):
    """
    Lightweight, deterministic local embeddings using character & word n-grams
    to ensure instant RAG retrieval without external API or heavy model loading delays.
    """
    def __init__(self, dim: int = 128):
        self.dim = dim

    def _embed_text(self, text: str) -> List[float]:
        vec = [0.0] * self.dim
        tokens = text.lower().split()
        for token in tokens:
            idx = zlib.crc32(token.encode('utf-8')) % self.dim
            vec[idx] += 1.0
        norm = sum(v * v for v in vec) ** 0.5
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._embed_text(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        return self._embed_text(text)


# Cached embeddings instance
_embeddings_instance = None

def get_embeddings():
    global _embeddings_instance
    if _embeddings_instance is None:
        use_hf = os.getenv("USE_HUGGINGFACE_EMBEDDINGS", "false").lower() == "true"
        if use_hf:
            try:
                from langchain_huggingface import HuggingFaceEmbeddings
                print("[DocumentProcessor] Loading HuggingFace embeddings...")
                _embeddings_instance = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2",
                    model_kwargs={"device": "cpu"}
                )
            except Exception as e:
                print(f"[DocumentProcessor] HuggingFace fallback: {e}")
                _embeddings_instance = FastLocalEmbeddings()
        else:
            _embeddings_instance = FastLocalEmbeddings()
    return _embeddings_instance


class SessionDocumentProcessor:
    """
    Manages session-scoped ingestion, chunking, and vector retrieval for a single patient record.
    """

    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.vector_store = None
        self.retriever = None
        self.raw_text: str = ""
        self.chunks: List[Document] = []

    def load_document(self, file_path_or_text: str) -> str:
        """
        Loads document from a file path (PDF/TXT) or accepts raw text string directly.
        """
        if isinstance(file_path_or_text, str) and os.path.exists(file_path_or_text):
            ext = os.path.splitext(file_path_or_text)[1].lower()
            if ext == ".pdf":
                try:
                    loader = PyPDFLoader(file_path_or_text)
                    docs = loader.load()
                    self.raw_text = "\n\n".join([doc.page_content for doc in docs])
                except Exception as e:
                    print(f"[DocumentProcessor] PyPDFLoader warning: {e}")
                    with open(file_path_or_text, "r", encoding="utf-8", errors="ignore") as f:
                        self.raw_text = f.read()
            else:
                with open(file_path_or_text, "r", encoding="utf-8", errors="ignore") as f:
                    self.raw_text = f.read()
        else:
            self.raw_text = str(file_path_or_text or "")

        return self.raw_text

    def create_section_aware_chunks(self, text: str) -> List[Document]:
        """
        Chunks medical records by section boundaries so lab values remain coupled
        with their reference ranges and clinical interpretations.
        """
        text_splitter = RecursiveCharacterTextSplitter(
            separators=[
                "\n\nSECTION:",
                "\nSECTION:",
                "\n\n",
                "-----------------------------------------------------------------------------",
                "\n- ",
                "\n",
                "; "
            ],
            chunk_size=500,
            chunk_overlap=80,
            length_function=len,
            is_separator_regex=False
        )

        raw_docs = [Document(page_content=text, metadata={"session_id": self.session_id})]
        self.chunks = text_splitter.split_documents(raw_docs)
        return self.chunks

    def build_vector_store(self, text: str):
        """
        Builds a session-isolated InMemoryVectorStore for retrieval-augmented generation.
        """
        self.raw_text = text
        chunks = self.create_section_aware_chunks(text)
        embeddings = get_embeddings()

        from langchain_core.vectorstores import InMemoryVectorStore
        self.vector_store = InMemoryVectorStore.from_documents(chunks, embeddings)
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})

        return self.retriever

    def build_vector_index(self, text: str):
        """
        Alias for build_vector_store.
        """
        return self.build_vector_store(text)

    def retrieve_context(self, query: str) -> List[Document]:
        """
        Retrieves top 3 relevant chunks for a follow-up question.
        """
        if not self.retriever:
            return self.chunks[:3]
        try:
            return self.retriever.invoke(query)
        except Exception as e:
            print(f"[DocumentProcessor] Retrieval warning: {e}")
            return self.chunks[:3]

    def answer_question(self, query: str) -> str:
        """
        Answers a follow-up question using retrieved context.
        """
        docs = self.retrieve_context(query)
        context = "\n\n".join([f"[Excerpt {i+1}]: {doc.page_content}" for i, doc in enumerate(docs)])
        from src.rag import MANDATORY_CLINICAL_DISCLAIMER
        return (
            f"{MANDATORY_CLINICAL_DISCLAIMER}\n\n"
            f"Based on your uploaded record excerpts:\n\n{context}\n\n"
            f"**Information regarding '{query}'**:\n"
            f"The excerpts above from your uploaded record contain the relevant details. "
            f"Please share these notes directly with your healthcare provider during your visit."
        )
