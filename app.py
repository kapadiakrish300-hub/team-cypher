"""
Gradio Web Application for Patient Record Simplifier & Health Companion Agent.
Clean, full-width dark theme interface (Agent Pipeline status sidebar removed for maximum clarity).
"""

import sys
import os

# Fix Windows console UTF-8 printing
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gradio as gr
import json
from src.sample_data import (
    SAMPLE_LAB_REPORT_DIABETES_LIPIDS,
    SAMPLE_DISCHARGE_SUMMARY_CARDIAC,
    SAMPLE_PRESCRIPTION_CLINICAL_NOTE,
    SAMPLE_DOCUMENTS
)
from src.document_processor import SessionDocumentProcessor
from src.agent import HealthCompanionAgent, MANDATORY_CLINICAL_DISCLAIMER

# Initialize Global Agent & Session Processor
agent = HealthCompanionAgent()
current_session_processor = SessionDocumentProcessor()

# Custom CSS for modern full-width dark cyber-medical theme
CUSTOM_CSS = """
body, .gradio-container {
    background-color: #090a0c !important;
    color: #e2e8f0 !important;
    font-family: -apple-system, BlinkMacSystemFont, "Inter", "Segoe UI", Roboto, sans-serif !important;
    max-width: 1400px !important;
    margin: 0 auto !important;
}

/* Header & Navigation Bar */
.brand-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #1e2330;
    padding-bottom: 16px;
    margin-bottom: 16px;
}

.brand-title {
    font-size: 1.75rem;
    font-weight: 800;
    letter-spacing: 0.5px;
    color: #ffffff;
    display: flex;
    align-items: center;
    gap: 12px;
}

.brand-badge {
    background: linear-gradient(135deg, #ff5500, #ff7700);
    color: #000000;
    font-size: 0.72rem;
    font-weight: 900;
    padding: 3px 10px;
    border-radius: 4px;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.status-pill {
    background: #141824;
    border: 1px solid #ff5500;
    color: #ffaa77;
    font-family: monospace;
    font-size: 0.8rem;
    padding: 6px 14px;
    border-radius: 20px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.status-dot {
    width: 8px;
    height: 8px;
    background-color: #ff5500;
    border-radius: 50%;
    box-shadow: 0 0 8px #ff5500;
}

/* Clinical Notice Banner */
.clinical-notice-bar {
    background: rgba(255, 85, 0, 0.08);
    border: 1px solid rgba(255, 85, 0, 0.4);
    border-radius: 6px;
    padding: 12px 18px;
    margin-bottom: 25px;
    color: #ffaa77;
    font-size: 0.88rem;
    font-family: monospace;
    letter-spacing: 0.3px;
    font-weight: 600;
}

/* Section Cards & Containers */
.hero-container {
    text-align: center;
    margin-bottom: 25px;
}

.hero-title {
    font-size: 2.5rem;
    font-weight: 800;
    color: #ffffff;
    margin-bottom: 8px;
}

.hero-subtitle {
    color: #94a3b8;
    font-size: 1.1rem;
    max-width: 800px;
    margin: 0 auto;
    line-height: 1.6;
}

.card-box {
    background: #11131a;
    border: 1px solid #1e2433;
    border-radius: 10px;
    padding: 24px;
    margin-bottom: 24px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
}

.card-title {
    font-family: monospace;
    font-weight: 700;
    color: #ff5500;
    letter-spacing: 1px;
    font-size: 1rem;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.cyber-btn {
    background: linear-gradient(135deg, #ff5500, #ff7700) !important;
    color: #000000 !important;
    font-weight: 800 !important;
    font-size: 1rem !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 12px 24px !important;
    transition: all 0.2s ease !important;
}

.cyber-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 15px rgba(255, 85, 0, 0.4) !important;
}

/* Table Formatting inside Markdown */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0;
}
th {
    background: #181d29;
    color: #ffaa77;
    text-align: left;
    padding: 12px;
    font-size: 0.9rem;
    border-bottom: 2px solid #ff5500;
}
td {
    padding: 12px;
    border-bottom: 1px solid #1e2433;
    font-size: 0.95rem;
}
"""

