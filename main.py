"""
Direct Command-Line Pipeline Runner (No Gradio Dependency) for:
Patient Record Simplifier & Health Companion Agent.

Usage:
  python main.py                     # Runs sample lab report automatically
  python main.py <path_to_file.pdf>  # Ingests file and outputs plain-language summary & specialist care plan
"""

import sys
import os

# Fix Windows console UTF-8 printing
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.sample_data import SAMPLE_LAB_REPORT_DIABETES_LIPIDS
from src.document_processor import SessionDocumentProcessor
from src.agent import HealthCompanionAgent


def main():
    agent = HealthCompanionAgent()
    processor = SessionDocumentProcessor()

    input_source = SAMPLE_LAB_REPORT_DIABETES_LIPIDS
    if len(sys.argv) > 1:
        target_path = sys.argv[1]
        if os.path.exists(target_path):
            input_source = target_path
            print(f"[INFO] Ingesting custom file: {target_path}")
        else:
            print(f"[WARNING] File '{target_path}' not found. Using default sample lab report.")
    else:
        print("[INFO] No file specified. Ingesting default Sample Lab Report (Diabetes & Lipids)...")

    # Run Automatic Ingestion Pipeline
    res = agent.process_document_ingestion(input_source, processor)

    print("\n" + "=" * 76)
    print("      PATIENT RECORD SIMPLIFIER -- AUTOMATIC ON-INGESTION REPORT     ")
    print("=" * 76)
    print(res["report_card_markdown"])
    print("=" * 76)

    # Optional Sample Question Demonstration
    sample_question = "What specialists do I need to see and why?"
    print(f"\n[DEMO] Follow-up Question: '{sample_question}'")
    answer = agent.answer_followup_question(sample_question, processor)
    print("-" * 76)
    print(answer)
    print("-" * 76)


if __name__ == "__main__":
    main()
