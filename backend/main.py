"""
main.py
Main FastAPI application for Tender Compliance System
RAG-based requirements extraction
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
from datetime import datetime
import uuid

from models import (
    Tender, TenderCreate, CompanySubmission
)
from database import db

# Initialize FastAPI app
app = FastAPI(
    title="Tender Compliance System",
    description="AI-Based Tender Requirements Compliance Checker with RAG",
    version="3.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("\n" + "="*70)
print("🚀 SYSTEM INITIALIZATION - RAG VERSION")
print("="*70)

# Load config
print("\n📋 Loading configuration...")
try:
    from config import config
    print("✅ Configuration loaded")
except Exception as e:
    print(f"❌ Config error: {e}")
    import sys
    sys.exit(1)

# Import extractors
print("\n📖 Importing extractors...")
from requirements_extractor import RequirementsExtractor

# Initialize requirements extractor
requirements_extractor = None

print("\n🤖 Initializing RAG Requirements Extractor...")
try:
    from extractor import Extractor
    requirements_extractor = Extractor(
        api_key=config.OPENAI_API_KEY,   # 🔄 changed from GROQ_API_KEY
        model=config.OPENAI_MODEL        # 🔄 changed from GROQ_MODEL
    )
    print("✅ RAG extractor ready (OpenAI)")
except Exception as e:
    print(f"❌ RAG init failed: {e}")
    print("⚠️ Cannot continue without RAG extractor")
    import sys
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Initialize compliance checker
print("\n🔍 Initializing compliance checker...")
from compliance_checker import ComplianceChecker
compliance_checker = ComplianceChecker()
print("✅ Compliance checker ready")

# Create data directories
os.makedirs("data/tenders", exist_ok=True)
os.makedirs("data/uploaded_files", exist_ok=True)

print("\n" + "="*70)
print("✅ READY - RAG SYSTEM ACTIVE")
print("="*70 + "\n")

@app.on_event("startup")
async def startup_event():
    """Load database on startup"""
    db.load()
    print(f"📊 Loaded {len(db.get_all_tenders())} tenders from database")

# ==================== ROOT ====================

@app.get("/")
async def root():
    """Root endpoint"""
    tenders = db.get_all_tenders()
    
    return {
        "message": "Tender Compliance System API",
        "version": "3.0.0",
        "status": "running",
        "extraction_method": "RAG (Retrieval Augmented Generation)",
        "total_tenders": len(tenders),
        "endpoints": {
            "docs": "/docs",
            "tenders": "/api/tenders",
            "health": "/api/health"
        }
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# ==================== TENDER MANAGEMENT ====================

@app.post("/api/tenders/create")
async def create_tender(tender_data: TenderCreate):
    """Create a new tender"""
    try:
        tender_id = f"TND{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:4].upper()}"
        
        tender = Tender(
            tender_id=tender_id,
            tender_name=tender_data.tender_name,
            description=tender_data.description,
            created_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            status="active"
        )
        
        tender_dir = f"data/tenders/{tender_id}"
        os.makedirs(tender_dir, exist_ok=True)
        os.makedirs(f"{tender_dir}/companies", exist_ok=True)
        
        success = db.create_tender(tender)
        
        if success:
            return {
                "success": True,
                "message": "Tender created successfully",
                "tender_id": tender_id,
                "tender": tender.dict()
            }
        else:
            raise HTTPException(status_code=400, detail="Tender ID already exists")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating tender: {str(e)}")

@app.get("/api/tenders")
async def get_all_tenders():
    """Get all tenders"""
    tenders = db.get_all_tenders()
    return {
        "success": True,
        "count": len(tenders),
        "tenders": tenders
    }

@app.get("/api/tenders/{tender_id}")
async def get_tender(tender_id: str):
    """Get tender details"""
    tender = db.get_tender(tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    
    return {
        "success": True,
        "tender": tender
    }

@app.delete("/api/tenders/{tender_id}")
async def delete_tender(tender_id: str):
    """Delete tender"""
    success = db.delete_tender(tender_id)
    
    if success:
        tender_dir = f"data/tenders/{tender_id}"
        if os.path.exists(tender_dir):
            shutil.rmtree(tender_dir)
        
        return {
            "success": True,
            "message": "Tender deleted successfully"
        }
    else:
        raise HTTPException(status_code=404, detail="Tender not found")

# ==================== REQUIREMENTS UPLOAD ====================

@app.post("/api/tenders/{tender_id}/requirements")
async def upload_requirements(tender_id: str, file: UploadFile = File(...)):
    """Upload government requirements document with RAG extraction"""
    try:
        tender = db.get_tender(tender_id)
        if not tender:
            raise HTTPException(status_code=404, detail="Tender not found")
        
        # Save file
        tender_dir = f"data/tenders/{tender_id}"
        filename = f"requirements_{file.filename}"
        filepath = os.path.join(tender_dir, filename)
        
        with open(filepath, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        print(f"\n{'='*70}")
        print(f"📄 RAG REQUIREMENTS EXTRACTION")
        print(f"{'='*70}")
        print(f"File: {filename}")
        print(f"Tender: {tender.get('tender_name')}")
        
        # Extract text from file
        print(f"\n📖 STEP 1: Extracting text from file...")
        basic_extractor = RequirementsExtractor()
        
        ext = filepath.lower().split('.')[-1]
        if ext == 'pdf':
            document_text = basic_extractor.extract_text_from_pdf(filepath)
        elif ext == 'docx':
            document_text = basic_extractor.extract_text_from_docx(filepath)
        else:
            with open(filepath, 'r', encoding='utf-8') as f:
                document_text = f.read()
        
        print(f"✅ Extracted {len(document_text)} characters")
        
        # Extract requirements using RAG
        print(f"\n🎯 STEP 2: RAG extraction...")
        final_requirements = requirements_extractor.extract(document_text)
        
        # Update tender
        tender["requirements_document"] = filename
        tender["requirements"] = [req.dict() for req in final_requirements]
        tender["total_requirements"] = len(final_requirements)
        
        db.update_tender(tender_id, tender)
        
        print(f"\n{'='*70}")
        print(f"✅ EXTRACTION COMPLETE: {len(final_requirements)} requirements")
        print(f"{'='*70}\n")
        
        return {
            "success": True,
            "message": "Requirements uploaded and extracted successfully",
            "total_requirements": len(final_requirements),
            "extraction_method": "RAG (Retrieval Augmented Generation)",
            "requirements": [req.dict() for req in final_requirements]
        }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error uploading requirements: {str(e)}")

@app.get("/api/tenders/{tender_id}/requirements")
async def get_requirements(tender_id: str):
    """Get extracted requirements for a tender"""
    tender = db.get_tender(tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    
    return {
        "success": True,
        "tender_id": tender_id,
        "tender_name": tender.get("tender_name"),
        "total_requirements": tender.get("total_requirements", 0),
        "requirements": tender.get("requirements", [])
    }

# ==================== COMPANY SUBMISSIONS ====================

@app.post("/api/tenders/{tender_id}/companies/{company_name}/upload")
async def upload_company_documents(
    tender_id: str,
    company_name: str,
    document_type: str = Form(...),
    file: UploadFile = File(...)
):
    """Upload company response documents"""
    try:
        tender = db.get_tender(tender_id)
        if not tender:
            raise HTTPException(status_code=404, detail="Tender not found")
        
        company_dir = f"data/tenders/{tender_id}/companies/{company_name}"
        os.makedirs(company_dir, exist_ok=True)
        
        filename = f"{document_type}_{file.filename}"
        filepath = os.path.join(company_dir, filename)
        
        with open(filepath, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        submission = db.get_company_submission(tender_id, company_name)
        
        if not submission:
            submission = CompanySubmission(
                company_name=company_name,
                submission_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                documents={},
                analysis_status="pending"
            ).dict()
        
        submission["documents"][document_type] = filepath
        
        if "companies" not in tender:
            tender["companies"] = {}
        tender["companies"][company_name] = submission
        
        db.update_tender(tender_id, tender)
        
        return {
            "success": True,
            "message": f"{document_type} uploaded successfully for {company_name}",
            "document_count": len(submission["documents"])
        }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error uploading document: {str(e)}")

@app.get("/api/tenders/{tender_id}/companies")
async def get_all_companies(tender_id: str):
    """Get all companies that submitted for a tender"""
    tender = db.get_tender(tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    
    companies = tender.get("companies", {})
    
    return {
        "success": True,
        "tender_id": tender_id,
        "company_count": len(companies),
        "companies": companies
    }

@app.get("/api/tenders/{tender_id}/companies/{company_name}")
async def get_company_submission(tender_id: str, company_name: str):
    """Get company submission details"""
    submission = db.get_company_submission(tender_id, company_name)
    
    if not submission:
        raise HTTPException(status_code=404, detail="Company submission not found")
    
    return {
        "success": True,
        "company_name": company_name,
        "submission": submission
    }

# ==================== COMPLIANCE ANALYSIS ====================

@app.post("/api/tenders/{tender_id}/companies/{company_name}/analyze")
async def analyze_compliance(tender_id: str, company_name: str):
    """Analyze company's compliance with requirements"""
    try:
        tender = db.get_tender(tender_id)
        if not tender:
            raise HTTPException(status_code=404, detail="Tender not found")
        
        submission = db.get_company_submission(tender_id, company_name)
        if not submission:
            raise HTTPException(status_code=404, detail="Company submission not found")
        
        if not tender.get("requirements"):
            raise HTTPException(status_code=400, detail="No requirements found. Upload requirements first.")
        
        if not submission.get("documents"):
            raise HTTPException(status_code=400, detail="No documents uploaded by company")
        
        submission["analysis_status"] = "analyzing"
        tender["companies"][company_name] = submission
        db.update_tender(tender_id, tender)
        
        from models import Requirement
        requirements = [Requirement(**req) for req in tender["requirements"]]
        
        print(f"🔍 Analyzing compliance for {company_name}...")
        # --------------------------------------------------
        # Extract proposal text with page map (TECHNICAL DOC)
        # --------------------------------------------------
        page_map = None
        technical_doc_path = None

        for doc_type, path in submission["documents"].items():
            if "technical" in doc_type.lower() or "proposal" in doc_type.lower():
                technical_doc_path = path
                break

            if technical_doc_path:
                print("📄 Extracting proposal text with page mapping...")
                proposal_text, page_map = requirements_extractor.extract_with_page_map(
                    technical_doc_path
                )
                print(f"✅ Page map created for proposal ({len(page_map)} sentences)")
            else:
                print("⚠️ No technical/proposal document found, page mapping skipped")



        compliance_report = compliance_checker.check_compliance(
            requirements=requirements,
            company_documents=submission["documents"],
            company_name=company_name,
            tender_id=tender_id,
            page_map=page_map
        )
        
        submission["compliance_report"] = compliance_report.dict()
        submission["analysis_status"] = "completed"
        tender["companies"][company_name] = submission
        db.update_tender(tender_id, tender)
        
        return {
            "success": True,
            "message": "Compliance analysis completed",
            "compliance_report": compliance_report.dict()
        }
    
    except Exception as e:
        try:
            if submission:
                submission["analysis_status"] = "failed"
                tender["companies"][company_name] = submission
                db.update_tender(tender_id, tender)
        except:
            pass
        
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error analyzing compliance: {str(e)}")