def process_document_pipeline(file_obj, pasted_text, selected_sample):
    """
    Automatic on-ingestion pipeline triggered immediately when document is submitted.
    """
    global current_session_processor
    current_session_processor = SessionDocumentProcessor()

    # Determine input text source
    doc_text = ""
    if file_obj is not None:
        doc_text = current_session_processor.load_document(file_obj.name)
    elif pasted_text and pasted_text.strip():
        doc_text = pasted_text.strip()
    elif selected_sample and selected_sample in SAMPLE_DOCUMENTS:
        doc_text = SAMPLE_DOCUMENTS[selected_sample]
    else:
        doc_text = SAMPLE_LAB_REPORT_DIABETES_LIPIDS

    # Run Automatic Ingestion Pipeline
    res = agent.process_document_ingestion(doc_text, current_session_processor)

    # Format JSON strings for Tools Audit
    simp_json = json.dumps(res["simplification_result"], indent=2)
    spec_json = json.dumps(res["specialist_result"], indent=2)

    return (
        res["report_card_markdown"],
        simp_json,
        spec_json,
        doc_text
    )


def handle_sample_click(sample_name):
    """
    Pre-fills sample and triggers automatic ingestion pipeline immediately.
    """
    text = SAMPLE_DOCUMENTS.get(sample_name, "")
    report_md, simp_j, spec_j, doc_t = process_document_pipeline(None, text, sample_name)
    return text, report_md, simp_j, spec_j


def handle_chat_question(question_text, chat_history):
    """
    Handles follow-up Q&A strictly grounded in the uploaded document using RAG.
    """
    if not question_text or not question_text.strip():
        return "", chat_history

    if chat_history is None:
        chat_history = []

    answer = agent.answer_followup_question(question_text, current_session_processor)
    chat_history.append((question_text, answer))
    return "", chat_history


