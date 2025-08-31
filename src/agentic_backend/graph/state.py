from __future__ import annotations
from typing import TypedDict, List, Dict, Any, Optional

class GraphState(TypedDict, total=False):
    job_id: str
    query: str
    plan: List[str]
    tabs: List[str]
    findings: List[Dict[str, Any]]
    citations: List[Dict[str, str]]
    form_spec: Optional[Dict[str, Any]]
    automation_spec: Optional[Dict[str, Any]]
    overlay_mode: bool
    evidence_zip: Optional[str]
    warnings: List[str]
