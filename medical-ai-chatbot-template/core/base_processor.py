from abc import ABC, abstractmethod
from typing import Dict, List, Any
import json
from pathlib import Path

class BaseDiseaseProcessor(ABC):
    def __init__(self, disease_name: str):
        self.disease_name = disease_name
        self.disease_path = Path(f"diseases/{disease_name}")
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        config_path = self.disease_path / "config.json"
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            return {}
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def generate_insights(self, query: str) -> str:
        pass
    
    def get_basic_info(self) -> Dict[str, Any]:
        return {
            'name': self.config.get('disease_info', {}).get('name', self.disease_name),
            'description': self.config.get('disease_info', {}).get('description', ''),
            'total_records': 0,  # Will be overridden by specific processors
            'categories': self.config.get('disease_info', {}).get('category', 'medical')
        }