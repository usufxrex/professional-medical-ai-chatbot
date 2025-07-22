"""Core Module for Medical AI Chatbot"""

# Import only what's needed to avoid circular imports
__all__ = [
    'ConfigManager',
    'DiseaseManager', 
    'DiseaseDetector',
    'AIClient',
    'BaseDiseaseProcessor'
]

# Note: Actual imports happen in the modules that need them
# This prevents circular import issues