"""
Deterministic Clinical Record Tools for Patient Record Simplifier & Health Companion Agent.
These tools do NOT rely on LLM generation for clinical evaluation; they implement deterministic,
rule-based medical terminology translation, reference range validation, and specialist routing logic.
"""

import re
import os
import requests
from typing import Dict, List, Any
from langchain_core.tools import tool

# Adzuna API Credentials from Environment
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY", "")

# ---------------------------------------------------------------------------
# Medical Jargon Dictionary (Deterministic Layperson Translation)
# ---------------------------------------------------------------------------
MEDICAL_JARGON_DICT: Dict[str, str] = {
    "hyperglycemia": "High blood sugar levels",
    "hypoglycemia": "Low blood sugar levels",
    "hypertension": "High blood pressure",
    "hypotension": "Low blood pressure",
    "dyslipidemia": "Unhealthy or abnormal cholesterol / lipid levels",
    "hypercholesterolemia": "High total cholesterol levels",
    "tachycardia": "Fast or elevated heart rate (over 100 bpm at rest)",
    "bradycardia": "Slow heart rate (under 60 bpm at rest)",
    "dyspnea": "Shortness of breath or difficulty breathing",
    "orthopnea": "Difficulty breathing when lying flat",
    "edema": "Swelling caused by excess fluid trapped in bodily tissues",
    "nephropathy": "Kidney damage or kidney disease",
    "neuropathy": "Nerve damage causing numbness, tingling, or pain",
    "retinopathy": "Eye damage caused by damaged blood vessels in the retina",
    "polyuria": "Excessive or frequent urination",
    "polydipsia": "Excessive or unquenchable thirst",
    "prandial": "Relating to or occurring during a meal",
    "postprandial": "Occurring after a meal",
    "prn": "As needed (take medication only when symptoms occur)",
    "bid": "Twice daily (two times a day)",
    "tid": "Three times daily (three times a day)",
    "qid": "Four times daily (four times a day)",
    "qhs": "At bedtime",
    "po": "By mouth (oral administration)",
    "npo": "Nothing by mouth (do not eat or drink)",
    "elevated": "Higher than normal range",
    "depressed": "Lower than normal range",
    "leukocytosis": "Elevated white blood cell count (may indicate infection or inflammation)",
    "anemia": "Low red blood cells or hemoglobin (may cause fatigue)",
    "thrombocytopenia": "Low blood platelet count (increased bleeding risk)",
    "hypokalemia": "Low potassium in the blood",
    "hyperkalemia": "High potassium in the blood",
    "hyponatremia": "Low sodium in the blood",
    "azotemia": "High blood urea nitrogen (BUN) indicating kidney workload",
}

