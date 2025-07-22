import os
import requests
import json
from typing import Dict, Any, Optional, List
import time
from pathlib import Path

class AIClient:
    def __init__(self, config_manager):
        self.config = config_manager
        self.provider = self.config.get('ai.provider', 'gemini')
        self.model = self.config.get('ai.model', 'models/gemini-2.0-flash')
        self.api_key = self.config.get('ai.api_key') or os.getenv('GEMINI_API_KEY')
        self.rate_limit_delay = 1  # seconds between requests
        self.last_request_time = 0
        
    def is_available(self) -> bool:
        """Check if AI service is available"""
        return bool(self.api_key)
    
    def generate_response(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generate AI response using the configured provider"""
        try:
            self._respect_rate_limit()
            
            if self.provider == 'gemini':
                return self._generate_gemini_response(prompt, max_tokens)
            elif self.provider == 'huggingface':
                return self._generate_huggingface_response(prompt, max_tokens)
            else:
                return self._fallback_response()
                
        except Exception as e:
            print(f"AI generation error: {e}")
            return self._fallback_response()
    
    def _respect_rate_limit(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        
        self.last_request_time = time.time()
    
    def _generate_gemini_response(self, prompt: str, max_tokens: int) -> str:
        """Generate response using Google Gemini API"""
        url = f"https://generativelanguage.googleapis.com/v1beta/{self.model}:generateContent"
        
        headers = {
            'Content-Type': 'application/json',
            'x-goog-api-key': self.api_key
        }
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": max_tokens,
                "stopSequences": []
            },
            "safetySettings": [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if 'candidates' in data and len(data['candidates']) > 0:
            if 'content' in data['candidates'][0]:
                if 'parts' in data['candidates'][0]['content']:
                    return data['candidates'][0]['content']['parts'][0]['text']
        
        return self._fallback_response()
    
    def _generate_huggingface_response(self, prompt: str, max_tokens: int) -> str:
        """Generate response using Hugging Face API (fallback option)"""
        # This requires Hugging Face API key
        hf_api_key = os.getenv('HUGGINGFACE_API_KEY')
        if not hf_api_key:
            return self._fallback_response()
        
        url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
        
        headers = {
            "Authorization": f"Bearer {hf_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_length": max_tokens,
                "temperature": 0.7,
                "do_sample": True
            }
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if isinstance(data, list) and len(data) > 0:
            return data[0].get('generated_text', '').replace(prompt, '').strip()
        
        return self._fallback_response()
    
    def _fallback_response(self) -> str:
        """Fallback response when AI is unavailable"""
        fallback_responses = [
            "I can provide information about the medical conditions in my dataset. Could you please be more specific about what you'd like to know?",
            "Based on the medical data available, I can help with information about symptoms, risk factors, and statistical insights.",
            "I have access to comprehensive medical datasets. Please ask about specific conditions, symptoms, or statistical analysis.",
            "Let me help you with medical information from my dataset. What specific aspect would you like to explore?"
        ]
        
        import random
        return random.choice(fallback_responses)
    
    def analyze_document(self, text: str, document_type: str = "medical") -> str:
        """Analyze uploaded documents"""
        prompt = f"""You are a medical AI assistant analyzing a {document_type} document.

DOCUMENT CONTENT:
{text[:2000]}  # Limit to first 2000 characters

INSTRUCTIONS:
1. Identify key medical information
2. Extract relevant symptoms, conditions, or findings
3. Provide clear, structured analysis
4. Always recommend consulting healthcare professionals
5. Be clear about limitations

Provide a comprehensive analysis:"""
        
        return self.generate_response(prompt, max_tokens=800)
    
    def get_model_info(self) -> Dict[str, str]:
        """Get information about current AI model"""
        return {
            'provider': self.provider,
            'model': self.model,
            'status': 'available' if self.is_available() else 'unavailable',
            'features': ['text_generation', 'document_analysis'] if self.is_available() else []
        }