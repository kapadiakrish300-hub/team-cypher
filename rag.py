"""
Top-level Wrapper for RAG Engine & Document Indexing.
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from src.rag import RAGEngine, FastLocalEmbeddings, MANDATORY_CLINICAL_DISCLAIMER

if __name__ == "__main__":
    print("=== RAG ENGINE MODULE CHECK ===")
    rag = RAGEngine(session_id="rag_demo_session")
    sample_text = "Fasting Blood Glucose: 165 mg/dL. Patient prescribed Lisinopril 20 mg PO daily."
    rag.build_vector_index(sample_text)
    print("Indexed Chunks:", len(rag.chunks))
    answer = rag.answer_question("What medications am I taking?")
    print("RAG Test Answer:")
    print("-" * 50)
    print(answer)
    print("-" * 50)
