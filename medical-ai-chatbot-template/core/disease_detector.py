import re
from typing import List, Dict, Set
from pathlib import Path
import json

class DiseaseDetector:
    def __init__(self):
        self.disease_keywords = self._load_disease_keywords()
        self.medical_terms = self._load_medical_terms()
    
    def _load_disease_keywords(self) -> Dict[str, List[str]]:
        """Load disease-specific keywords from config files"""
        keywords = {}
        diseases_dir = Path("diseases")
        
        if diseases_dir.exists():
            for disease_folder in diseases_dir.iterdir():
                if disease_folder.is_dir():
                    config_file = disease_folder / "config.json"
                    if config_file.exists():
                        try:
                            with open(config_file, 'r') as f:
                                config = json.load(f)
                                keywords[disease_folder.name] = config.get('keywords', [])
                        except Exception as e:
                            print(f"Error loading keywords for {disease_folder.name}: {e}")
        
        # Default keywords if no config found
        if not keywords:
            keywords = {
                'lung_cancer': [
                    'lung cancer', 'pulmonary cancer', 'lung tumor', 'lung mass',
                    'cough', 'coughing', 'shortness of breath', 'chest pain',
                    'smoking', 'tobacco', 'wheezing', 'fatigue', 'weight loss',
                    'lung', 'respiratory', 'breathing', 'bronchial'
                ]
            }
        
        return keywords
    
    def _load_medical_terms(self) -> Set[str]:
        """Load general medical terms"""
        return {
            'symptoms', 'diagnosis', 'treatment', 'medication', 'disease',
            'condition', 'syndrome', 'disorder', 'infection', 'virus',
            'bacteria', 'pain', 'fever', 'inflammation', 'chronic',
            'acute', 'severe', 'mild', 'moderate', 'health', 'medical',
            'doctor', 'physician', 'hospital', 'clinic', 'patient',
            'risk factors', 'prevention', 'cure', 'therapy', 'surgery',
            'blood test', 'x-ray', 'scan', 'biopsy', 'cancer', 'tumor',
            'benign', 'malignant', 'metastasis', 'stage'
        }
    
    def detect_diseases(self, query: str) -> List[str]:
        """Detect diseases mentioned in the query"""
        query_lower = query.lower()
        detected_diseases = []
        
        for disease, keywords in self.disease_keywords.items():
            for keyword in keywords:
                if keyword.lower() in query_lower:
                    if disease not in detected_diseases:
                        detected_diseases.append(disease)
                    break
        
        # If no specific disease detected but medical terms found, return all available
        if not detected_diseases and self.is_medical_query(query):
            detected_diseases = list(self.disease_keywords.keys())
        
        return detected_diseases
    
    def is_medical_query(self, query: str) -> bool:
        """Check if query is medical-related"""
        query_lower = query.lower()
        
        # Check for direct medical terms
        for term in self.medical_terms:
            if term in query_lower:
                return True
        
        # Check for disease-specific keywords
        for keywords in self.disease_keywords.values():
            for keyword in keywords:
                if keyword.lower() in query_lower:
                    return True
        
        # Check for medical patterns
        medical_patterns = [
            r'\b(what|how|why|when|where)\s+(is|are|does|do|can|will|should)\s+.*\b(disease|condition|symptom|treatment|medication)\b',
            r'\b(symptoms|signs)\s+of\b',
            r'\bcaused?\s+by\b',
            r'\b(risk|factors|prevention|cure|treatment|therapy)\b',
            r'\b(pain|ache|hurt|sore)\b',
            r'\b(doctor|physician|medical|health)\b'
        ]
        
        for pattern in medical_patterns:
            if re.search(pattern, query_lower):
                return True
        
        return False
    
    def get_confidence_score(self, query: str, disease: str) -> float:
        """Calculate confidence score for disease detection"""
        if disease not in self.disease_keywords:
            return 0.0
        
        query_lower = query.lower()
        keywords = self.disease_keywords[disease]
        matches = 0
        
        for keyword in keywords:
            if keyword.lower() in query_lower:
                matches += 1
        
        return min(matches / len(keywords), 1.0)
    
    def add_disease_keywords(self, disease_name: str, keywords: List[str]):
        """Add new disease keywords dynamically"""
        self.disease_keywords[disease_name] = keywords
    
    def get_available_diseases(self) -> List[str]:
        """Get list of available diseases"""
        return list(self.disease_keywords.keys())