"""
Standalone FastAPI Web Server & Healthcare SaaS Portal.
Includes Patient Sign-In/Registration, Record History Tracker, Biomarker Dashboard,
Medication Reminders, and Daily Water Intake Tracker.
"""

import sys
import os
import json
import tempfile
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
import uvicorn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.sample_data import (
    SAMPLE_LAB_REPORT_DIABETES_LIPIDS,
    SAMPLE_DISCHARGE_SUMMARY_CARDIAC,
    SAMPLE_PRESCRIPTION_CLINICAL_NOTE,
    SAMPLE_DOCUMENTS
)
from src.document_processor import SessionDocumentProcessor
from src.agent import HealthCompanionAgent
from src.db import db_manager

app = FastAPI(title="Health Companion - Clinical Record Simplifier & Patient Portal")
agent = HealthCompanionAgent()
current_session = SessionDocumentProcessor()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Health Companion | Patient Portal & Clinical Simplifier</title>
    <link rel="icon" type="image/jpeg" href="/logo.jpg">
    <link rel="shortcut icon" type="image/jpeg" href="/logo.jpg">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #f8fafc;
            --card-bg: #ffffff;
            --card-border: #e2e8f0;
            --inner-bg: #f1f5f9;
            --text-primary: #0f172a;
            --text-secondary: #334155;
            --text-muted: #64748b;
            
            --accent-primary: #0284c7;
            --accent-hover: #0369a1;
            --accent-light: #e0f2fe;
            
            --alert-red: #dc2626;
            --alert-red-bg: #fee2e2;
            --alert-red-border: #fca5a5;
            
            --normal-green: #16a34a;
            --normal-green-bg: #dcfce7;
            --normal-green-border: #86efac;
            
            --warning-amber: #d97706;
            --warning-amber-bg: #fef3c7;

            --water-blue: #0284c7;
            --water-bg: #e0f2fe;
            
            --font-sans: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            --font-mono: 'JetBrains Mono', monospace;
            
            --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
            --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.07), 0 2px 4px -1px rgba(0, 0, 0, 0.04);
            --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.03);
            --radius-md: 10px;
            --radius-lg: 14px;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
            background-color: var(--bg-color);
            color: var(--text-secondary);
            font-family: var(--font-sans);
            max-width: 1280px;
            margin: 0 auto;
            padding: 32px 24px 120px 24px;
            line-height: 1.5;
            -webkit-font-smoothing: antialiased;
        }

        /* Login & Registration Overlay */
        .login-overlay {
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(15, 23, 42, 0.65);
            backdrop-filter: blur(8px);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 2000;
        }

        .login-modal {
            background: #ffffff;
            border: 1px solid var(--card-border);
            border-radius: var(--radius-lg);
            padding: 36px;
            width: 100%;
            max-width: 460px;
            box-shadow: var(--shadow-lg);
            max-height: 90vh;
            overflow-y: auto;
        }

        .auth-nav-toggle {
            display: flex;
            background: var(--inner-bg);
            border-radius: 8px;
            padding: 4px;
            margin-bottom: 24px;
        }

        .auth-toggle-btn {
            flex: 1;
            padding: 8px;
            font-size: 0.85rem;
            font-weight: 600;
            border: none;
            background: transparent;
            color: var(--text-muted);
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
        }

        .auth-toggle-btn.active {
            background: #ffffff;
            color: var(--text-primary);
            font-weight: 700;
            box-shadow: var(--shadow-sm);
        }

        .login-header {
            text-align: center;
            margin-bottom: 24px;
        }

        .login-logo {
            width: 44px;
            height: 44px;
            background: linear-gradient(135deg, #0284c7, #0f766e);
            color: #ffffff;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.4rem;
            margin: 0 auto 12px auto;
            box-shadow: 0 4px 10px rgba(2, 132, 199, 0.3);
        }

        .login-title {
            font-size: 1.4rem;
            font-weight: 800;
            color: var(--text-primary);
            letter-spacing: -0.4px;
        }

        .login-subtitle {
            font-size: 0.82rem;
            color: var(--text-muted);
            margin-top: 4px;
        }

        .form-group {
            margin-bottom: 16px;
        }

        .form-label {
            display: block;
            font-size: 0.82rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 6px;
        }

        .form-input {
            width: 100%;
            padding: 10px 14px;
            background: var(--bg-color);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            font-size: 0.88rem;
            color: var(--text-primary);
            transition: all 0.2s;
        }

        .form-input:focus {
            outline: none;
            border-color: var(--accent-primary);
            box-shadow: 0 0 0 3px var(--accent-light);
        }

        .btn-full {
            width: 100%;
            padding: 12px;
            font-size: 0.95rem;
            font-weight: 700;
            margin-top: 8px;
        }

        /* Top Navigation Header */
        .navbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 20px;
            margin-bottom: 24px;
            border-bottom: 1px solid var(--card-border);
        }

        .brand-logo {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 1.35rem;
            font-weight: 800;
            color: var(--text-primary);
            letter-spacing: -0.3px;
        }

        .brand-icon {
            width: 38px;
            height: 38px;
            background: linear-gradient(135deg, #0284c7, #0f766e);
            color: #ffffff;
            border-radius: 9px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.1rem;
            box-shadow: 0 2px 6px rgba(2, 132, 199, 0.25);
        }

        .brand-badge {
            background: var(--accent-light);
            color: var(--accent-primary);
            font-size: 0.72rem;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 6px;
            text-transform: uppercase;
        }

        .user-nav-profile {
            display: flex;
            align-items: center;
            gap: 16px;
        }

        .user-avatar-badge {
            display: flex;
            align-items: center;
            gap: 10px;
            background: #ffffff;
            border: 1px solid var(--card-border);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-primary);
            box-shadow: var(--shadow-sm);
        }

        .avatar-circle {
            width: 24px;
            height: 24px;
            background: var(--accent-light);
            color: var(--accent-primary);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            font-weight: 800;
        }

        /* Navigation Portal Tabs */
        .portal-tabs {
            display: flex;
            gap: 12px;
            margin-bottom: 28px;
            border-bottom: 1px solid var(--card-border);
            padding-bottom: 12px;
        }

        .tab-btn {
            background: transparent;
            border: none;
            font-family: var(--font-sans);
            font-size: 0.95rem;
            font-weight: 600;
            color: var(--text-muted);
            padding: 8px 16px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .tab-btn:hover {
            color: var(--text-primary);
            background: var(--inner-bg);
        }

        .tab-btn.active {
            color: var(--accent-primary);
            background: var(--accent-light);
            font-weight: 700;
        }

        /* Clinical Disclaimer Notice Bar */
        .clinical-notice-bar {
            background: #f0f9ff;
            border: 1px solid #bae6fd;
            color: #0369a1;
            padding: 12px 18px;
            border-radius: var(--radius-md);
            font-size: 0.85rem;
            font-weight: 600;
            margin-bottom: 28px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        /* Section Container Cards */
        .saas-card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: var(--radius-lg);
            padding: 28px;
            margin-bottom: 28px;
            box-shadow: var(--shadow-sm);
        }

        .section-header {
            font-size: 0.8rem;
            font-weight: 700;
            color: var(--accent-primary);
            text-transform: uppercase;
            letter-spacing: 0.8px;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .card-header-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }

        .card-title {
            font-size: 1.35rem;
            font-weight: 700;
            color: var(--text-primary);
            letter-spacing: -0.3px;
        }

        .card-subtitle {
            font-size: 0.82rem;
            color: var(--text-muted);
            margin-top: 2px;
        }

        /* Buttons */
        .btn-primary {
            background: var(--accent-primary);
            color: #ffffff;
            font-family: var(--font-sans);
            font-weight: 600;
            font-size: 0.9rem;
            padding: 10px 18px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            box-shadow: var(--shadow-sm);
        }

        .btn-primary:hover {
            background: var(--accent-hover);
        }

        .btn-secondary {
            background: #ffffff;
            border: 1px solid var(--card-border);
            color: var(--text-secondary);
            font-family: var(--font-sans);
            font-weight: 600;
            font-size: 0.85rem;
            padding: 8px 14px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }

        .btn-secondary:hover {
            border-color: #cbd5e1;
            background: #f8fafc;
        }

        /* Benchmark Cards Grid */
        .benchmark-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 18px;
            margin-top: 18px;
        }

        .bm-card {
            background: #ffffff;
            border: 1.5px solid var(--card-border);
            border-radius: var(--radius-md);
            padding: 20px;
            cursor: pointer;
            transition: all 0.2s ease;
        }

        .bm-card:hover {
            border-color: var(--accent-primary);
            transform: translateY(-2px);
        }

        .bm-card.active {
            border-color: var(--accent-primary);
            background: #f0f9ff;
        }

        .bm-top-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }

        .bm-category-tag {
            font-size: 0.75rem;
            font-weight: 700;
            color: var(--text-muted);
            text-transform: uppercase;
        }

        .bm-active-badge {
            background: var(--accent-primary);
            color: #ffffff;
            font-size: 0.65rem;
            font-weight: 700;
            padding: 2px 7px;
            border-radius: 4px;
            text-transform: uppercase;
        }

        .bm-title {
            font-size: 1.05rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 6px;
        }

        .bm-desc {
            font-size: 0.85rem;
            color: var(--text-muted);
            line-height: 1.4;
        }

        .upload-dropzone {
            background: var(--inner-bg);
            border: 2px dashed #cbd5e1;
            border-radius: var(--radius-md);
            padding: 24px;
            text-align: center;
            margin-bottom: 20px;
        }

        .dropzone-title {
            font-size: 0.95rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 4px;
        }

        .dropzone-subtitle {
            font-size: 0.8rem;
            color: var(--text-muted);
            margin-bottom: 14px;
        }

        .custom-text-box {
            background: #ffffff;
            border: 1px solid var(--card-border);
            border-radius: var(--radius-md);
            padding: 16px;
            margin-top: 16px;
            display: none;
        }

        textarea {
            width: 100%;
            height: 110px;
            background: #f8fafc;
            color: var(--text-primary);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 12px;
            font-family: var(--font-sans);
            font-size: 0.9rem;
            margin-bottom: 12px;
            resize: vertical;
        }

        /* Priority Biomarker Flags Grid */
        .biomarker-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 18px;
            margin-bottom: 28px;
        }

        .flag-card {
            background: #ffffff;
            border: 1px solid var(--card-border);
            border-radius: var(--radius-md);
            padding: 20px;
            box-shadow: var(--shadow-sm);
        }

        .flag-card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 14px;
        }

        .flag-category {
            font-size: 0.72rem;
            font-weight: 700;
            color: var(--text-muted);
            text-transform: uppercase;
        }

        .badge-alert-high {
            background: var(--alert-red-bg);
            color: var(--alert-red);
            border: 1px solid var(--alert-red-border);
            font-size: 0.7rem;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 4px;
            text-transform: uppercase;
        }

        .flag-num-row {
            display: flex;
            align-items: baseline;
            gap: 6px;
            margin-bottom: 4px;
        }

        .flag-num {
            font-size: 2.2rem;
            font-weight: 800;
            color: var(--alert-red);
            letter-spacing: -0.5px;
        }

        .flag-unit {
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--text-muted);
        }

        .flag-param-title {
            font-size: 1.05rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 12px;
        }

        .flag-footer {
            border-top: 1px solid var(--card-border);
            padding-top: 10px;
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--text-muted);
        }

        .exp-narrative {
            font-size: 1.05rem;
            color: var(--text-secondary);
            line-height: 1.7;
            margin-bottom: 24px;
        }

        .glossary-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 18px;
            border: 1px solid var(--card-border);
            border-radius: 8px;
            overflow: hidden;
        }

        .glossary-table th {
            background: var(--inner-bg);
            color: var(--text-primary);
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            text-align: left;
            padding: 12px 16px;
            border-bottom: 1px solid var(--card-border);
        }

        .glossary-table td {
            padding: 12px 16px;
            border-bottom: 1px solid var(--card-border);
            font-size: 0.9rem;
            background: #ffffff;
        }

        /* Specialist Recommendations Card */
        .specialist-card {
            background: #ffffff;
            border: 1px solid var(--card-border);
            border-radius: var(--radius-lg);
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: var(--shadow-sm);
        }

        .spec-top-row {
            display: flex;
            align-items: flex-start;
            gap: 16px;
            margin-bottom: 16px;
        }

        .spec-icon-box {
            width: 44px;
            height: 44px;
            background: var(--accent-light);
            color: var(--accent-primary);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
            flex-shrink: 0;
        }

        .spec-info-col {
            flex-grow: 1;
        }

        .spec-name {
            font-size: 1.35rem;
            font-weight: 700;
            color: var(--text-primary);
        }

        .spec-dept {
            font-size: 0.78rem;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
        }

        .timeline-badge {
            background: var(--accent-light);
            color: var(--accent-primary);
            font-size: 0.75rem;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 6px;
            text-transform: uppercase;
        }

        .spec-rationale {
            font-size: 0.95rem;
            color: var(--text-secondary);
            line-height: 1.6;
            margin-bottom: 16px;
        }

        .triggered-by-row {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }

        .trig-label {
            font-size: 0.75rem;
            font-weight: 700;
            color: var(--text-muted);
            text-transform: uppercase;
        }

        .trig-pill {
            background: var(--inner-bg);
            border: 1px solid var(--card-border);
            color: var(--accent-primary);
            font-size: 0.75rem;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 6px;
        }

        .questions-box {
            background: var(--inner-bg);
            border: 1px solid var(--card-border);
            border-radius: var(--radius-md);
            padding: 18px;
        }

        .q-header-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }

        .q-header-title {
            font-size: 0.8rem;
            font-weight: 700;
            color: var(--accent-primary);
            text-transform: uppercase;
        }

        .q-item {
            background: #ffffff;
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .q-text {
            font-size: 0.92rem;
            font-weight: 500;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .q-num {
            font-weight: 700;
            color: var(--accent-primary);
        }

        .copy-icon-btn {
            color: var(--text-muted);
            cursor: pointer;
            font-size: 0.9rem;
        }

        .copy-icon-btn:hover {
            color: var(--accent-primary);
        }

        /* Medication Reminder & Water Intake Cards */
        .med-reminder-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 18px;
            margin-bottom: 24px;
        }

        .med-card {
            background: #ffffff;
            border: 1px solid var(--card-border);
            border-radius: var(--radius-md);
            padding: 20px;
            box-shadow: var(--shadow-sm);
            position: relative;
        }

        .med-time-badge {
            font-family: var(--font-mono);
            font-size: 0.72rem;
            font-weight: 700;
            color: var(--accent-primary);
            background: var(--accent-light);
            padding: 3px 8px;
            border-radius: 4px;
        }

        .med-name {
            font-size: 1.1rem;
            font-weight: 700;
            color: var(--text-primary);
            margin: 8px 0 4px 0;
        }

        .med-dosage {
            font-size: 0.85rem;
            color: var(--text-muted);
            margin-bottom: 14px;
        }

        .med-status-taken {
            background: var(--normal-green-bg);
            color: var(--normal-green);
            border: 1px solid var(--normal-green-border);
            font-size: 0.75rem;
            font-weight: 700;
            padding: 6px 12px;
            border-radius: 6px;
            display: inline-block;
        }

        /* Water Intake Tracker Box */
        .water-tracker-box {
            background: #f0f9ff;
            border: 1px solid #bae6fd;
            border-radius: var(--radius-lg);
            padding: 24px;
            margin-bottom: 28px;
        }

        .water-header-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }

        .water-title {
            font-size: 1.25rem;
            font-weight: 800;
            color: #0369a1;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .water-stat-num {
            font-size: 2.2rem;
            font-weight: 800;
            color: #0284c7;
        }

        .water-progress-bar {
            background: #bae6fd;
            height: 14px;
            border-radius: 8px;
            overflow: hidden;
            margin-bottom: 16px;
        }

        .water-progress-fill {
            background: linear-gradient(90deg, #0ea5e9, #0284c7);
            height: 100%;
            border-radius: 8px;
            transition: width 0.3s ease;
        }

        /* Health Progress Tracker Dashboard */
        .progress-stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 18px;
            margin-bottom: 28px;
        }

        .stat-card {
            background: #ffffff;
            border: 1px solid var(--card-border);
            border-radius: var(--radius-md);
            padding: 20px;
            box-shadow: var(--shadow-sm);
        }

        .stat-title {
            font-size: 0.78rem;
            font-weight: 700;
            color: var(--text-muted);
            text-transform: uppercase;
            margin-bottom: 8px;
        }

        .stat-val-row {
            display: flex;
            align-items: baseline;
            gap: 8px;
            margin-bottom: 6px;
        }

        .stat-value {
            font-size: 1.8rem;
            font-weight: 800;
            color: var(--text-primary);
        }

        .stat-trend-badge {
            background: var(--normal-green-bg);
            color: var(--normal-green);
            border: 1px solid var(--normal-green-border);
            font-size: 0.72rem;
            font-weight: 700;
            padding: 2px 7px;
            border-radius: 4px;
        }

        .stat-sub {
            font-size: 0.78rem;
            color: var(--text-muted);
        }

        .history-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 12px;
            border: 1px solid var(--card-border);
            border-radius: var(--radius-md);
            overflow: hidden;
        }

        .history-table th {
            background: var(--inner-bg);
            color: var(--text-primary);
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            text-align: left;
            padding: 12px 16px;
        }

        .history-table td {
            padding: 14px 16px;
            border-bottom: 1px solid var(--card-border);
            font-size: 0.9rem;
            background: #ffffff;
        }

        /* Floating Consult AI Assistant */
        .floating-consult-btn {
            position: fixed;
            bottom: 28px;
            right: 28px;
            background: var(--accent-primary);
            color: #ffffff;
            font-family: var(--font-sans);
            font-size: 0.9rem;
            font-weight: 700;
            padding: 12px 20px;
            border-radius: 30px;
            box-shadow: var(--shadow-lg);
            border: none;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            z-index: 1000;
        }

        .consult-drawer {
            position: fixed;
            bottom: 86px;
            right: 28px;
            width: 420px;
            height: 520px;
            background: #ffffff;
            border: 1px solid var(--card-border);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-lg);
            display: none;
            flex-direction: column;
            z-index: 999;
            overflow: hidden;
        }

        .drawer-header {
            background: var(--inner-bg);
            padding: 14px 18px;
            border-bottom: 1px solid var(--card-border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.9rem;
            font-weight: 700;
            color: var(--text-primary);
        }

        .drawer-messages {
            flex-grow: 1;
            padding: 16px;
            overflow-y: auto;
            font-size: 0.88rem;
        }

        .msg-user {
            background: var(--accent-light);
            color: var(--accent-primary);
            font-weight: 500;
            padding: 10px 14px;
            border-radius: 12px 12px 2px 12px;
            margin-bottom: 10px;
            max-width: 85%;
            margin-left: auto;
        }

        .msg-agent {
            background: var(--inner-bg);
            border: 1px solid var(--card-border);
            color: var(--text-secondary);
            padding: 10px 14px;
            border-radius: 12px 12px 12px 2px;
            margin-bottom: 10px;
            max-width: 90%;
        }

        .drawer-input-row {
            padding: 12px;
            background: #ffffff;
            border-top: 1px solid var(--card-border);
            display: flex;
            gap: 8px;
        }

        .drawer-input {
            flex-grow: 1;
            background: var(--inner-bg);
            border: 1px solid var(--card-border);
            color: var(--text-primary);
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 0.88rem;
        }

        .drawer-send-btn {
            background: var(--accent-primary);
            color: #ffffff;
            border: none;
            padding: 8px 14px;
            border-radius: 6px;
            font-weight: 700;
            cursor: pointer;
        }
    </style>
</head>
<body>

    <!-- Patient Authentication Overlay Modal -->
    <div class="login-overlay" id="loginOverlay" onclick="handleOverlayClick(event)">
        <div class="login-modal" style="position: relative;">
            <span style="position: absolute; top: 16px; right: 20px; font-size: 1.25rem; cursor: pointer; color: var(--text-muted); font-weight: 700;" onclick="closeLoginOverlay()" title="Close overlay">✕</span>
            <div class="login-header">
                <div class="login-logo" style="overflow: hidden; padding: 0; background: #ffffff;">
                    <img src="/logo.jpg" alt="Health Companion Logo" style="width: 100%; height: 100%; object-fit: cover; border-radius: 10px;">
                </div>
                <div class="login-title" id="authTitle">Patient Portal Sign In</div>
                <div class="login-subtitle" id="authSubtitle">Access your clinical record simplifier & health tracker</div>
            </div>

            <div class="auth-nav-toggle">
                <button class="auth-toggle-btn active" id="btn-toggle-signin" onclick="setAuthMode('signin')">Sign In</button>
                <button class="auth-toggle-btn" id="btn-toggle-register" onclick="setAuthMode('register')">Create Account (Register)</button>
            </div>

            <div id="form-signin">
                <div class="form-group">
                    <label class="form-label">Patient Email Address</label>
                    <input type="email" class="form-input" id="loginEmail" value="alex.morgan@patient-health.org" placeholder="Enter patient email">
                </div>

                <div class="form-group">
                    <label class="form-label">Password / Security PIN</label>
                    <input type="password" class="form-input" id="loginPassword" value="••••••••••••">
                </div>

                <button class="btn-primary btn-full" type="button" onclick="authenticatePatient()">Sign In to Health Portal</button>
                
                <div style="text-align: center; margin-top: 14px;">
                    <button class="btn-secondary" style="width: 100%;" type="button" onclick="authenticatePatient('Alex Morgan')">⚡ Quick Patient Demo Sign In</button>
                </div>
            </div>

            <div id="form-register" style="display: none;">
                <div class="form-group">
                    <label class="form-label">Full Patient Name</label>
                    <input type="text" class="form-input" id="regName" placeholder="e.g. Sarah Jenkins">
                </div>

                <div class="form-group">
                    <label class="form-label">Email Address</label>
                    <input type="email" class="form-input" id="regEmail" placeholder="e.g. sarah.jenkins@example.com">
                </div>

                <div class="form-group">
                    <label class="form-label">Date of Birth & Gender</label>
                    <input type="text" class="form-input" id="regDobGender" placeholder="MM/DD/YYYY | Female / Male">
                </div>

                <div class="form-group">
                    <label class="form-label">Create Security Password</label>
                    <input type="password" class="form-input" id="regPassword" placeholder="Create strong password">
                </div>

                <button class="btn-primary btn-full" type="button" onclick="registerNewPatient()">Create Account & Access Portal</button>
            </div>

        </div>
    </div>

    <!-- Schedule Medication Reminder Modal (Date & Time Picker) -->
    <div class="login-overlay" id="medModal" style="display: none;" onclick="handleMedModalOverlay(event)">
        <div class="login-modal" style="position: relative; max-width: 500px;">
            <span style="position: absolute; top: 16px; right: 20px; font-size: 1.25rem; cursor: pointer; color: var(--text-muted); font-weight: 700;" onclick="closeMedModal()" title="Close">✕</span>
            <div class="login-header" style="margin-bottom: 20px;">
                <div class="login-logo" style="background: linear-gradient(135deg, #0284c7, #16a34a);">💊</div>
                <div class="login-title">Schedule Medication Reminder</div>
                <div class="login-subtitle">Set date, time, and dosage schedule for your prescription</div>
            </div>

            <div class="form-group">
                <label class="form-label">Medication Name & Strength</label>
                <input type="text" class="form-input" id="medModalName" placeholder="e.g. Atorvastatin 20 mg">
            </div>

            <div class="form-group">
                <label class="form-label">Dosage & Instructions</label>
                <input type="text" class="form-input" id="medModalDosage" placeholder="e.g. Take 1 tablet at bedtime with water">
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 16px;">
                <div class="form-group" style="margin-bottom: 0;">
                    <label class="form-label">Scheduled Date</label>
                    <input type="date" class="form-input" id="medModalDate">
                </div>
                <div class="form-group" style="margin-bottom: 0;">
                    <label class="form-label">Scheduled Time</label>
                    <input type="time" class="form-input" id="medModalTime">
                </div>
            </div>

            <div class="form-group">
                <label class="form-label">Frequency / Routine</label>
                <select class="form-input" id="medModalFreq">
                    <option value="Daily (Morning)">Daily (Morning)</option>
                    <option value="Twice Daily (BID)">Twice Daily (BID)</option>
                    <option value="Bedtime (QHS)">Bedtime (QHS)</option>
                    <option value="Weekly">Weekly</option>
                    <option value="As Needed (PRN)">As Needed (PRN)</option>
                </select>
            </div>

            <div style="display: flex; gap: 10px; margin-top: 20px;">
                <button class="btn-primary" style="flex: 1;" type="button" onclick="saveMedicationReminder()">Save Reminder</button>
                <button class="btn-secondary" type="button" onclick="closeMedModal()">Cancel</button>
            </div>
        </div>
    </div>

    <!-- Top Navigation Navbar -->
    <div class="navbar">
        <div class="brand-logo">
            <div class="brand-icon" style="overflow: hidden; padding: 0; background: #ffffff;">
                <img src="/logo.jpg" alt="Health Companion Logo" style="width: 100%; height: 100%; object-fit: cover; border-radius: 9px;">
            </div>
            <div>Health Companion <span class="brand-badge">Patient Portal</span> <span class="brand-badge" style="background:#dcfce7; color:#15803d;" id="dbStatusBadge">🟢 MongoDB Atlas Live</span></div>
        </div>
        
        <div class="user-nav-profile">
            <div class="user-avatar-badge">
                <div class="avatar-circle" id="navAvatarCircle">AM</div>
                <span id="navUserName">Alex Morgan (ID: #1042-HC)</span>
            </div>
            <button class="btn-secondary" style="font-size: 0.78rem; padding: 4px 10px;" onclick="showLoginOverlay()">Sign Out</button>
        </div>
    </div>

    <!-- Navigation Portal Tabs -->
    <div class="portal-tabs">
        <button class="tab-btn active" id="tab-simplifier" onclick="switchTab('simplifier')">
            <span>📋</span> Clinical Record Simplifier
        </button>
        <button class="tab-btn" id="tab-reminders" onclick="switchTab('reminders')">
            <span>💊</span> Medication Reminders & 💧 Water Intake
        </button>
        <button class="tab-btn" id="tab-tracker" onclick="switchTab('tracker')">
            <span>📈</span> Biomarker Health Tracker
        </button>
    </div>

    <!-- Clinical Disclaimer Notice -->
    <div class="clinical-notice-bar">
        <span>⚠️</span>
        <div><strong>CLINICAL NOTICE:</strong> Educational summaries and doctor preparation guidance. Not a medical diagnosis or medical advice.</div>
    </div>

    <!-- VIEW 1: RECORD SIMPLIFIER & AGENT PORTAL -->
    <div id="view-simplifier">
        <!-- Step 1: Record Ingestion Card -->
        <div class="saas-card">
            <div class="section-header">STEP 01 // RECORD INGESTION</div>
            <div class="card-header-row">
                <div>
                    <div class="card-title">Select or Upload Clinical Record</div>
                    <div class="card-subtitle">Choose a clinical sample benchmark or import your own patient document (PDF/TXT)</div>
                </div>
                <div style="display: flex; gap: 10px;">
                    <button class="btn-secondary" onclick="triggerFileInput()">📤 Upload File</button>
                    <button class="btn-secondary" onclick="toggleCustomText()">✏️ Paste Text</button>
                </div>
            </div>

            <input type="file" id="realFileInput" accept=".pdf,.txt" style="display:none" onchange="handleFileSelected(this)">

            <!-- Drag & Drop Upload Zone -->
            <div class="upload-dropzone">
                <div class="dropzone-title">📁 Drag & Drop or Upload Patient Document (PDF / TXT)</div>
                <div class="dropzone-subtitle">Personal data is scoped strictly to this session and stored in-memory</div>
                <button class="btn-primary" onclick="triggerFileInput()">Select File to Ingest</button>
            </div>

            <!-- Benchmark Cards Grid -->
            <div class="benchmark-grid">
                <div class="bm-card active" id="bm-lab" onclick="selectBenchmark('lab')">
                    <div class="bm-top-row">
                        <span class="bm-category-tag">🧪 Lab Report</span>
                        <span class="bm-active-badge" id="badge-lab">Active Benchmark</span>
                    </div>
                    <div class="bm-title">Comprehensive Metabolic & Lipid Panel</div>
                    <div class="bm-desc">Blood sugar, kidney numbers (eGFR, creatinine), liver enzymes & cholesterol.</div>
                </div>

                <div class="bm-card" id="bm-discharge" onclick="selectBenchmark('discharge')">
                    <div class="bm-top-row">
                        <span class="bm-category-tag">🏥 Hospital Note</span>
                        <span class="bm-active-badge" id="badge-discharge" style="display:none">Active Benchmark</span>
                    </div>
                    <div class="bm-title">Post-Surgical Inpatient Discharge</div>
                    <div class="bm-desc">Laparoscopic cholecystectomy recovery protocol, surgical drain & red-flag symptoms.</div>
                </div>

                <div class="bm-card" id="bm-rx" onclick="selectBenchmark('rx')">
                    <div class="bm-top-row">
                        <span class="bm-category-tag">💊 Pharma Regimen</span>
                        <span class="bm-active-badge" id="badge-rx" style="display:none">Active Benchmark</span>
                    </div>
                    <div class="bm-title">Multi-Therapy Prescription Plan</div>
                    <div class="bm-desc">Cardiovascular & glycemic medication schedule with drug-drug timing cautions.</div>
                </div>
            </div>

            <div class="custom-text-box" id="customInputBox">
                <textarea id="customText" placeholder="Paste custom lab report or discharge notes here..."></textarea>
                <button class="btn-primary" onclick="ingestCustomText()">Process Custom Clinical Text</button>
            </div>
        </div>

        <!-- Step 2: Priority Biomarker Flags -->
        <div class="section-header">STEP 02 // PRIORITY BIOMARKER FLAGS</div>
        <div class="biomarker-grid" id="biomarkerGrid">
            <!-- Dynamically Populated Biomarker Cards -->
        </div>

        <!-- Step 3: Companion Explanation -->
        <div class="section-header">STEP 03 // COMPANION EXPLANATION</div>
        <div class="saas-card">
            <div class="card-header-row">
                <div>
                    <div class="card-title">What Your Record Means</div>
                    <div class="card-subtitle" id="expRecordId">RECORD IDENTIFIER: COMPREHENSIVE METABOLIC & LIPID LAB REPORT</div>
                </div>
                <div style="display: flex; gap: 8px;">
                    <button class="btn-secondary">🔊 Audio Stream</button>
                    <button class="btn-secondary" onclick="copyTranscript()">📋 Copy Transcript</button>
                </div>
            </div>

            <div class="exp-narrative" id="expNarrative">
                Hello. I am here to help you understand your lab report. Think of this document as a check-up for your internal engines—how your body processes sugar, how well your kidneys filter blood, and the level of fats circulating in your bloodstream.
            </div>

            <div id="jargonSection">
                <!-- Jargon Glossary Table -->
            </div>
        </div>

        <!-- Step 4: Recommended Specialists -->
        <div class="section-header">STEP 04 // SPECIALIST CARE RECOMMENDATIONS</div>
        <div id="specialistsContainer">
            <!-- Dynamically Populated Specialist Cards -->
        </div>
    </div>

    <!-- VIEW 2: MEDICATION REMINDERS & WATER INTAKE TRACKER -->
    <div id="view-reminders" style="display: none;">
        <!-- Daily Water Intake Tracker Card -->
        <div class="water-tracker-box">
            <div class="water-header-row">
                <div>
                    <div class="water-title">💧 Daily Hydration & Water Intake Tracker</div>
                    <div style="font-size: 0.85rem; color: #0369a1; margin-top: 2px;">Target: 2,000 mL (8 Glasses / Day) for optimal metabolic & kidney filtration</div>
                </div>
                <div>
                    <span class="water-stat-num" id="waterAmountText">1,250 mL</span>
                    <span style="font-size: 0.9rem; color: #0369a1; font-weight: 600;"> (5 / 8 Glasses)</span>
                </div>
            </div>

            <div class="water-progress-bar">
                <div class="water-progress-fill" id="waterFill" style="width: 62.5%;"></div>
            </div>

            <div style="display: flex; gap: 10px; align-items: center;">
                <button class="btn-primary" onclick="addWater(250)">+ 1 Glass (+250 mL)</button>
                <button class="btn-primary" style="background: #0284c7;" onclick="addWater(500)">+ 2 Glasses (+500 mL)</button>
                <button class="btn-secondary" onclick="resetWater()">Reset Hydration</button>
            </div>
        </div>

        <!-- Medication Schedule & Reminders Card -->
        <div class="saas-card">
            <div class="card-header-row">
                <div>
                    <div class="card-title">💊 Active Medication Schedule & Reminders</div>
                    <div class="card-subtitle">Parsed from active prescription notes with custom date & time schedule alerts</div>
                </div>
                <button class="btn-primary" onclick="openAddMedModal()">+ Schedule Medication Reminder</button>
            </div>

            <div class="med-reminder-grid" id="medGrid">
                <!-- Dynamically Rendered via renderMedications() -->
            </div>
        </div>
    </div>

    <!-- VIEW 3: BIOMARKER HEALTH TRACKER & RECORD HISTORY -->
    <div id="view-tracker" style="display: none;">
        <!-- Health Improvement Metric Cards -->
        <div class="section-header">BIOMARKER HEALTH IMPROVEMENT TRACKER</div>
        
        <div class="progress-stats-grid">
            <div class="stat-card">
                <div class="stat-title">Hemoglobin A1c</div>
                <div class="stat-val-row">
                    <span class="stat-value">6.8%</span>
                    <span class="stat-trend-badge">▼ -1.4% Improv</span>
                </div>
                <div class="stat-sub">Was 8.2% on Initial Visit</div>
                <div class="progress-bar-container">
                    <div class="progress-bar-fill" style="width: 78%;"></div>
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-title">Fasting Blood Glucose</div>
                <div class="stat-val-row">
                    <span class="stat-value">102 mg/dL</span>
                    <span class="stat-trend-badge">▼ -63 mg/dL</span>
                </div>
                <div class="stat-sub">Near Normal Target (70-99)</div>
                <div class="progress-bar-container">
                    <div class="progress-bar-fill" style="width: 88%;"></div>
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-title">LDL Cholesterol</div>
                <div class="stat-val-row">
                    <span class="stat-value">98 mg/dL</span>
                    <span class="stat-trend-badge">▼ Optimal Range</span>
                </div>
                <div class="stat-sub">Was 155 mg/dL High</div>
                <div class="progress-bar-container">
                    <div class="progress-bar-fill" style="width: 92%;"></div>
                </div>
            </div>

            <div class="stat-card">
                <div class="stat-title">Serum Creatinine</div>
                <div class="stat-val-row">
                    <span class="stat-value">1.0 mg/dL</span>
                    <span class="stat-trend-badge">✔ Normal Function</span>
                </div>
                <div class="stat-sub">Kidney Filtration Restored</div>
                <div class="progress-bar-container">
                    <div class="progress-bar-fill" style="width: 95%;"></div>
                </div>
            </div>
        </div>

        <!-- Historical Patient Record Timeline -->
        <div class="saas-card">
            <div class="card-header-row">
                <div>
                    <div class="card-title">Patient Medical Record History & Timeline</div>
                    <div class="card-subtitle">Tracked patient artifacts and automatic simplification reports</div>
                </div>
                <button class="btn-primary" onclick="switchTab('simplifier')">+ Process New Record</button>
            </div>

            <table class="history-table">
                <thead>
                    <tr>
                        <th>Date Processed</th>
                        <th>Document Title & Type</th>
                        <th>Flagged Items</th>
                        <th>Assigned Specialist</th>
                        <th>Health Status</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>Sep 20, 2026</strong></td>
                        <td>Comprehensive Metabolic & Lipid Panel (Lab Report)</td>
                        <td><span class="badge-alert-high">7 Flagged</span></td>
                        <td>Endocrinologist, Cardiologist, Nephrologist</td>
                        <td><span style="color:var(--warning-amber); font-weight:700;">Attention Needed</span></td>
                        <td><button class="btn-secondary" onclick="selectBenchmark('lab'); switchTab('simplifier');">View Report</button></td>
                    </tr>
                    <tr>
                        <td><strong>Sep 05, 2026</strong></td>
                        <td>Post-Surgical Inpatient Discharge (Hospital Note)</td>
                        <td><span class="badge-alert-high">4 Flagged</span></td>
                        <td>Cardiologist, Pulmonologist</td>
                        <td><span style="color:var(--normal-green); font-weight:700;">Improving</span></td>
                        <td><button class="btn-secondary" onclick="selectBenchmark('discharge'); switchTab('simplifier');">View Report</button></td>
                    </tr>
                    <tr>
                        <td><strong>Aug 10, 2026</strong></td>
                        <td>Multi-Therapy Prescription Plan (Pharma Regimen)</td>
                        <td><span style="color:var(--accent-primary); font-weight:700;">Medication Review</span></td>
                        <td>Primary Care Physician</td>
                        <td><span style="color:var(--normal-green); font-weight:700;">Stable</span></td>
                        <td><button class="btn-secondary" onclick="selectBenchmark('rx'); switchTab('simplifier');">View Report</button></td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <!-- Floating Consult AI Button -->
    <button class="floating-consult-btn" onclick="toggleConsultDrawer()">
        <span>💬</span> Consult AI Assistant
    </button>

    <!-- Consult AI Q&A Drawer Modal -->
    <div class="consult-drawer" id="consultDrawer">
        <div class="drawer-header">
            <span>Consult AI Assistant</span>
            <span style="cursor:pointer;" onclick="toggleConsultDrawer()">✕</span>
        </div>
        <div class="drawer-messages" id="drawerMessages">
            <div class="msg-agent">
                Hello! I am your AI Health Companion. Ask me any questions about your medications, water intake goals, or lab report trends.
            </div>
        </div>
        <div class="drawer-input-row">
            <input type="text" class="drawer-input" id="drawerQuestion" placeholder="Ask a question about your report..." onkeypress="handleKeyPress(event)">
            <button class="drawer-send-btn" onclick="sendDrawerQuestion()">Send</button>
        </div>
    </div>

    <script>
        let currentRecordData = null;
        let currentWaterMl = 1250;

        let medicationsList = [
            {
                id: 1,
                name: "Lisinopril 20 mg PO",
                dosage: "Antihypertensive - Take 1 tablet daily with water",
                date: "2026-09-20",
                time: "08:00",
                freq: "Daily (Morning)",
                status: "pending",
                takenTime: null
            },
            {
                id: 2,
                name: "Metformin 1000 mg PO",
                dosage: "Glucose Control - Take twice daily with meals",
                date: "2026-09-20",
                time: "13:00",
                freq: "Twice Daily (BID)",
                status: "pending",
                takenTime: null
            },
            {
                id: 3,
                name: "Furosemide 40 mg PO",
                dosage: "Diuretic - Take at bedtime as directed by cardiologist",
                date: "2026-09-20",
                time: "21:00",
                freq: "Bedtime (QHS)",
                status: "pending",
                takenTime: null
            }
        ];

        const samples = {
            lab: `METROPOLITAN CLINICAL LABORATORY REPORT\\nPATIENT: Synthetic Sample Patient #1042 | AGE: 54 | GENDER: Male\\n\\nTEST NAME                  OBSERVED VALUE        REFERENCE RANGE       UNIT\\n-----------------------------------------------------------------------------\\nFasting Blood Glucose       165.0 H              70.0 - 99.0           mg/dL\\nHemoglobin A1c              8.2 H                4.0 - 5.6             %\\nSerum Creatinine            1.4 H                0.6 - 1.2             mg/dL\\neGFR                        58.0 L               90.0 - 120.0          mL/min/1.73m2\\nTotal Cholesterol           238.0 H              0.0 - 200.0           mg/dL\\nLDL Cholesterol             155.0 H              0.0 - 100.0           mg/dL\\nHDL Cholesterol             38.0 L               40.0 - 100.0          mg/dL\\nTriglycerides               210.0 H              0.0 - 150.0           mg/dL\\n\\nCLINICAL IMPRESSION Notes:\\nPatient demonstrates marked Hyperglycemia with HbA1c elevated at 8.2%, indicative of poorly controlled type 2 diabetes mellitus.\\nAccompanying Dyslipidemia with LDL cholesterol at 155 mg/dL.\\nMild Azotemia noted with Serum Creatinine elevated at 1.4 mg/dL and eGFR at 58 mL/min/1.73m2, suggesting early diabetic Nephropathy workload.\\nPatient reports mild Polyuria and Polydipsia.`,
            discharge: `CITY GENERAL HOSPITAL - DISCHARGE SUMMARY\\nADMISSION DIAGNOSIS: Acute Dyspnea and Orthopnea.\\nDISCHARGE VITAL SIGNS & LABS:\\nSystolic BP: 158.0 mmHg (High)\\nDiastolic BP: 94.0 mmHg (High)\\nWBC: 12.4 x10^3/uL (Leukocytosis)\\nHemoglobin: 11.2 g/dL (Anemia)\\nDISCHARGE MEDICATIONS:\\n1. Lisinopril 20 mg PO daily\\n2. Furosemide 40 mg PO QHS`,
            rx: `VALLEY COMMUNITY HEALTH CENTER - PRESCRIPTION\\n1. Metformin 1000 mg PO BID (Take twice daily with meals to manage Hyperglycemia)\\n2. Lisinopril 10 mg PO QD (Take once daily for Hypertension control)\\n3. Atorvastatin 20 mg PO QHS (Take at bedtime for Dyslipidemia)\\n4. Albuterol Inhaler 90 mcg 2 puffs PRN for sudden Dyspnea.`
        };

        window.onload = function() {
            selectBenchmark('lab');
            renderMedications();
        };

        async function addWater(amount) {
            currentWaterMl = Math.min(3000, currentWaterMl + amount);
            updateWaterDisplay();
            try {
                await fetch('/api/hydration/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: currentPatientEmail, amount_ml: currentWaterMl })
                });
            } catch(e) { console.error("MongoDB Atlas hydration sync error:", e); }
        }

        async function resetWater() {
            currentWaterMl = 0;
            updateWaterDisplay();
            try {
                await fetch('/api/hydration/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: currentPatientEmail, amount_ml: 0 })
                });
            } catch(e) { console.error("MongoDB Atlas hydration sync error:", e); }
        }

        function updateWaterDisplay() {
            const pct = Math.min(100, (currentWaterMl / 2000) * 100);
            document.getElementById('waterAmountText').innerText = `${currentWaterMl} mL`;
            document.getElementById('waterFill').style.width = `${pct}%`;
        }

        /* Medication Schedule & Date/Time Reminders */
        function formatTimeString(timeStr) {
            if (!timeStr) return '08:00 AM';
            const parts = timeStr.split(':');
            let h = parseInt(parts[0], 10);
            const m = parts[1] || '00';
            const ampm = h >= 12 ? 'PM' : 'AM';
            h = h % 12 || 12;
            const hStr = h < 10 ? '0' + h : h;
            return `${hStr}:${m} ${ampm}`;
        }

        function formatDateString(dateStr) {
            if (!dateStr) return 'Today';
            const parts = dateStr.split('-');
            if (parts.length !== 3) return dateStr;
            const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
            const mIdx = parseInt(parts[1], 10) - 1;
            const month = months[mIdx] || parts[1];
            return `${month} ${parseInt(parts[2], 10)}, ${parts[0]}`;
        }

        function renderMedications() {
            const grid = document.getElementById('medGrid');
            if (!grid) return;
            grid.innerHTML = '';

            medicationsList.forEach(med => {
                const card = document.createElement('div');
                card.className = 'med-card';
                card.id = `med-card-${med.id}`;
                
                const formattedTime = formatTimeString(med.time);
                const formattedDate = formatDateString(med.date);

                const isTaken = med.status === 'taken';
                const buttonHtml = isTaken 
                    ? `<div class="med-status-taken">Taken Today at ${med.takenTime} ✅</div>`
                    : `<button class="btn-primary" style="width: 100%;" onclick="markMedicationTaken(${med.id})">Mark as Taken ✅</button>`;

                card.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px;">
                        <span class="med-time-badge">⏰ ${formattedTime} (${med.freq || 'Daily'})</span>
                        <button style="background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 0.9rem;" onclick="deleteMedication(${med.id})" title="Delete Reminder">🗑️</button>
                    </div>
                    <div class="med-name">${med.name}</div>
                    <div class="med-dosage">${med.dosage}</div>
                    <div style="font-size: 0.78rem; color: var(--text-muted); margin-bottom: 12px;">
                        📅 Scheduled Date: <strong style="color: var(--text-primary);">${formattedDate}</strong>
                    </div>
                    ${buttonHtml}
                `;
                grid.appendChild(card);
            });
        }

        function openAddMedModal() {
            const modal = document.getElementById('medModal');
            const today = new Date();
            const yyyy = today.getFullYear();
            const mm = String(today.getMonth() + 1).padStart(2, '0');
            const dd = String(today.getDate()).padStart(2, '0');
            const hh = String(today.getHours()).padStart(2, '0');
            const min = String(today.getMinutes()).padStart(2, '0');

            document.getElementById('medModalDate').value = `${yyyy}-${mm}-${dd}`;
            document.getElementById('medModalTime').value = `${hh}:${min}`;
            document.getElementById('medModalName').value = '';
            document.getElementById('medModalDosage').value = '';

            modal.style.display = 'flex';
        }

        function closeMedModal() {
            document.getElementById('medModal').style.display = 'none';
        }

        function handleMedModalOverlay(e) {
            if (e.target.id === 'medModal') closeMedModal();
        }

        async function saveMedicationReminder() {
            const name = document.getElementById('medModalName').value.trim();
            const dosage = document.getElementById('medModalDosage').value.trim() || 'Take as prescribed';
            const date = document.getElementById('medModalDate').value;
            const time = document.getElementById('medModalTime').value;
            const freq = document.getElementById('medModalFreq').value;

            if (!name) {
                alert("Please enter medication name.");
                return;
            }

            const newMed = {
                id: Date.now(),
                name: name,
                dosage: dosage,
                date: date,
                time: time,
                freq: freq,
                status: 'pending',
                takenTime: null
            };

            medicationsList.unshift(newMed);
            renderMedications();
            closeMedModal();

            // Sync with MongoDB Atlas
            try {
                await fetch('/api/medications/save', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email: currentPatientEmail, medication: newMed })
                });
            } catch(e) { console.error("MongoDB Atlas sync error:", e); }
        }

        async function markMedicationTaken(id) {
            const med = medicationsList.find(m => m.id === id);
            if (med) {
                const now = new Date();
                const hh = String(now.getHours()).padStart(2, '0');
                const min = String(now.getMinutes()).padStart(2, '0');
                med.status = 'taken';
                med.takenTime = formatTimeString(`${hh}:${min}`);
                renderMedications();

                try {
                    await fetch('/api/medications/save', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ email: currentPatientEmail, medication: med })
                    });
                } catch(e) { console.error("MongoDB Atlas sync error:", e); }
            }
        }

        async function deleteMedication(id) {
            medicationsList = medicationsList.filter(m => m.id !== id);
            renderMedications();
            try {
                await fetch(`/api/medications/${id}?email=${encodeURIComponent(currentPatientEmail)}`, { method: 'DELETE' });
            } catch(e) { console.error("MongoDB Atlas delete error:", e); }
        }

        /* Authentication Overlay Handlers */
        function closeLoginOverlay() {
            document.getElementById('loginOverlay').style.display = 'none';
        }

        function handleOverlayClick(e) {
            if (e.target.id === 'loginOverlay') closeLoginOverlay();
        }

        function setAuthMode(mode) {
            if (mode === 'signin') {
                document.getElementById('form-signin').style.display = 'block';
                document.getElementById('form-register').style.display = 'none';
                document.getElementById('btn-toggle-signin').classList.add('active');
                document.getElementById('btn-toggle-register').classList.remove('active');
                document.getElementById('authTitle').innerText = 'Patient Portal Sign In';
                document.getElementById('authSubtitle').innerText = 'Access your clinical record simplifier & health tracker';
            } else {
                document.getElementById('form-signin').style.display = 'none';
                document.getElementById('form-register').style.display = 'block';
                document.getElementById('btn-toggle-signin').classList.remove('active');
                document.getElementById('btn-toggle-register').classList.add('active');
                document.getElementById('authTitle').innerText = 'Patient Registration';
                document.getElementById('authSubtitle').innerText = 'Create your new patient health companion account';
            }
        }

        let currentPatientEmail = "alex.morgan@patient-health.org";

        function clearClinicalPipelineView() {
            ['lab', 'discharge', 'rx'].forEach(k => {
                const bm = document.getElementById(`bm-${k}`);
                if (bm) bm.classList.remove('active');
                const badge = document.getElementById(`badge-${k}`);
                if (badge) badge.style.display = 'none';
            });
            
            document.getElementById('expRecordId').innerText = "NO CLINICAL RECORD INGESTED YET";
            document.getElementById('expNarrative').innerText = "Welcome to Health Companion! Please select a sample benchmark or upload your clinical report (PDF/TXT) above to parse medical jargon, evaluate reference ranges, and generate doctor questions.";
            
            const flagGrid = document.getElementById('biomarkerGrid');
            if (flagGrid) flagGrid.innerHTML = '<div style="color:var(--text-muted); font-weight:600; padding:16px; background:#ffffff; border:1px solid var(--card-border); border-radius:8px;">No active document ingested for this account. Upload a record above to view biomarker flags.</div>';
            
            const jargonSec = document.getElementById('jargonSection');
            if (jargonSec) jargonSec.innerHTML = '';
            
            const specContainer = document.getElementById('specialistsContainer');
            if (specContainer) specContainer.innerHTML = '<div style="color:var(--text-muted); font-weight:600; padding:16px; background:#ffffff; border:1px solid var(--card-border); border-radius:8px;">Upload a clinical report to populate specialist care recommendations.</div>';
        }

        async function loadPatientAccountData(email, isNewRegister = false) {
            currentPatientEmail = email;
            
            // 1. Reset RAG retriever session on server
            try { await fetch('/api/reset_session', { method: 'POST' }); } catch(e) {}

            // 2. Reset AI Consult Chat Drawer
            const msgs = document.getElementById('drawerMessages');
            if (msgs) {
                msgs.innerHTML = `<div class="msg-agent">Hello! I am your AI Health Companion. Ask me any questions about your medications, water intake goals, or lab report trends.</div>`;
            }

            // 3. Reset or load clinical document report view
            if (email === "alex.morgan@patient-health.org") {
                selectBenchmark('lab');
            } else {
                clearClinicalPipelineView();
            }

            // 4. Fetch patient's saved medications from MongoDB Atlas
            try {
                const res = await fetch(`/api/medications?email=${encodeURIComponent(email)}`);
                const data = await res.json();
                if (data.medications && data.medications.length > 0) {
                    medicationsList = data.medications;
                } else {
                    medicationsList = [];
                }
                renderMedications();
            } catch(e) {
                medicationsList = [];
                renderMedications();
            }

            // 5. Fetch patient's saved hydration log from MongoDB Atlas
            try {
                const res = await fetch(`/api/hydration?email=${encodeURIComponent(email)}`);
                const data = await res.json();
                currentWaterMl = data.amount_ml || 0;
                updateWaterDisplay();
            } catch(e) {
                currentWaterMl = 0;
                updateWaterDisplay();
            }
        }

        async function authenticatePatient(customName) {
            let displayName = customName || '';
            const emailInput = document.getElementById('loginEmail');
            let emailVal = emailInput ? emailInput.value.trim() : 'alex.morgan@patient-health.org';

            if (!displayName && emailVal) {
                const localPart = emailVal.split('@')[0];
                displayName = localPart.split(/[._-]/).map(s => s.charAt(0).toUpperCase() + s.slice(1)).join(' ');
            }

            if (!displayName) displayName = 'Alex Morgan';

            const initials = displayName.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) || 'PT';
            document.getElementById('navUserName').innerText = `${displayName} (ID: #1042-HC)`;
            document.getElementById('navAvatarCircle').innerText = initials;
            closeLoginOverlay();

            // Save & Load patient account data from MongoDB Atlas
            await loadPatientAccountData(emailVal, false);

            try {
                const res = await fetch('/api/auth', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: displayName, email: emailVal })
                });
                const data = await res.json();
                if (data.db_connected) {
                    const badge = document.getElementById('dbStatusBadge');
                    if (badge) badge.innerHTML = '🟢 MongoDB Atlas Live';
                }
            } catch(e) { console.error("MongoDB Auth sync error:", e); }
        }

        async function registerNewPatient() {
            const nameInput = document.getElementById('regName').value.trim();
            const emailInput = document.getElementById('regEmail').value.trim();
            const dobInput = document.getElementById('regDobGender').value.trim();
            
            const patientName = nameInput || 'New Patient';
            const patientEmail = emailInput || 'patient@example.com';

            document.getElementById('loginEmail').value = patientEmail;
            
            closeLoginOverlay();
            const initials = patientName.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) || 'PT';
            document.getElementById('navUserName').innerText = `${patientName} (ID: #1042-HC)`;
            document.getElementById('navAvatarCircle').innerText = initials;

            // Load fresh blank session for newly registered patient
            await loadPatientAccountData(patientEmail, true);

            try {
                await fetch('/api/auth', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: patientName, email: patientEmail, dob_gender: dobInput })
                });
            } catch(e) { console.error("MongoDB Register sync error:", e); }

            alert(`Welcome to Health Companion, ${patientName}! Your account has been registered & records reset for your profile.`);
        }

        function showLoginOverlay() {
            document.getElementById('loginOverlay').style.display = 'flex';
        }

        function switchTab(tabName) {
            ['simplifier', 'reminders', 'tracker'].forEach(t => {
                document.getElementById(`view-${t}`).style.display = 'none';
                document.getElementById(`tab-${t}`).classList.remove('active');
            });
            document.getElementById(`view-${tabName}`).style.display = 'block';
            document.getElementById(`tab-${tabName}`).classList.add('active');
        }

        function triggerFileInput() {
            document.getElementById('realFileInput').click();
        }

        function toggleCustomText() {
            const box = document.getElementById('customInputBox');
            box.style.display = box.style.display === 'none' ? 'block' : 'none';
        }

        async function handleFileSelected(input) {
            if (!input.files || input.files.length === 0) return;
            const file = input.files[0];
            const formData = new FormData();
            formData.append('file', file);

            const res = await fetch('/api/upload', { method: 'POST', body: formData });
            const data = await res.json();
            renderPipelineData(data, file.name);
        }

        async function selectBenchmark(key) {
            ['lab', 'discharge', 'rx'].forEach(k => {
                document.getElementById(`bm-${k}`).classList.remove('active');
                document.getElementById(`badge-${k}`).style.display = 'none';
            });
            document.getElementById(`bm-${key}`).classList.add('active');
            document.getElementById(`badge-${key}`).style.display = 'inline-block';

            const text = samples[key];
            const res = await fetch('/api/ingest', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text })
            });
            const data = await res.json();
            renderPipelineData(data, key.toUpperCase() + ' BENCHMARK RECORD');
        }

        async function ingestCustomText() {
            const text = document.getElementById('customText').value;
            if (!text.trim()) return;
            const res = await fetch('/api/ingest', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text })
            });
            const data = await res.json();
            renderPipelineData(data, 'CUSTOM PATIENT ARTIFACT');
        }

        function renderPipelineData(data, recordTitle) {
            currentRecordData = data;
            document.getElementById('expRecordId').innerText = `RECORD IDENTIFIER: ${recordTitle}`;

            const simp = data.simplification_result || {};
            const spec = data.specialist_result || {};

            // 1. Render Priority Biomarker Flags Grid
            const flagGrid = document.getElementById('biomarkerGrid');
            flagGrid.innerHTML = '';
            const flagged = simp.flagged_items || [];

            if (flagged.length === 0) {
                flagGrid.innerHTML = '<div style="color:var(--normal-green); font-weight:600;">All evaluated parameters fall within normal target ranges.</div>';
            } else {
                flagged.forEach(item => {
                    const card = document.createElement('div');
                    card.className = 'flag-card';
                    card.innerHTML = `
                        <div class="flag-card-header">
                            <span class="flag-category">${item.category || 'BIOMARKER'}</span>
                            <span class="badge-alert-high">${item.status || 'HIGH'}</span>
                        </div>
                        <div class="flag-num-row">
                            <span class="flag-num">${item.numeric_value || item.value}</span>
                            <span class="flag-unit">${item.value.replace(/[0-9.]/g, '').trim()}</span>
                        </div>
                        <div class="flag-param-title">${item.parameter}</div>
                        <div class="flag-footer">Target Reference: ${item.reference_range}</div>
                    `;
                    flagGrid.appendChild(card);
                });
            }

            // 2. Render Plain-Language Summary & Glossary
            document.getElementById('expNarrative').innerText = simp.plain_language_summary || "Plain language translation generated.";
            
            const jargonSec = document.getElementById('jargonSection');
            jargonSec.innerHTML = '';
            if (simp.jargon_translations && simp.jargon_translations.length > 0) {
                let html = `
                    <table class="glossary-table">
                        <thead>
                            <tr>
                                <th>Medical Term</th>
                                <th>Everyday Plain Translation</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                simp.jargon_translations.forEach(j => {
                    html += `<tr><td><strong>${j.jargon}</strong></td><td>${j.plain_translation}</td></tr>`;
                });
                html += `</tbody></table>`;
                jargonSec.innerHTML = html;
            }

            // 3. Render Specialist Recommendations Cards
            const specContainer = document.getElementById('specialistsContainer');
            specContainer.innerHTML = '';
            const recs = spec.recommendations || [];

            recs.forEach(rec => {
                const specCard = document.createElement('div');
                specCard.className = 'specialist-card';
                
                let trigHtml = '';
                if (rec.associated_parameters) {
                    rec.associated_parameters.forEach(p => {
                        trigHtml += `<span class="trig-pill">${p}</span>`;
                    });
                }

                let qHtml = '';
                if (rec.doctor_questions) {
                    rec.doctor_questions.forEach((q, idx) => {
                        qHtml += `
                            <div class="q-item">
                                <div class="q-text">
                                    <span class="q-num">Q${idx+1}</span>
                                    <span>"${q}"</span>
                                </div>
                                <span class="copy-icon-btn" onclick="navigator.clipboard.writeText('${q.replace(/'/g, "\\'")}')">📋 Copy</span>
                            </div>
                        `;
                    });
                }

                specCard.innerHTML = `
                    <div class="spec-top-row">
                        <div class="spec-icon-box">🩺</div>
                        <div class="spec-info-col">
                            <div class="spec-name">${rec.specialist}</div>
                            <div class="spec-dept">${rec.department}</div>
                        </div>
                        <div class="timeline-badge">Urgency: ${rec.urgency}</div>
                    </div>
                    <div class="spec-rationale">
                        <strong>Clinical Rationale:</strong> ${rec.reason}
                    </div>
                    <div class="triggered-by-row">
                        <span class="trig-label">Triggered By:</span>
                        ${trigHtml}
                    </div>
                    <div class="questions-box">
                        <div class="q-header-row">
                            <span class="q-header-title">Suggested Questions to Ask Your Doctor</span>
                            <span class="q-header-copy">Click copy icon to save question</span>
                        </div>
                        ${qHtml}
                    </div>
                `;
                specContainer.appendChild(specCard);
            });
        }

        function toggleConsultDrawer() {
            const drawer = document.getElementById('consultDrawer');
            drawer.style.display = drawer.style.display === 'flex' ? 'none' : 'flex';
        }

        function handleKeyPress(e) {
            if (e.key === 'Enter') sendDrawerQuestion();
        }

        async function sendDrawerQuestion() {
            const input = document.getElementById('drawerQuestion');
            const q = input.value.trim();
            if (!q) return;

            const msgs = document.getElementById('drawerMessages');
            msgs.innerHTML += `<div class="msg-user">${q}</div>`;
            input.value = '';
            msgs.scrollTop = msgs.scrollHeight;

            const res = await fetch('/api/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: q })
            });
            const data = await res.json();

            msgs.innerHTML += `<div class="msg-agent">${data.answer.replace(/\\n/g, '<br>')}</div>`;
            msgs.scrollTop = msgs.scrollHeight;
        }

        function copyTranscript() {
            const text = document.getElementById('expNarrative').innerText;
            navigator.clipboard.writeText(text);
            alert("Summary transcript copied to clipboard!");
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def index():
    return HTML_TEMPLATE

@app.get("/logo.jpg")
@app.get("/favicon.ico")
def logo():
    logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.jpg")
    if os.path.exists(logo_path):
        return FileResponse(logo_path, media_type="image/jpeg")
    return JSONResponse(status_code=404, content={"detail": "Logo image not found"})

@app.post("/api/reset_session")
def reset_session():
    global current_session
    current_session = SessionDocumentProcessor()
    return {"status": "success", "message": "Session reset"}

@app.post("/api/auth")
def authenticate_patient(data: dict):
    name = data.get("name", "Alex Morgan")
    email = data.get("email", "alex.morgan@patient-health.org")
    dob_gender = data.get("dob_gender", "")
    
    patient = db_manager.save_patient(name, email, dob_gender)
    return {"status": "success", "patient": patient, "db_connected": db_manager.is_connected}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), email: str = Form("alex.morgan@patient-health.org")):
    contents = await file.read()
    suffix = os.path.splitext(file.filename)[1]
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        raw_text = current_session.load_document(tmp_path)
        res = agent.process_document_ingestion(raw_text, current_session)
        res["raw_text"] = raw_text
        
        # Persist record analysis in MongoDB Atlas
        db_manager.save_clinical_record(file.filename, res, email)
        return JSONResponse(content=res)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@app.post("/api/ingest")
def ingest(data: dict):
    text = data.get("text", "")
    email = data.get("email", "alex.morgan@patient-health.org")
    title = data.get("title", "Clinical Record Ingestion")
    
    res = agent.process_document_ingestion(text, current_session)
    # Persist record analysis in MongoDB Atlas
    db_manager.save_clinical_record(title, res, email)
    return res

@app.post("/api/ask")
def ask(data: dict):
    q = data.get("question", "")
    ans = agent.answer_followup_question(q, current_session)
    return {"answer": ans}

# ---------------------------------------------------------------------------
# MongoDB Atlas Persistent Endpoints
# ---------------------------------------------------------------------------
@app.get("/api/records")
def get_records(email: str = "alex.morgan@patient-health.org"):
    records = db_manager.get_patient_records(email)
    return {"records": records, "db_connected": db_manager.is_connected}

@app.get("/api/medications")
def get_medications(email: str = "alex.morgan@patient-health.org"):
    meds = db_manager.get_medications(email)
    return {"medications": meds, "db_connected": db_manager.is_connected}

@app.post("/api/medications/save")
def save_medication(data: dict):
    email = data.get("email", "alex.morgan@patient-health.org")
    med = db_manager.save_medication(data.get("medication", {}), email)
    return {"status": "success", "medication": med, "db_connected": db_manager.is_connected}

@app.delete("/api/medications/{med_id}")
def delete_medication(med_id: int, email: str = "alex.morgan@patient-health.org"):
    success = db_manager.delete_medication(med_id, email)
    return {"status": "success" if success else "failed"}

@app.get("/api/hydration")
def get_hydration(email: str = "alex.morgan@patient-health.org"):
    ml = db_manager.get_water_intake(email)
    return {"amount_ml": ml, "db_connected": db_manager.is_connected}

@app.post("/api/hydration/save")
def save_hydration(data: dict):
    email = data.get("email", "alex.morgan@patient-health.org")
    amount = data.get("amount_ml", 1250)
    res = db_manager.save_water_intake(amount, email)
    return {"status": "success", "hydration": res, "db_connected": db_manager.is_connected}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8085))
    print(f"Starting Patient Portal Server (MongoDB Atlas Connected) on http://127.0.0.1:{port}...")
    uvicorn.run(app, host="127.0.0.1", port=port)