# ---------------------------------------------------------------------------
# Standard Deterministic Clinical Reference Ranges
# ---------------------------------------------------------------------------
CLINICAL_REFERENCE_RANGES: List[Dict[str, Any]] = [
    {
        "names": ["hba1c", "a1c", "hemoglobin a1c"],
        "display_name": "Hemoglobin A1c (HbA1c)",
        "unit": "%",
        "normal_min": 4.0,
        "normal_max": 5.6,
        "warning_max": 6.4, # Pre-diabetes: 5.7 - 6.4
        "category": "Endocrinology",
        "low_meaning": "Lower than average blood sugar over recent months",
        "high_meaning": "Elevated average blood sugar over past 2-3 months (indicates diabetes / pre-diabetes risk)",
    },
    {
        "names": ["fasting glucose", "fasting blood sugar", "glucose"],
        "display_name": "Fasting Blood Glucose",
        "unit": "mg/dL",
        "normal_min": 70.0,
        "normal_max": 99.0,
        "warning_max": 125.0,
        "category": "Endocrinology",
        "low_meaning": "Low blood sugar (hypoglycemia) - may cause dizziness or shakiness",
        "high_meaning": "High fasting blood sugar (hyperglycemia) - requires dietary or medical follow-up",
    },
    {
        "names": ["systolic bp", "systolic blood pressure", "systolic"],
        "display_name": "Systolic Blood Pressure",
        "unit": "mmHg",
        "normal_min": 90.0,
        "normal_max": 120.0,
        "warning_max": 139.0,
        "category": "Cardiology",
        "low_meaning": "Low blood pressure - may cause lightheadedness",
        "high_meaning": "Elevated blood pressure - places higher strain on heart and blood vessels",
    },
    {
        "names": ["diastolic bp", "diastolic blood pressure", "diastolic"],
        "display_name": "Diastolic Blood Pressure",
        "unit": "mmHg",
        "normal_min": 60.0,
        "normal_max": 80.0,
        "warning_max": 89.0,
        "category": "Cardiology",
        "low_meaning": "Low resting pressure in arteries",
        "high_meaning": "Elevated resting pressure in blood vessels",
    },
    {
        "names": ["ldl", "ldl cholesterol", "ldl-c"],
        "display_name": "LDL Cholesterol ('Bad' Cholesterol)",
        "unit": "mg/dL",
        "normal_min": 0.0,
        "normal_max": 100.0,
        "warning_max": 159.0,
        "category": "Cardiology",
        "low_meaning": "Very low LDL level (generally favorable)",
        "high_meaning": "High LDL cholesterol - can lead to plaque buildup in cardiovascular system",
    },
    {
        "names": ["hdl", "hdl cholesterol", "hdl-c"],
        "display_name": "HDL Cholesterol ('Good' Cholesterol)",
        "unit": "mg/dL",
        "normal_min": 40.0,
        "normal_max": 100.0,
        "category": "Cardiology",
        "low_meaning": "Below optimal protective HDL cholesterol level",
        "high_meaning": "Good protective cholesterol level",
    },
    {
        "names": ["triglycerides", "triglyceride"],
        "display_name": "Triglycerides",
        "unit": "mg/dL",
        "normal_min": 0.0,
        "normal_max": 150.0,
        "warning_max": 199.0,
        "category": "Cardiology",
        "low_meaning": "Low triglyceride level",
        "high_meaning": "Elevated blood fat levels - increases cardiovascular risk",
    },
    {
        "names": ["tsh", "thyroid stimulating hormone"],
        "display_name": "Thyroid Stimulating Hormone (TSH)",
        "unit": "mIU/L",
        "normal_min": 0.45,
        "normal_max": 4.5,
        "category": "Endocrinology",
        "low_meaning": "Possible hyperthyroidism (overactive thyroid gland)",
        "high_meaning": "Possible hypothyroidism (underactive thyroid gland)",
    },
    {
        "names": ["creatinine", "serum creatinine"],
        "display_name": "Serum Creatinine",
        "unit": "mg/dL",
        "normal_min": 0.6,
        "normal_max": 1.2,
        "category": "Nephrology",
        "low_meaning": "Lower creatinine level (often related to low muscle mass)",
        "high_meaning": "Elevated creatinine - indicates reduced kidney filtration capacity",
    },
    {
        "names": ["egfr", "gfr", "estimated gfr"],
        "display_name": "eGFR (Kidney Function)",
        "unit": "mL/min/1.73m2",
        "normal_min": 90.0,
        "normal_max": 120.0,
        "category": "Nephrology",
        "low_meaning": "Reduced kidney filtration rate - warrants nephrology evaluation",
        "high_meaning": "Normal healthy kidney filtration rate",
    },
    {
        "names": ["wbc", "white blood cells", "white blood cell count"],
        "display_name": "White Blood Cell Count (WBC)",
        "unit": "x10^3/uL",
        "normal_min": 4.5,
        "normal_max": 11.0,
        "category": "Hematology",
        "low_meaning": "Low white blood cells - higher susceptibility to infections",
        "high_meaning": "Elevated white blood cells - indicates active immune response or inflammation",
    },
    {
        "names": ["hemoglobin", "hgb"],
        "display_name": "Hemoglobin",
        "unit": "g/dL",
        "normal_min": 12.0,
        "normal_max": 17.5,
        "category": "Hematology",
        "low_meaning": "Low hemoglobin (Anemia) - causes fatigue and reduced oxygen transport",
        "high_meaning": "Elevated hemoglobin level",
    },
    {
        "names": ["platelets", "platelet count"],
        "display_name": "Platelet Count",
        "unit": "x10^3/uL",
        "normal_min": 150.0,
        "normal_max": 450.0,
        "category": "Hematology",
        "low_meaning": "Low platelets (Thrombocytopenia) - risk of easy bruising or bleeding",
        "high_meaning": "High platelet count",
    },
    {
        "names": ["alt", "alanine aminotransferase", "sgpt"],
        "display_name": "ALT (Liver Enzyme)",
        "unit": "U/L",
        "normal_min": 7.0,
        "normal_max": 56.0,
        "category": "Gastroenterology",
        "low_meaning": "Normal liver enzyme activity",
        "high_meaning": "Elevated liver enzyme - potential liver stress or inflammation",
    },
    {
        "names": ["ast", "aspartate aminotransferase", "sgot"],
        "display_name": "AST (Liver Enzyme)",
        "unit": "U/L",
        "normal_min": 10.0,
        "normal_max": 40.0,
        "category": "Gastroenterology",
        "low_meaning": "Normal liver enzyme activity",
        "high_meaning": "Elevated liver enzyme - suggests liver tissue or muscle stress",
    }
]

