"""
requirements_extractor.py
Extract requirements from government tender documents
"""

import re
from typing import List, Dict
import fitz
import docx
from models import Requirement

class RequirementsExtractor:
    
    def __init__(self):
        # Keywords that typically indicate requirements
        self.requirement_keywords = [
            'shall', 'must', 'required', 'should', 'needs to',
            'is required to', 'has to', 'will', 'need to'
        ]
        
        # Section headers that typically contain requirements
        self.requirement_sections = [
            'requirements', 'specifications', 'scope of work',
            'technical requirements', 'functional requirements',
            'mandatory requirements', 'eligibility criteria'
        ]
    
    def extract_text_from_pdf(self, filepath: str) -> str:
        """Extract text from PDF"""
        text = ""
        try:
            with fitz.open(filepath) as doc:
                for page in doc:
                    text += page.get_text() + "\n\n"
        except Exception as e:
            print(f"Error extracting PDF: {e}")
        return text
    
    def extract_text_from_docx(self, filepath: str) -> str:
        """Extract text from DOCX"""
        text = ""
        try:
            doc = docx.Document(filepath)
            for para in doc.paragraphs:
                text += para.text + "\n"
        except Exception as e:
            print(f"Error extracting DOCX: {e}")
        return text
    
    def extract_requirements(self, filepath: str) -> List[Requirement]:
        """
        Extract requirements from document
        Returns list of Requirement objects
        """
        # Get file extension
        ext = filepath.lower().split('.')[-1]
        
        # Extract text based on file type
        if ext == 'pdf':
            text = self.extract_text_from_pdf(filepath)
        elif ext == 'docx':
            text = self.extract_text_from_docx(filepath)
        else:
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
        
        requirements = []
        
        # Method 1: Extract numbered requirements
        numbered_reqs = self._extract_numbered_requirements(text)
        requirements.extend(numbered_reqs)
        
        # Method 2: Extract requirements with keywords
        keyword_reqs = self._extract_keyword_requirements(text)
        requirements.extend(keyword_reqs)
        
        # Method 3: Extract from requirement sections
        section_reqs = self._extract_section_requirements(text)
        requirements.extend(section_reqs)
        
        # Remove duplicates and assign IDs
        unique_requirements = self._deduplicate_requirements(requirements)
        
        # Assign unique IDs
        final_requirements = []
        for idx, req in enumerate(unique_requirements, 1):
            req.req_id = f"REQ{idx:03d}"
            final_requirements.append(req)
        
        return final_requirements
    
    def _extract_numbered_requirements(self, text: str) -> List[Requirement]:
        """Extract numbered requirements (1., 2., 1.1, etc.)"""
        requirements = []
        
        # Pattern for numbered lists
        patterns = [
            r'(?:^|\n)(\d+\.)\s+([^\n]+)',  # 1. requirement
            r'(?:^|\n)(\d+\.\d+\.)\s+([^\n]+)',  # 1.1. requirement
            r'(?:^|\n)([a-z]\))\s+([^\n]+)',  # a) requirement
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            for match in matches:
                req_text = match[1].strip()
                if len(req_text) > 20 and self._is_likely_requirement(req_text):
                    requirements.append(Requirement(
                        req_id="",
                        requirement_text=req_text,
                        category=self._categorize_requirement(req_text),
                        keywords=self._extract_keywords(req_text)
                    ))
        
        return requirements
    
    def _extract_keyword_requirements(self, text: str) -> List[Requirement]:
        """Extract sentences containing requirement keywords"""
        requirements = []
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:
                continue
            
            # Check if sentence contains requirement keywords
            for keyword in self.requirement_keywords:
                if keyword in sentence.lower():
                    requirements.append(Requirement(
                        req_id="",
                        requirement_text=sentence,
                        category=self._categorize_requirement(sentence),
                        mandatory=self._is_mandatory(sentence),
                        keywords=self._extract_keywords(sentence)
                    ))
                    break
        
        return requirements
    
    def _extract_section_requirements(self, text: str) -> List[Requirement]:
        """Extract requirements from specific sections"""
        requirements = []
        
        # Find requirement sections
        for section_name in self.requirement_sections:
            pattern = f"(?i){section_name}.*?(?=\n[A-Z]{{2,}}|\Z)"
            sections = re.findall(pattern, text, re.DOTALL)
            
            for section in sections:
                # Extract sentences from section
                sentences = re.split(r'[.!?]+', section)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if len(sentence) > 30 and self._is_likely_requirement(sentence):
                        requirements.append(Requirement(
                            req_id="",
                            requirement_text=sentence,
                            category=self._categorize_requirement(sentence),
                            keywords=self._extract_keywords(sentence)
                        ))
        
        return requirements
    
    def _is_likely_requirement(self, text: str) -> bool:
        """Check if text is likely a requirement"""
        text_lower = text.lower()
        
        # Must contain requirement keyword
        has_keyword = any(kw in text_lower for kw in self.requirement_keywords)
        
        # Should be substantial
        has_length = len(text) > 20
        
        # Should not be a heading
        is_not_heading = not text.isupper() and ':' not in text[:20]
        
        return has_keyword and has_length and is_not_heading
    
    def _is_mandatory(self, text: str) -> bool:
        """Determine if requirement is mandatory"""
        mandatory_words = ['shall', 'must', 'required', 'mandatory']
        text_lower = text.lower()
        return any(word in text_lower for word in mandatory_words)
    
    def _categorize_requirement(self, text: str) -> str:
        """Categorize requirement based on content"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['technical', 'specification', 'performance', 'system']):
            return "Technical"
        elif any(word in text_lower for word in ['financial', 'price', 'cost', 'payment', 'budget']):
            return "Financial"
        elif any(word in text_lower for word in ['compliance', 'certification', 'standard', 'regulation']):
            return "Compliance"
        elif any(word in text_lower for word in ['delivery', 'timeline', 'schedule', 'deadline']):
            return "Timeline"
        elif any(word in text_lower for word in ['experience', 'qualification', 'eligibility']):
            return "Eligibility"
        else:
            return "General"
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from requirement text"""
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                     'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be', 'been'}
        
        words = re.findall(r'\b[a-z]+\b', text.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 3]
        
        # Return unique keywords (max 10)
        return list(set(keywords))[:10]
    
    def _deduplicate_requirements(self, requirements: List[Requirement]) -> List[Requirement]:
        """Remove duplicate requirements"""
        seen = set()
        unique = []
        
        for req in requirements:
            # Normalize text for comparison
            normalized = req.requirement_text.lower().strip()
            if normalized not in seen and len(normalized) > 20:
                seen.add(normalized)
                unique.append(req)
        
        return unique
