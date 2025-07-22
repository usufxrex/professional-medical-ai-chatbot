
import yaml
import os
from typing import Dict, Any
from pathlib import Path

class ConfigManager:
    def __init__(self, config_path: str = "config/global_config.yaml"):
        self.config_path = Path(config_path)
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        try:
            with open(self.config_path, 'r') as file:
                config = yaml.safe_load(file)
            
            # Override with environment variables
            if os.getenv('GEMINI_API_KEY'):
                config.setdefault('ai', {})['api_key'] = os.getenv('GEMINI_API_KEY')
                
            return config
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            return {
                'application': {'name': 'Medical AI Chatbot'},
                'api': {'host': '0.0.0.0', 'port': 5000, 'debug': True},
                'diseases': {'enabled': ['lung_cancer']}
            }
    
    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value