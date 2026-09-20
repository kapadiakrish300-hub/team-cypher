"""
RAG Engine Module for Patient Record Simplifier & Health Companion Agent.
Handles document extraction, section-aware text splitting, vector store retrieval,
and context-grounded Q&A synthesis.
"""

import os
import uuid
import zlib
from typing import List, Dict, Any, Optional
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from src.llm import get_llm_model

MANDATORY_CLINICAL_DISCLAIMER = (
    "⚠️ **CLINICAL NOTICE**: Educational summaries and doctor preparation guidance. "
    "Not a medical diagnosis or medical advice."
)


class FastLocalEmbeddings(Embeddings):
    """
    Lightweight, deterministic local embeddings for instant RAG vector indexing.
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


class RAGEngine:
    """
    Session-scoped RAG Engine for indexing patient documents and executing grounded retrieval.
    """

    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.raw_text: str = ""
        self.chunks: List[Document] = []
        self.vector_store = None
        self.retriever = None

    def load_document(self, file_path_or_text: str) -> str:
        """
        Loads PDF/TXT document or string text into memory.
        """
        if isinstance(file_path_or_text, str) and os.path.exists(file_path_or_text):
            ext = os.path.splitext(file_path_or_text)[1].lower()
            if ext == ".pdf":
                try:
                    loader = PyPDFLoader(file_path_or_text)
                    docs = loader.load()
                    self.raw_text = "\n\n".join([doc.page_content for doc in docs])
                except Exception as e:
                    with open(file_path_or_text, "r", encoding="utf-8", errors="ignore") as f:
                        self.raw_text = f.read()
            else:
                with open(file_path_or_text, "r", encoding="utf-8", errors="ignore") as f:
                    self.raw_text = f.read()
        else:
            self.raw_text = str(file_path_or_text or "")

        return self.raw_text

    def chunk_by_section(self, text: str) -> List[Document]:
        """
        Section-aware chunking so lab values stay attached to reference ranges.
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
            length_function=len
        )
        raw_docs = [Document(page_content=text, metadata={"session_id": self.session_id})]
        self.chunks = text_splitter.split_documents(raw_docs)
        return self.chunks

    def build_vector_index(self, text: str):
        """
        Builds vector store retriever for RAG.
        """
        self.raw_text = text
        chunks = self.chunk_by_section(text)
        embeddings = FastLocalEmbeddings()

        from langchain_core.vectorstores import InMemoryVectorStore
        self.vector_store = InMemoryVectorStore.from_documents(chunks, embeddings)
        self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
        return self.retriever

    def build_vector_store(self, text: str):
        """
        Alias for build_vector_index for backward compatibility.
        """
        return self.build_vector_index(text)

    def retrieve(self, query: str) -> List[Document]:
        """
        Retrieves top 3 relevant chunks.
        """
        if not self.retriever:
            return self.chunks[:3]
        return self.retriever.invoke(query)

    def answer_question(self, question: str) -> str:
        """
        Answers follow-up question grounded strictly in retrieved document context.
        """
        retrieved = self.retrieve(question)
        context = "\n\n".join([f"[Excerpt {i+1}]: {doc.page_content}" for i, doc in enumerate(retrieved)])

        llm = get_llm_model()
        if llm:
            try:
                from langchain_core.messages import SystemMessage, HumanMessage
                system_prompt = (
                    "You are an empathetic Medical Document Assistant. "
                    "Answer the user's question based strictly on these document excerpts:\n"
                    f"{context}\n\n"
                    "RULES: Never diagnose diseases. Explain in plain English. Recommend doctor consultation."
                )
                response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=question)])
                ans = response.content if hasattr(response, 'content') else str(response)
                return f"{MANDATORY_CLINICAL_DISCLAIMER}\n\n{ans}\n\n---\n**Context Excerpts**:\n{context}"
            except Exception as e:
                print(f"[RAG] LLM invoke fallback: {e}")

        # Fallback Synthesis
        return (
            f"{MANDATORY_CLINICAL_DISCLAIMER}\n\n"
            f"Based on your uploaded record excerpts:\n\n{context}\n\n"
            f"**Information regarding '{question}'**:\n"
            f"The excerpts above from your uploaded record contain the relevant details. "
            f"Please share these notes directly with your healthcare provider during your visit."
        )
