"""
database.py
Simple JSON-based database handler
"""

import json
import os
from typing import Dict, Optional, List
from models import Tender, CompanySubmission, Requirement

DATABASE_FILE = "tender_database.json"

class TenderDatabase:
    def __init__(self):
        self.data = {"tenders": {}}
        self.load()
    
    def load(self):
        """Load database from JSON file"""
        if os.path.exists(DATABASE_FILE):
            try:
                with open(DATABASE_FILE, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
                print(f"📊 Loaded {len(self.data['tenders'])} tenders from database")
            except Exception as e:
                print(f"⚠️ Error loading database: {e}")
                self.data = {"tenders": {}}
    
    def save(self):
        """Save database to JSON file"""
        try:
            with open(DATABASE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error saving database: {e}")
    
    def create_tender(self, tender: Tender) -> bool:
        """Create new tender"""
        if tender.tender_id in self.data["tenders"]:
            return False
        self.data["tenders"][tender.tender_id] = tender.dict()
        self.save()
        return True
    
    def get_tender(self, tender_id: str) -> Optional[Dict]:
        """Get tender by ID"""
        return self.data["tenders"].get(tender_id)
    
    def get_all_tenders(self) -> List[Dict]:
        """Get all tenders"""
        return list(self.data["tenders"].values())
    
    def update_tender(self, tender_id: str, tender_data: Dict) -> bool:
        """Update tender"""
        if tender_id not in self.data["tenders"]:
            return False
        self.data["tenders"][tender_id] = tender_data
        self.save()
        return True
    
    def delete_tender(self, tender_id: str) -> bool:
        """Delete tender"""
        if tender_id in self.data["tenders"]:
            del self.data["tenders"][tender_id]
            self.save()
            return True
        return False
    
    def add_company_submission(self, tender_id: str, company_name: str, submission: CompanySubmission) -> bool:
        """Add company submission to tender"""
        tender = self.get_tender(tender_id)
        if not tender:
            return False
        
        if "companies" not in tender:
            tender["companies"] = {}
        
        tender["companies"][company_name] = submission.dict()
        self.update_tender(tender_id, tender)
        return True
    
    def get_company_submission(self, tender_id: str, company_name: str) -> Optional[Dict]:
        """Get company submission"""
        tender = self.get_tender(tender_id)
        if not tender or "companies" not in tender:
            return None
        return tender["companies"].get(company_name)

# Global database instance
db = TenderDatabase()