# ---------------------------------------------------------------------------
# Deterministic Specialist / Department Lookup Table
# ---------------------------------------------------------------------------
SPECIALIST_LOOKUP_TABLE: Dict[str, Dict[str, Any]] = {
    "Endocrinology": {
        "specialist": "Endocrinologist",
        "department": "Department of Endocrinology & Diabetes Care",
        "reason": "Specializes in hormone regulation, blood sugar management, thyroid function, and metabolic health.",
        "urgency": "Routine / Within 1 to 2 weeks",
        "doctor_questions": [
            "What lifestyle or medication adjustments are recommended for my HbA1c / glucose levels?",
            "Do I need to monitor my blood sugar at home, and how often?",
            "Should we order a follow-up metabolic panel or thyroid check?"
        ]
    },
    "Cardiology": {
        "specialist": "Cardiologist",
        "department": "Department of Cardiology & Vascular Medicine",
        "reason": "Specializes in heart function, blood pressure optimization, lipid profiles, and cardiovascular prevention.",
        "urgency": "Prompt / Within 3 to 7 days",
        "doctor_questions": [
            "Are my current blood pressure and cholesterol levels placing me at elevated cardiovascular risk?",
            "Would a lipid-lowering medication (e.g. statin) or antihypertensive dose adjustment be appropriate?",
            "Are there specific exercise limits or cardiac diagnostic tests I should take?"
        ]
    },
    "Nephrology": {
        "specialist": "Nephrologist",
        "department": "Department of Nephrology & Kidney Care",
        "reason": "Specializes in kidney function, electrolyte balance, and preventing renal stress.",
        "urgency": "Prompt / Within 5 to 7 days",
        "doctor_questions": [
            "Does my elevated creatinine or reduced eGFR indicate acute kidney stress or chronic kidney disease?",
            "Are any of my current medications hard on my kidneys?",
            "What hydration or dietary precautions should I follow?"
        ]
    },
    "Hematology": {
        "specialist": "Hematologist",
        "department": "Department of Hematology & Blood Disorders",
        "reason": "Specializes in blood counts, red blood cells, white blood cells, and clotting parameters.",
        "urgency": "Routine / Within 1 to 2 weeks",
        "doctor_questions": [
            "What is causing the fluctuation in my blood cell / platelet count?",
            "Should we screen for iron deficiency, vitamin B12 deficiency, or underlying inflammation?",
            "Do I need repeat blood work to track these levels over time?"
        ]
    },
    "Gastroenterology": {
        "specialist": "Gastroenterologist / Hepatologist",
        "department": "Department of Gastroenterology & Digestive Diseases",
        "reason": "Specializes in liver enzyme elevation, digestive tract health, and abdominal symptom evaluation.",
        "urgency": "Routine / Within 1 to 2 weeks",
        "doctor_questions": [
            "Could my elevated liver enzymes (ALT/AST) be caused by medication, fatty liver, or another factor?",
            "Do you recommend an abdominal ultrasound or further hepatic blood tests?",
            "Are there specific dietary changes or alcohol restrictions I should maintain?"
        ]
    },
    "Pulmonology": {
        "specialist": "Pulmonologist",
        "department": "Department of Respiratory & Pulmonary Medicine",
        "reason": "Specializes in lung health, shortness of breath, respiratory illness, and airway function.",
        "urgency": "Prompt / Within 2 to 5 days",
        "doctor_questions": [
            "What is the primary cause of my respiratory symptoms or shortness of breath?",
            "Should I perform a spirometry test or chest imaging review?",
            "What signs should prompt immediate emergency care?"
        ]
    },
    "Primary Care": {
        "specialist": "Primary Care Physician (PCP)",
        "department": "Department of General Internal Medicine / Family Practice",
        "reason": "Oversees comprehensive care, medication reconciliation, and holistic health monitoring.",
        "urgency": "Routine / Within 1 to 2 weeks",
        "doctor_questions": [
            "Can you review my full medication regimen for potential interactions?",
            "When should I schedule repeat baseline lab work?",
            "Do I need any specialist referrals based on this report?"
        ]
    }
}


