"""
Interactive Command-Line Application (No Gradio Dependency) for:
Patient Record Simplifier & Health Companion Agent.

Allows patients/users to:
1. Select sample documents or enter custom PDF/text files.
2. Automatically run simplification, reference range flagging, and specialist finder ON INGESTION.
3. Ask follow-up questions interactively via document-level RAG.
"""

import sys
import os
import json

# Fix Windows console UTF-8 printing
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.sample_data import (
    SAMPLE_LAB_REPORT_DIABETES_LIPIDS,
    SAMPLE_DISCHARGE_SUMMARY_CARDIAC,
    SAMPLE_PRESCRIPTION_CLINICAL_NOTE,
    SAMPLE_DOCUMENTS
)
from src.document_processor import SessionDocumentProcessor
from src.agent import HealthCompanionAgent, MANDATORY_CLINICAL_DISCLAIMER


def print_banner():
    print("=" * 72)
    print("      HEALTH COMPANION AGENT -- PATIENT RECORD SIMPLIFIER      ")
    print("             (CLI TERMINAL EDITION - NO GRADIO REQUIRED)       ")
    print("=" * 72)
    print("NOTICE:", MANDATORY_CLINICAL_DISCLAIMER)
    print("-" * 72)


def display_ingestion_report(res: dict):
    print("\n" + "=" * 72)
    print("         AUTOMATIC ON-INGESTION REPORT & SPECIALIST CARE PLAN      ")
    print("=" * 72)
    print(res["report_card_markdown"])
    print("=" * 72 + "\n")


def interactive_cli():
    agent = HealthCompanionAgent()
    processor = SessionDocumentProcessor()

    print_banner()
    
    while True:
        print("\n--- SELECT INPUT DOCUMENT ---")
        print("1. Sample Lab Report (Diabetes & Lipid Panel)")
        print("2. Sample Discharge Summary (Cardiac & Hypertension)")
        print("3. Sample Prescription & Clinical Visit Note")
        print("4. Provide Custom File Path (PDF or TXT)")
        print("5. Paste Custom Text Directly")
        print("6. Exit")
        
        choice = input("\nEnter choice (1-6): ").strip()

        if choice == "6":
            print("Exiting Health Companion. Stay healthy!")
            break

        doc_text = ""
        if choice == "1":
            doc_text = SAMPLE_LAB_REPORT_DIABETES_LIPIDS
            print("\n[INFO] Loaded Sample Lab Report.")
        elif choice == "2":
            doc_text = SAMPLE_DISCHARGE_SUMMARY_CARDIAC
            print("\n[INFO] Loaded Sample Discharge Summary.")
        elif choice == "3":
            doc_text = SAMPLE_PRESCRIPTION_CLINICAL_NOTE
            print("\n[INFO] Loaded Sample Prescription.")
        elif choice == "4":
            file_path = input("Enter path to PDF or TXT file: ").strip().strip('"')
            if not os.path.exists(file_path):
                print(f"[ERROR] File not found: {file_path}")
                continue
            doc_text = processor.load_document(file_path)
            print(f"\n[INFO] Successfully loaded document from '{file_path}'")
        elif choice == "5":
            print("Paste raw text below (press Enter twice or type 'EOF' on a new line when done):")
            lines = []
            while True:
                line = input()
                if line.strip() == "EOF":
                    break
                lines.append(line)
                if len(lines) > 1 and lines[-1] == "" and lines[-2] == "":
                    break
            doc_text = "\n".join(lines).strip()
            if not doc_text:
                print("[ERROR] No text entered.")
                continue
        else:
            print("[ERROR] Invalid choice, please enter 1-6.")
            continue

        # AUTOMATIC ON-INGESTION PIPELINE EXECUTION
        print("\n[AGENT] Ingesting document...")
        print("[AGENT] Executing Record Simplification & Flagging Tool...")
        print("[AGENT] Executing Specialist & Department Finder Tool...")
        
        res = agent.process_document_ingestion(doc_text, processor)
        display_ingestion_report(res)

        # INTERACTIVE FOLLOW-UP CHAT LOOP
        print("\n--- INTERACTIVE Q&A SESSION (Scoped to Uploaded Record) ---")
        print("Type your question below (or type 'new' to select another document, 'exit' to quit):")
        
        while True:
            question = input("\nPatient Q: ").strip()
            if not question:
                continue
            if question.lower() in ["exit", "quit"]:
                sys.exit(0)
            if question.lower() in ["new", "menu", "back"]:
                break

            print("\n[AGENT RAG RETRIEVAL & SYNTHESIS]:")
            answer = agent.answer_followup_question(question, processor)
            print("-" * 60)
            print(answer)
            print("-" * 60)


if __name__ == "__main__":
    interactive_cli()
