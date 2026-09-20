"""
Synthetic De-Identified Sample Medical Documents for Patient Record Simplifier & Health Companion Agent.
These documents contain NO real patient data and are for testing and benchmarking purposes.
"""

SAMPLE_LAB_REPORT_DIABETES_LIPIDS = """METROPOLITAN CLINICAL LABORATORY REPORT
PATIENT: Synthetic Sample Patient #1042
AGE: 54 | GENDER: Male | DATE: 2026-08-15
PHYSICIAN: Dr. R. Vance, MD | FACILITY: Metro Health Diagnostic Center

SECTION: COMPREHENSIVE METABOLIC & LIPID PANEL

TEST NAME                  OBSERVED VALUE        REFERENCE RANGE       UNIT
-----------------------------------------------------------------------------
Fasting Blood Glucose       165.0 H              70.0 - 99.0           mg/dL
Hemoglobin A1c              8.2 H                4.0 - 5.6             %
Serum Creatinine            1.4 H                0.6 - 1.2             mg/dL
eGFR                        58.0 L               90.0 - 120.0          mL/min/1.73m2
Total Cholesterol           238.0 H              0.0 - 200.0           mg/dL
LDL Cholesterol             155.0 H              0.0 - 100.0           mg/dL
HDL Cholesterol             38.0 L               40.0 - 100.0          mg/dL
Triglycerides               210.0 H              0.0 - 150.0           mg/dL
TSH                         2.1                  0.45 - 4.5            mIU/L
WBC                         6.8                  4.5 - 11.0            x10^3/uL

CLINICAL IMPRESSION & IMPRESSION NOTES:
Patient demonstrates marked Hyperglycemia with HbA1c elevated at 8.2%, indicative of poorly controlled type 2 diabetes mellitus.
Accompanying Dyslipidemia with LDL cholesterol at 155 mg/dL and elevated triglycerides.
Mild Azotemia noted with Serum Creatinine elevated at 1.4 mg/dL and eGFR at 58 mL/min/1.73m2, suggesting early diabetic Nephropathy workload.
Patient reports mild Polyuria and Polydipsia over past 3 weeks.

RECOMMENDATIONS:
- Dietary modification with low glycemic index nutrition and reduced saturated fats.
- Specialist consultation with Endocrinology for diabetes management optimization.
- Nephrology follow-up for renal function monitoring.
"""

SAMPLE_DISCHARGE_SUMMARY_CARDIAC = """CITY GENERAL HOSPITAL - DISCHARGE SUMMARY
PATIENT: Synthetic Sample Patient #2089
ADMISSION DATE: 2026-09-01 | DISCHARGE DATE: 2026-09-05
ATTENDING PHYSICIAN: Dr. S. Patel, MD, FACC

DIAGNOSIS & CLINICAL COURSE:
Patient admitted with acute Dyspnea on exertion and Orthopnea. Physical examination revealed bilateral peripheral Edema (+2) and elevated resting blood pressure.
Echocardiogram demonstrated left ventricular ejection fraction of 48%. Patient treated with intravenous Furosemide with significant diuresis and symptom resolution.

DISCHARGE VITAL SIGNS & LABS:
Systolic BP: 158.0 mmHg (High)
Diastolic BP: 94.0 mmHg (High)
Heart Rate: 88 bpm
WBC: 12.4 x10^3/uL (Elevated Leukocytosis)
Hemoglobin: 11.2 g/dL (Mild Anemia)
Serum Potassium: 4.1 mEq/L (Normal)
Serum Creatinine: 1.1 mg/dL (Normal)

DISCHARGE MEDICATIONS:
1. Lisinopril 20 mg PO daily (Antihypertensive - ACE Inhibitor)
2. Furosemide 40 mg PO QHS (Diuretic - take at bedtime / as directed)
3. Metoprolol Succinate 50 mg PO daily (Beta-blocker)
4. Atorvastatin 40 mg PO QHS

PATIENT INSTRUCTIONS:
- Monitor blood pressure daily and record in logbook.
- Report any sudden weight gain (>2 lbs in 24 hrs) or worsening Dyspnea immediately.
- Cardiology outpatient follow-up appointment within 7 days.
- Low-sodium diet (<2000 mg/day).
"""

SAMPLE_PRESCRIPTION_CLINICAL_NOTE = """VALLEY COMMUNITY HEALTH CENTER - PRESCRIPTION & CLINICAL VISIT NOTE
PATIENT: Synthetic Sample Patient #3011
DATE OF VISIT: 2026-09-10
PROVIDER: Dr. A. Miller, DO

REASON FOR VISIT: Routine follow-up for chronic hypertension and metabolic management.

CLINICAL OBSERVATIONS:
Patient complains of occasional Tachycardia and mild exertion fatigue. Blood pressure today measured at 144/88 mmHg. Fasting blood sugar noted at 138.0 mg/dL.
Mild Leukocytosis present on recent CBC.

ACTIVE PRESCRIPTION ORDERS:
1. Metformin 1000 mg PO BID (Take twice daily with meals to manage Hyperglycemia)
2. Lisinopril 10 mg PO QD (Take once daily for Hypertension control)
3. Atorvastatin 20 mg PO QHS (Take at bedtime for Dyslipidemia)
4. Albuterol Inhaler 90 mcg 2 puffs PRN (Take as needed for sudden Dyspnea)

SPECIAL INSTRUCTIONS:
- Do NPO prior to upcoming fasting blood work.
- If experiencing severe Tachycardia or dizziness, contact clinic PRN.
"""

SAMPLE_DOCUMENTS = {
    "Lab Report (Diabetes & Lipid Panel)": SAMPLE_LAB_REPORT_DIABETES_LIPIDS,
    "Discharge Summary (Cardiac & BP)": SAMPLE_DISCHARGE_SUMMARY_CARDIAC,
    "Prescription & Clinical Note": SAMPLE_PRESCRIPTION_CLINICAL_NOTE,
}