# ---------------------------------------------------------------------------
# Tool 1: Record Simplification & Flagging Tool
# ---------------------------------------------------------------------------
@tool
def record_simplification_and_flagging_tool(record_text: str) -> Dict[str, Any]:
    """
    Parses a patient's medical document text deterministically, translates medical jargon
    into plain language, evaluates lab values against reference ranges, and flags any abnormal
    results or critical instructions needing follow-up.

    Args:
        record_text: The complete extracted text from the patient's lab report, discharge summary, or prescription.

    Returns:
        Dict containing plain_language_summary, jargon_translations, flagged_items, and verified_normal_items.
    """
    text_lower = record_text.lower()
    
    # 1. Deterministic Medical Jargon Extraction & Translation
    jargon_found = []
    for jargon_term, plain_meaning in MEDICAL_JARGON_DICT.items():
        pattern = r"\b" + re.escape(jargon_term) + r"\b"
        if re.search(pattern, text_lower):
            jargon_found.append({
                "jargon": jargon_term.capitalize(),
                "plain_translation": plain_meaning
            })

    # 2. Deterministic Reference Range Evaluation & Value Extraction
    flagged_items = []
    normal_items = []

    for ref in CLINICAL_REFERENCE_RANGES:
        for name in ref["names"]:
            # Pattern matches name followed by optional separator (: / = / space) and number
            pattern = r"\b" + re.escape(name) + r"\s*[:=\-]?\s*([0-9]+(?:\.[0-9]+)?)"
            match = re.search(pattern, text_lower)
            if match:
                val = float(match.group(1))
                item_info = {
                    "parameter": ref["display_name"],
                    "value": f"{val} {ref['unit']}",
                    "numeric_value": val,
                    "reference_range": f"{ref['normal_min']} - {ref['normal_max']} {ref['unit']}",
                    "category": ref["category"],
                }

                if val > ref["normal_max"]:
                    severity = "CRITICAL / HIGH" if ("warning_max" in ref and val > ref["warning_max"]) else "ABNORMAL HIGH"
                    item_info["status"] = severity
                    item_info["flagged"] = True
                    item_info["explanation"] = ref["high_meaning"]
                    flagged_items.append(item_info)
                elif val < ref["normal_min"]:
                    item_info["status"] = "ABNORMAL LOW"
                    item_info["flagged"] = True
                    item_info["explanation"] = ref["low_meaning"]
                    flagged_items.append(item_info)
                else:
                    item_info["status"] = "NORMAL"
                    item_info["flagged"] = False
                    item_info["explanation"] = "Within healthy target range."
                    normal_items.append(item_info)
                break  # Matched one alias for this parameter

    # 3. Supplemental Rule-Based Key Phrase Scanning (Discharge / Rx warnings)
    rx_warnings = []
    if "furosemide" in text_lower or "lasix" in text_lower:
        rx_warnings.append("Diuretic medication detected (Furosemide/Lasix): Hydration and electrolyte monitoring recommended.")
    if "lisinopril" in text_lower or "enalapril" in text_lower:
        rx_warnings.append("ACE Inhibitor medication detected (Lisinopril): Monitor blood pressure and potassium levels.")
    if "metformin" in text_lower:
        rx_warnings.append("Glucose-lowering medication detected (Metformin): Monitor kidney function (creatinine) periodically.")

    # 4. Synthesize Plain-Language Narrative Summary
    total_parsed = len(flagged_items) + len(normal_items)
    summary_sentences = [
        f"We processed your record and identified {total_parsed} key clinical parameter(s) and {len(jargon_found)} medical term(s)."
    ]
    if flagged_items:
        summary_sentences.append(
            f"⚠️ **Attention Required**: {len(flagged_items)} value(s) fall outside the standard reference range and have been flagged for doctor review."
        )
    else:
        summary_sentences.append("✅ All evaluated laboratory results fall within standard normal target ranges.")

    if jargon_found:
        terms_str = ", ".join([f"'{item['jargon']}' ({item['plain_translation'].lower()})" for item in jargon_found[:3]])
        summary_sentences.append(f"Medical jargon translated includes: {terms_str}.")

    plain_summary = " ".join(summary_sentences)

    return {
        "plain_language_summary": plain_summary,
        "jargon_translations": jargon_found,
        "flagged_items": flagged_items,
        "verified_normal_items": normal_items,
        "prescription_warnings": rx_warnings,
        "total_flagged_count": len(flagged_items),
    }