@app.get("/api/tenders/{tender_id}/companies/{company_name}/report")
async def get_compliance_report(tender_id: str, company_name: str):
    """Get compliance report for a company"""
    submission = db.get_company_submission(tender_id, company_name)
    
    if not submission:
        raise HTTPException(status_code=404, detail="Company submission not found")
    
    compliance_report = submission.get("compliance_report")
    
    if not compliance_report:
        raise HTTPException(status_code=404, detail="Compliance report not found. Run analysis first.")
    
    return {
        "success": True,
        "company_name": company_name,
        "compliance_report": compliance_report
    }

@app.get("/api/tenders/{tender_id}/comparison")
async def compare_companies(tender_id: str):
    """Compare all companies for a tender"""
    tender = db.get_tender(tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    
    companies = tender.get("companies", {})
    
    comparison_data = []
    for company_name, submission in companies.items():
        compliance_report = submission.get("compliance_report")
        
        if compliance_report:
            comparison_data.append({
                "company_name": company_name,
                "compliance_percentage": compliance_report["compliance_percentage"],
                "requirements_met": len(compliance_report["requirements_met"]),
                "requirements_missing": len(compliance_report["requirements_missing"]),
                "requirements_partial": len(compliance_report["requirements_partial"]),
                "total_requirements": compliance_report["total_requirements"],
                "analysis_date": compliance_report["analysis_date"]
            })
    
    comparison_data.sort(key=lambda x: x["compliance_percentage"], reverse=True)
    
    for idx, company in enumerate(comparison_data, 1):
        company["rank"] = idx
    
    return {
        "success": True,
        "tender_id": tender_id,
        "tender_name": tender.get("tender_name"),
        "total_companies": len(comparison_data),
        "comparison": comparison_data
    }

# ==================== STATISTICS ====================

@app.get("/api/statistics")
async def get_statistics():
    """Get overall system statistics"""
    tenders = db.get_all_tenders()
    
    total_tenders = len(tenders)
    active_tenders = len([t for t in tenders if t.get("status") == "active"])
    total_companies = sum(len(t.get("companies", {})) for t in tenders)
    total_requirements = sum(t.get("total_requirements", 0) for t in tenders)
    
    return {
        "success": True,
        "statistics": {
            "total_tenders": total_tenders,
            "active_tenders": active_tenders,
            "total_companies": total_companies,
            "total_requirements": total_requirements,
            "avg_requirements_per_tender": round(total_requirements / total_tenders, 2) if total_tenders > 0 else 0
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