# Build Gradio Blocks Application
with gr.Blocks(title="Patient Record Simplifier & Health Companion") as demo:
    
    # Top Header & Status Indicator
    gr.HTML(
        """
        <div class="brand-header">
            <div class="brand-title">
                HEALTH COMPANION <span class="brand-badge">SIMPLIFIER</span>
            </div>
            <div class="status-pill">
                <span class="status-dot"></span> DETERMINISTIC CLINICAL ENGINE ACTIVE
            </div>
        </div>
        <div class="clinical-notice-bar">
            // CLINICAL NOTICE: EDUCATIONAL SUMMARIES AND DOCTOR PREPARATION GUIDANCE. NOT A MEDICAL DIAGNOSIS OR MEDICAL ADVICE.
        </div>
        """
    )

    # Hero Intro Section
    gr.HTML(
        """
        <div class="hero-container">
            <div class="hero-title">Patient Record Simplifier</div>
            <div class="hero-subtitle">
                An intelligent clinical record simplifier that automatically parses uploaded lab reports, discharge summaries, 
                or prescriptions, translates medical jargon into plain language, flags out-of-range results, and maps appropriate specialists.
            </div>
        </div>
        """
    )

    # Full-Width Document Ingestion Card
    with gr.Group(elem_classes=["card-box"]):
        gr.HTML("<div class='card-title'>STEP 1: CHOOSE SAMPLE OR UPLOAD PATIENT DOCUMENT</div>")
        
        # Sample Quick-Select Buttons
        with gr.Row():
            btn_sample_lab = gr.Button("📋 Lab Report (Diabetes & Lipids)", variant="secondary")
            btn_sample_discharge = gr.Button("🏥 Discharge Summary (Cardiac)", variant="secondary")
            btn_sample_rx = gr.Button("💊 Prescription & Notes", variant="secondary")

        with gr.Tabs():
            with gr.Tab("📄 Upload File (PDF / TXT)"):
                file_input = gr.File(label="Upload Patient Document", file_types=[".pdf", ".txt"])
            with gr.Tab("✏️ Paste Raw Clinical Text"):
                text_input = gr.Textbox(
                    label="Clinical Document Text",
                    placeholder="Paste lab report, discharge summary, or prescription text here...",
                    lines=7,
                    value=SAMPLE_LAB_REPORT_DIABETES_LIPIDS
                )

        btn_ingest = gr.Button("🚀 INGEST RECORD & GENERATE PLAIN-LANGUAGE REPORT", elem_classes=["cyber-btn"])

    # Full-Width Immediate Automatic Report Card Output
    with gr.Group(elem_classes=["card-box"]):
        gr.HTML("<div class='card-title'>STEP 2: AUTOMATIC PLAIN-LANGUAGE SUMMARY & SPECIALIST ROUTING</div>")
        report_markdown = gr.Markdown(value="*Ingest a document above to generate plain language summary, flags, and specialist routing.*")

    # Full-Width Interactive Chat for Document Follow-up Q&A
    with gr.Group(elem_classes=["card-box"]):
        gr.HTML("<div class='card-title'>STEP 3: ASK FOLLOW-UP QUESTIONS ABOUT YOUR RECORD</div>")
        chatbot = gr.Chatbot(label="Health Companion Q&A Assistant", height=340)
        
        with gr.Row():
            question_input = gr.Textbox(
                show_label=False,
                placeholder="Ask a question about your uploaded record (e.g., 'What is HbA1c?' or 'What medications do I take?')...",
                scale=5
            )
            btn_ask = gr.Button("Ask Question", variant="primary", scale=1)

    # Tools Audit Accordion (Raw Tool JSON Inspection)
    with gr.Accordion("🔍 Audit View: Raw Deterministic Tool Outputs (JSON)", open=False):
        with gr.Row():
            json_simp = gr.Code(label="Record Simplification Tool Output (Raw JSON)", language="json")
            json_spec = gr.Code(label="Specialist Finder Tool Output (Raw JSON)", language="json")

    # Event Wiring
    btn_ingest.click(
        fn=process_document_pipeline,
        inputs=[file_input, text_input, gr.State("")],
        outputs=[report_markdown, json_simp, json_spec, text_input]
    )

    btn_sample_lab.click(
        fn=lambda: handle_sample_click("Lab Report (Diabetes & Lipid Panel)"),
        inputs=[],
        outputs=[text_input, report_markdown, json_simp, json_spec]
    )

    btn_sample_discharge.click(
        fn=lambda: handle_sample_click("Discharge Summary (Cardiac & BP)"),
        inputs=[],
        outputs=[text_input, report_markdown, json_simp, json_spec]
    )

    btn_sample_rx.click(
        fn=lambda: handle_sample_click("Prescription & Clinical Note"),
        inputs=[],
        outputs=[text_input, report_markdown, json_simp, json_spec]
    )

    file_input.change(
        fn=process_document_pipeline,
        inputs=[file_input, gr.State(""), gr.State("")],
        outputs=[report_markdown, json_simp, json_spec, text_input]
    )

    btn_ask.click(
        fn=handle_chat_question,
        inputs=[question_input, chatbot],
        outputs=[question_input, chatbot]
    )

    question_input.submit(
        fn=handle_chat_question,
        inputs=[question_input, chatbot],
        outputs=[question_input, chatbot]
    )

    # Auto-load initial sample report on app load
    demo.load(
        fn=lambda: handle_sample_click("Lab Report (Diabetes & Lipid Panel)"),
        inputs=[],
        outputs=[text_input, report_markdown, json_simp, json_spec]
    )

if __name__ == "__main__":
    print("Launching Patient Record Simplifier Web Application...")
    demo.launch(server_name="127.0.0.1", server_port=7860, css=CUSTOM_CSS, share=False)