# ---------------------------------------------------------------------------
# Tool 2: Specialist / Department Finder Tool
# ---------------------------------------------------------------------------
@tool
def specialist_department_finder_tool(flagged_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Takes the out-of-range clinical items flagged by the simplification tool and deterministically
    maps them to the corresponding medical specialist, department, action timeline, and preparation questions.

    Args:
        flagged_items: List of flagged out-of-range item dictionaries returned by record_simplification_and_flagging_tool.

    Returns:
        Dict containing recommendations mapped by specialty and priority action steps.
    """
    if not flagged_items:
        return {
            "has_recommendations": False,
            "message": "No out-of-range items were flagged. Routine follow-up with your Primary Care Physician is recommended for standard maintenance.",
            "recommendations": [
                {
                    "category": "Primary Care",
                    "specialist": SPECIALIST_LOOKUP_TABLE["Primary Care"]["specialist"],
                    "department": SPECIALIST_LOOKUP_TABLE["Primary Care"]["department"],
                    "urgency": SPECIALIST_LOOKUP_TABLE["Primary Care"]["urgency"],
                    "reason": SPECIALIST_LOOKUP_TABLE["Primary Care"]["reason"],
                    "doctor_questions": SPECIALIST_LOOKUP_TABLE["Primary Care"]["doctor_questions"],
                    "associated_parameters": ["Routine Baseline Checks"]
                }
            ]
        }

    # Group flagged items by medical category
    category_map: Dict[str, List[str]] = {}
    for item in flagged_items:
        cat = item.get("category", "Primary Care")
        param = f"{item['parameter']} ({item['value']} vs Ref: {item['reference_range']})"
        category_map.setdefault(cat, []).append(param)

    recommendations = []
    for cat, params in category_map.items():
        lookup = SPECIALIST_LOOKUP_TABLE.get(cat, SPECIALIST_LOOKUP_TABLE["Primary Care"])
        recommendations.append({
            "category": cat,
            "specialist": lookup["specialist"],
            "department": lookup["department"],
            "urgency": lookup["urgency"],
            "reason": lookup["reason"],
            "doctor_questions": lookup["doctor_questions"],
            "associated_parameters": params
        })

    return {
        "has_recommendations": True,
        "total_specialties_recommended": len(recommendations),
        "recommendations": recommendations,
        "general_advice": "Please share these flagged values and suggested questions directly with your doctor during your next appointment."
    }


# ---------------------------------------------------------------------------
# Tool 3: Adzuna API Medical Specialist / Healthcare Search Tool
# ---------------------------------------------------------------------------
@tool
def adzuna_specialist_search_tool(query: str, country: str = "us") -> Dict[str, Any]:
    """
    Uses the Adzuna API to search for active medical specialist listings, healthcare department
    postings, or clinical opportunities corresponding to a recommended medical specialty.

    Args:
        query: Medical role or specialty term (e.g., 'Endocrinologist', 'Cardiologist', 'Nephrologist').
        country: Country code for Adzuna API search (default 'us' or 'gb').

    Returns:
        Dict containing listing search results or status.
    """
    app_id = os.getenv("ADZUNA_APP_ID", "")
    app_key = os.getenv("ADZUNA_APP_KEY", "")

    if not app_id or not app_key:
        return {
            "status": "CONFIG_REQUIRED",
            "message": "Adzuna API credentials (ADZUNA_APP_ID, ADZUNA_APP_KEY) not set in environment or .env file.",
            "query": query,
            "sample_listings": [
                {
                    "title": f"Senior {query} - Academic Medical Center",
                    "department": f"Department of {query}",
                    "location": "Regional Health System",
                    "description": f"Clinical specialist position focusing on comprehensive patient care and diagnostic evaluation."
                }
            ]
        }

    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
    params = {
        "app_id": app_id,
        "app_key": app_key,
        "what": query,
        "content-type": "application/json"
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])[:3]
            clean_results = []
            for r in results:
                clean_results.append({
                    "title": r.get("title", ""),
                    "company": r.get("company", {}).get("display_name", "Medical Facility"),
                    "location": r.get("location", {}).get("display_name", ""),
                    "url": r.get("redirect_url", "")
                })
            return {
                "status": "SUCCESS",
                "total_matches": len(data.get("results", [])),
                "listings": clean_results
            }
        else:
            return {
                "status": "API_ERROR",
                "error": f"Adzuna API returned status code {response.status_code}",
                "query": query
            }
    except Exception as e:
        return {
            "status": "EXCEPTION",
            "error": str(e),
            "query": query
        }

