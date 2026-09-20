"""
Agent & Orchestration Pipeline for Patient Record Simplifier & Health Companion Agent.
Configures ChatOllama with fallback synthesis, executes automatic on-ingestion tool calls,
and handles context-bounded follow-up Q&A.
"""

import os
from typing import Dict, Any, List, Tuple
from src.tools import (
    record_simplification_and_flagging_tool,
    specialist_department_finder_tool,
    adzuna_specialist_search_tool
)
from src.rag import RAGEngine, MANDATORY_CLINICAL_DISCLAIMER
from src.llm import get_llm_model


class HealthCompanionAgent:
    """
    Agent that processes uploaded medical documents immediately upon ingestion,
    runs simplification, range flagging, specialist lookup, and Adzuna API search automatically,
    and provides grounded RAG Q&A for follow-up patient questions.
    """

    def __init__(self, model_name: str = "qwen2.5:0.5b", ollama_base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.ollama_base_url = ollama_base_url
        self.llm = get_llm_model(model_name, ollama_base_url)

    def process_document_ingestion(self, document_content: str, rag_engine: RAGEngine) -> Dict[str, Any]:
        """
        CORE REQUIRED BEHAVIOR:
        Runs automatically the moment a document is ingested (before patient asks any question).
        1. Indexes record into session vector store.
        2. Executes deterministic simplification & flagging tool.
        3. Executes deterministic specialist department finder tool.
        4. Executes Adzuna API specialist opportunity search tool.
        5. Synthesizes plain-language summary & report card.
        """
        # Step 1: Load and build session vector store for RAG
        raw_text = rag_engine.load_document(document_content)
        rag_engine.build_vector_index(raw_text)

        # Step 2: Automatic execution of Simplification & Flagging Tool
        simplification_result = record_simplification_and_flagging_tool.invoke({"record_text": raw_text})

        # Step 3: Automatic execution of Specialist / Department Finder Tool
        flagged_items = simplification_result.get("flagged_items", [])
        specialist_result = specialist_department_finder_tool.invoke({"flagged_items": flagged_items})

        # Step 4: Automatic Adzuna API Search for Recommended Specialties
        adzuna_results = {}
        for rec in specialist_result.get("recommendations", []):
            spec_title = rec.get("specialist", "")
            if spec_title:
                adz_res = adzuna_specialist_search_tool.invoke({"query": spec_title})
                adzuna_results[spec_title] = adz_res

        # Step 5: Format Markdown Report Card for display
        report_card = self._format_ingestion_report_card(
            raw_text=raw_text,
            simplification_result=simplification_result,
            specialist_result=specialist_result,
            adzuna_results=adzuna_results
        )

        return {
            "session_id": rag_engine.session_id,
            "raw_text": raw_text,
            "simplification_result": simplification_result,
            "specialist_result": specialist_result,
            "adzuna_results": adzuna_results,
            "report_card_markdown": report_card,
            "disclaimer": MANDATORY_CLINICAL_DISCLAIMER
        }

    def _format_ingestion_report_card(
        self,
        raw_text: str,
        simplification_result: Dict[str, Any],
        specialist_result: Dict[str, Any],
        adzuna_results: Dict[str, Any]
    ) -> str:
        """
        Formats the automatic ingestion output into a structured, readable markdown report.
        """
        summary = simplification_result.get("plain_language_summary", "")
        flagged = simplification_result.get("flagged_items", [])
        jargon = simplification_result.get("jargon_translations", [])
        rx_warns = simplification_result.get("prescription_warnings", [])
        recs = specialist_result.get("recommendations", [])

        md = []
        md.append(f"> {MANDATORY_CLINICAL_DISCLAIMER}\n")
        md.append("## 📋 Plain-Language Clinical Summary")
        md.append(f"{summary}\n")

        # Jargon Translations Table
        if jargon:
            md.append("### 🔍 Medical Terminology Glossary")
            md.append("| Medical Term | Plain Language Explanation |")
            md.append("|--------------|---------------------------|")
            for item in jargon:
                md.append(f"| **{item['jargon']}** | {item['plain_translation']} |")
            md.append("")

        # Flagged Abnormal Values Section
        if flagged:
            md.append("### 🚨 Flagged Clinical Findings (Out of Range)")
            md.append("| Parameter | Observed Value | Normal Reference Range | Status | Clinical Context & Guidance |")
            md.append("|-----------|----------------|------------------------|--------|----------------------------|")
            for item in flagged:
                md.append(
                    f"| **{item['parameter']}** | `{item['value']}` | `{item['reference_range']}` | "
                    f"**{item['status']}** | {item['explanation']} |"
                )
            md.append("")
        else:
            md.append("### ✅ Standard Target Ranges")
            md.append("All evaluated lab tests fell within normal baseline target ranges.\n")

        # Prescription / Medication Warnings
        if rx_warns:
            md.append("### 💊 Medication Notes & Precautions")
            for warn in rx_warns:
                md.append(f"- {warn}")
            md.append("")

        # Specialist & Department Recommendations
        md.append("### 🩺 Recommended Specialists & Care Plan")
        if recs:
            for rec in recs:
                spec_name = rec['specialist']
                md.append(f"#### Specialist: **{spec_name}** ({rec['department']})")
                md.append(f"- **Recommended Timeline**: `{rec['urgency']}`")
                md.append(f"- **Care Focus**: {rec['reason']}")
                if rec.get("associated_parameters"):
                    md.append(f"- **Trigger Parameters**: {', '.join(rec['associated_parameters'])}")
                md.append("- **Suggested Questions for Your Doctor**:")
                for q in rec["doctor_questions"]:
                    md.append(f"  - *\"{q}\"*")

                # Adzuna API Listings Section
                adz = adzuna_results.get(spec_name, {})
                if adz.get("status") == "SUCCESS" and adz.get("listings"):
                    md.append(f"- **Adzuna API Healthcare Listings for {spec_name}**:")
                    for listing in adz["listings"]:
                        md.append(f"  - [{listing['title']}]({listing.get('url', '#')}) - {listing.get('company', '')} ({listing.get('location', '')})")
                elif adz.get("sample_listings"):
                    md.append(f"- **Adzuna API Directory (Sample)**:")
                    for listing in adz["sample_listings"]:
                        md.append(f"  - *{listing['title']}* - {listing['department']} ({listing['location']})")
                md.append("")
        else:
            md.append("Standard routine follow-up with your Primary Care Physician is recommended.\n")

        return "\n".join(md)

    def answer_followup_question(self, question: str, rag_engine: RAGEngine) -> str:
        """
        Answers follow-up questions from the patient strictly grounded in their specific record using RAG.
        """
        return rag_engine.answer_question(question)
