from typing import Dict, Any
import importlib
import sys
from pathlib import Path
from .disease_detector import DiseaseDetector
from .ai_client import AIClient

class DiseaseManager:
    def __init__(self, config_manager):
        self.config = config_manager
        self.processors = {}
        self.detector = DiseaseDetector()
        self.ai_client = AIClient(config_manager)
        self._load_diseases()
    
    def _load_diseases(self):
        enabled_diseases = self.config.get('diseases.enabled', ['lung_cancer'])
        
        for disease_name in enabled_diseases:
            try:
                processor = self._load_disease_processor(disease_name)
                self.processors[disease_name] = processor
                print(f"✅ Loaded {disease_name}")
            except Exception as e:
                print(f"❌ Failed to load {disease_name}: {e}")
    
    def _load_disease_processor(self, disease_name: str):
        # Add diseases directory to path
        diseases_dir = str(Path("diseases").absolute())
        if diseases_dir not in sys.path:
            sys.path.insert(0, diseases_dir)
        
        # Import the processor
        module_path = f"diseases.{disease_name}.processor"
        module = importlib.import_module(module_path)
        
        # Get processor class
        class_name = f"LungCancerProcessor"  # We know it's lung cancer for now
        processor_class = getattr(module, class_name)
        
        return processor_class()
    
    def process_query(self, user_query: str) -> Dict[str, Any]:
        try:
            detected_diseases = self.detector.detect_diseases(user_query)
            
            if not self.detector.is_medical_query(user_query):
                return self._generate_non_medical_response()
            
            # Get context from available diseases
            disease_context = {}
            for disease in detected_diseases:
                if disease in self.processors:
                    context = self.processors[disease].generate_insights(user_query)
                    disease_context[disease] = context
            
            # Generate AI response
            if disease_context and self.ai_client.is_available():
                prompt = self._create_prompt(user_query, disease_context)
                ai_response = self.ai_client.generate_response(prompt)
            else:
                ai_response = "I can help with lung cancer information. Please ask about symptoms, risks, or dataset insights."
            
            return {
                "query": user_query,
                "detected_diseases": detected_diseases,
                "ai_response": ai_response,
                "metadata": {"total_processors": len(self.processors)}
            }
            
        except Exception as e:
            return {
                "query": user_query,
                "detected_diseases": [],
                "ai_response": f"❌ Error: {str(e)}",
                "metadata": {"error": True}
            }
    
    def _create_prompt(self, query: str, disease_context: Dict[str, Any]) -> str:
        prompt = f"""You are a medical AI assistant with access to disease datasets.

AVAILABLE DATA:
"""
        for disease, context in disease_context.items():
            prompt += f"\n{disease.upper()}:\n{context}\n"
        
        prompt += f"""
INSTRUCTIONS:
1. Provide evidence-based information from the dataset
2. Include relevant statistics
3. Always recommend consulting healthcare professionals
4. Be clear about limitations

USER QUESTION: {query}

Provide a helpful medical response:"""
        
        return prompt
    
    def _generate_non_medical_response(self) -> Dict[str, Any]:
        return {
            "query": "non_medical",
            "detected_diseases": [],
            "ai_response": """I specialize in medical information based on disease datasets. 

I can help you with:
- Disease symptoms and risk factors
- Medical dataset analysis
- Health insights and statistics

Please ask me about medical conditions or health-related topics.""",
            "metadata": {"response_type": "redirect"}
        }
    
    def get_available_diseases(self) -> Dict[str, Dict[str, Any]]:
        diseases_info = {}
        for disease_name, processor in self.processors.items():
            diseases_info[disease_name] = processor.get_basic_info()
        return diseases_info
    
    def get_disease_statistics(self, disease_name: str) -> Dict[str, Any]:
        if disease_name in self.processors:
            return self.processors[disease_name].get_statistics()
        return {"error": f"Disease '{disease_name}' not found"}