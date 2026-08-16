"""
models.py
Data models for Tender Compliance System
"""

from typing import List, Dict, Optional
from pydantic import BaseModel
from datetime import datetime

class Requirement(BaseModel):
    req_id: str
    requirement_text: str
    category: str = "General"
    mandatory: bool = True
    keywords: List[str] = []

class ComplianceResult(BaseModel):
    req_id: str
    requirement_text: str
    status: str  # "met", "missing", "partial"
    confidence_score: float
    matched_sections: List[str] = []
    reasoning: str = ""

class ComplianceReport(BaseModel):
    company_name: str
    tender_id: str
    analysis_date: str
    total_requirements: int
    requirements_met: List[str]
    requirements_missing: List[str]
    requirements_partial: List[str]
    compliance_percentage: float
    detailed_results: List[ComplianceResult]

class CompanySubmission(BaseModel):
    company_name: str
    submission_date: str
    documents: Dict[str, str]  # document_type: filename
    compliance_report: Optional[ComplianceReport] = None
    analysis_status: str = "pending"  # pending, analyzing, completed

class Tender(BaseModel):
    tender_id: str
    tender_name: str
    description: str = ""
    created_date: str
    status: str = "active"  # active, closed, archived
    requirements_document: Optional[str] = None
    requirements: List[Requirement] = []
    total_requirements: int = 0
    companies: Dict[str, CompanySubmission] = {}

class TenderCreate(BaseModel):
    tender_name: str
    description: str = ""

class DocumentUpload(BaseModel):
    document_type: str  # rfp, rfq, rfi, eoi, technical, financial
    company_name: str
