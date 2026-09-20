"""
FastMCP Server for Patient Record Simplifier & Health Companion Agent.
Exposes simplification/flagging tool and specialist finder tool via MCP standard protocol.
"""

from fastmcp import FastMCP
from typing import Dict, List, Any
import sys
import os

# Ensure src path is accessible
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.tools import (
    record_simplification_and_flagging_tool,
    specialist_department_finder_tool
)

mcp = FastMCP("PatientRecordSimplifierMCP")

@mcp.tool()
def simplify_and_flag_record(record_text: str) -> Dict[str, Any]:
    """
    FastMCP Tool: Evaluates patient clinical record text, translates medical jargon,
    and flags out-of-range lab results.
    """
    return record_simplification_and_flagging_tool.invoke({"record_text": record_text})

@mcp.tool()
def find_specialist_department(flagged_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    FastMCP Tool: Maps out-of-range flagged items to specialist departments with action plans.
    """
    return specialist_department_finder_tool.invoke({"flagged_items": flagged_items})

if __name__ == "__main__":
    print("Starting Patient Record Simplifier FastMCP Server on SSE port 8000...")
    mcp.run(transport="sse", port=8000)
