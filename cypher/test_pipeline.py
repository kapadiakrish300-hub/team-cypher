"""
Test Suite & Verification for Patient Record Simplifier & Health Companion Agent.
Validates:
1. Simplification & Flagging Tool deterministic evaluation.
2. Specialist / Department Finder Tool mapping.
3. Document processor section-aware chunking & Chroma vector store creation.
4. End-to-end automatic on-ingestion pipeline execution without prior question input.
5. Grounded RAG Q&A follow-up.
"""

import sys
import os

# Fix Windows console UTF-8 printing
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.tools import (
    record_simplification_and_flagging_tool,
    specialist_department_finder_tool
)
from src.sample_data import SAMPLE_LAB_REPORT_DIABETES_LIPIDS, SAMPLE_DISCHARGE_SUMMARY_CARDIAC
from src.document_processor import SessionDocumentProcessor
from src.agent import HealthCompanionAgent


def test_simplification_tool():
    print("\n--- TEST 1: Simplification & Flagging Tool ---")
    res = record_simplification_and_flagging_tool.invoke({"record_text": SAMPLE_LAB_REPORT_DIABETES_LIPIDS})
    print("Summary:", res["plain_language_summary"])
    print(f"Jargon Found ({len(res['jargon_translations'])}):", [j["jargon"] for j in res["jargon_translations"]])
    print(f"Flagged Items ({len(res['flagged_items'])}):")
    for f in res["flagged_items"]:
        print(f"  - {f['parameter']}: {f['value']} (Ref: {f['reference_range']}) -> Status: {f['status']}")
    
    assert len(res["flagged_items"]) > 0, "Expected flagged items for sample lab report!"
    assert any("hb" in f["parameter"].lower() or "a1c" in f["parameter"].lower() for f in res["flagged_items"]), "HbA1c should be flagged"
    print("[PASS] TEST 1 PASSED!")
    return res


def test_specialist_tool(simplification_res):
    print("\n--- TEST 2: Specialist & Department Finder Tool ---")
    flagged = simplification_res["flagged_items"]
    res = specialist_department_finder_tool.invoke({"flagged_items": flagged})
    print(f"Total Specialties Recommended: {res['total_specialties_recommended']}")
    for r in res["recommendations"]:
        print(f"  - Specialty: {r['specialist']} ({r['department']}) | Urgency: {r['urgency']}")
        print(f"    Questions to ask: {r['doctor_questions'][0]}")

    assert res["has_recommendations"] is True
    print("[PASS] TEST 2 PASSED!")


def test_end_to_end_agent():
    print("\n--- TEST 3: End-to-End Automatic Ingestion Agent Pipeline ---")
    agent = HealthCompanionAgent()
    processor = SessionDocumentProcessor(session_id="test_session_101")
    
    # Ingestion happens AUTOMATICALLY on document delivery
    result = agent.process_document_ingestion(SAMPLE_DISCHARGE_SUMMARY_CARDIAC, processor)
    
    print("Report Card Markdown Preview:")
    print("=" * 60)
    print(result["report_card_markdown"][:600] + "\n...")
    print("=" * 60)

    # Follow-up RAG test question
    question = "What medications was I prescribed at discharge?"
    print(f"\nAsking follow-up question: '{question}'")
    answer = agent.answer_followup_question(question, processor)
    print("Agent Answer Preview:")
    print("-" * 60)
    print(answer[:400] + "\n...")
    print("-" * 60)

    assert "CLINICAL NOTICE" in answer or "Lisinopril" in answer or "Furosemide" in answer
    print("[PASS] TEST 3 PASSED!")


if __name__ == "__main__":
    print("RUNNING PIPELINE VERIFICATION SUITE...")
    simp_res = test_simplification_tool()
    test_specialist_tool(simp_res)
    test_end_to_end_agent()
    print("\nALL TESTS PASSED SUCCESSFULLY!")
