import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.base_processor import BaseDiseaseProcessor

class LungCancerProcessor(BaseDiseaseProcessor):
    def __init__(self):
        super().__init__('lung_cancer')
        self.data = self._load_data()
        self.features = self._get_features()
    
    def _load_data(self) -> pd.DataFrame:
        """Load lung cancer dataset"""
        data_path = self.disease_path / "data.csv"
        
        if not data_path.exists():
            print(f"❌ Data file not found: {data_path}")
            return pd.DataFrame()
        
        try:
            df = pd.read_csv(data_path)
            print(f"✅ Loaded {len(df)} lung cancer records")
            return df
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return pd.DataFrame()
    
    def _get_features(self) -> list:
        """Get feature columns (excluding target)"""
        if self.data.empty:
            return []
        
        # Exclude the target column (LUNG_CANCER)
        features = [col for col in self.data.columns if col != 'LUNG_CANCER']
        return features
    
    def get_statistics(self) -> dict:
        """Get comprehensive dataset statistics"""
        if self.data.empty:
            return {"error": "No data available"}
        
        stats = {
            "total_records": len(self.data),
            "features": len(self.features),
            "target_distribution": self._get_target_distribution(),
            "feature_analysis": self._get_feature_analysis(),
            "risk_factors": self._get_risk_factors(),
            "demographic_insights": self._get_demographic_insights(),
            "correlation_insights": self._get_correlation_insights()
        }
        
        return stats
    
    def _get_target_distribution(self) -> dict:
        """Get distribution of cancer cases"""
        if 'LUNG_CANCER' not in self.data.columns:
            return {}
        
        distribution = self.data['LUNG_CANCER'].value_counts().to_dict()
        total = len(self.data)
        
        return {
            "cancer_cases": distribution.get('YES', 0),
            "non_cancer_cases": distribution.get('NO', 0),
            "cancer_rate": round((distribution.get('YES', 0) / total) * 100, 2),
            "total_cases": total
        }
    
    def _get_feature_analysis(self) -> dict:
        """Analyze individual features"""
        if self.data.empty:
            return {}
        
        analysis = {}
        
        for feature in self.features:
            if feature in self.data.columns:
                unique_values = self.data[feature].nunique()
                value_counts = self.data[feature].value_counts().head(5).to_dict()
                
                analysis[feature] = {
                    "unique_values": unique_values,
                    "most_common": value_counts,
                    "data_type": str(self.data[feature].dtype)
                }
        
        return analysis
    
    def _get_risk_factors(self) -> dict:
        """Identify key risk factors"""
        if self.data.empty or 'LUNG_CANCER' not in self.data.columns:
            return {}
        
        risk_factors = {}
        cancer_cases = self.data[self.data['LUNG_CANCER'] == 'YES']
        total_cancer = len(cancer_cases)
        
        if total_cancer == 0:
            return risk_factors
        
        # Analyze each feature as potential risk factor
        for feature in self.features:
            if feature in cancer_cases.columns:
                if feature == 'SMOKING':
                    smokers_with_cancer = len(cancer_cases[cancer_cases[feature] == 1])
                    risk_factors['SMOKING'] = {
                        "cancer_cases_with_factor": smokers_with_cancer,
                        "percentage": round((smokers_with_cancer / total_cancer) * 100, 2),
                        "description": "Smoking history"
                    }
                
                elif feature == 'AGE':
                    avg_age = cancer_cases[feature].mean()
                    risk_factors['AGE'] = {
                        "average_age": round(avg_age, 1),
                        "age_range": f"{cancer_cases[feature].min()}-{cancer_cases[feature].max()}",
                        "description": "Age factor in cancer cases"
                    }
                
                elif feature == 'GENDER':
                    gender_dist = cancer_cases[feature].value_counts().to_dict()
                    risk_factors['GENDER'] = {
                        "distribution": gender_dist,
                        "description": "Gender distribution in cancer cases"
                    }
        
        return risk_factors
    
    def _get_demographic_insights(self) -> dict:
        """Get demographic insights"""
        if self.data.empty:
            return {}
        
        insights = {}
        
        # Gender distribution
        if 'GENDER' in self.data.columns:
            gender_dist = self.data['GENDER'].value_counts().to_dict()
            insights['gender_distribution'] = gender_dist
        
        # Age statistics
        if 'AGE' in self.data.columns:
            insights['age_statistics'] = {
                "mean_age": round(self.data['AGE'].mean(), 1),
                "median_age": self.data['AGE'].median(),
                "age_range": f"{self.data['AGE'].min()}-{self.data['AGE'].max()}"
            }
        
        return insights
    
    def _get_correlation_insights(self) -> dict:
        """Get correlation insights between features and cancer"""
        if self.data.empty or 'LUNG_CANCER' not in self.data.columns:
            return {}
        
        insights = {}
        
        # Convert categorical to numerical for correlation
        data_numeric = self.data.copy()
        data_numeric['LUNG_CANCER'] = data_numeric['LUNG_CANCER'].map({'YES': 1, 'NO': 0})
        
        # Calculate correlations
        correlations = {}
        for feature in self.features:
            if feature in data_numeric.columns:
                if data_numeric[feature].dtype in ['int64', 'float64']:
                    corr = data_numeric[feature].corr(data_numeric['LUNG_CANCER'])
                    if not np.isnan(corr):
                        correlations[feature] = round(corr, 3)
        
        # Sort by absolute correlation value
        sorted_correlations = sorted(correlations.items(), key=lambda x: abs(x[1]), reverse=True)
        
        insights['feature_correlations'] = dict(sorted_correlations[:10])  # Top 10
        insights['strongest_predictors'] = [item[0] for item in sorted_correlations[:5]]
        
        return insights
    
    def generate_insights(self, query: str) -> str:
        """Generate contextual insights based on query"""
        if self.data.empty:
            return "Dataset not available for analysis."
        
        query_lower = query.lower()
        
        # Query-specific insights
        if 'smoking' in query_lower:
            return self._smoking_insights()
        elif 'age' in query_lower:
            return self._age_insights()
        elif 'gender' in query_lower:
            return self._gender_insights()
        elif 'symptom' in query_lower:
            return self._symptom_insights()
        elif 'statistic' in query_lower or 'data' in query_lower:
            return self._general_statistics()
        else:
            return self._general_insights()
    
    def _smoking_insights(self) -> str:
        """Generate smoking-related insights"""
        if 'SMOKING' not in self.data.columns:
            return "Smoking data not available in dataset."
        
        total = len(self.data)
        smokers = len(self.data[self.data['SMOKING'] == 1])
        smokers_pct = round((smokers / total) * 100, 1)
        
        if 'LUNG_CANCER' in self.data.columns:
            cancer_cases = self.data[self.data['LUNG_CANCER'] == 'YES']
            smokers_with_cancer = len(cancer_cases[cancer_cases['SMOKING'] == 1])
            total_cancer = len(cancer_cases)
            
            if total_cancer > 0:
                smoker_cancer_pct = round((smokers_with_cancer / total_cancer) * 100, 1)
                return f"SMOKING ANALYSIS:\n• {smokers_pct}% of patients in dataset are smokers\n• {smoker_cancer_pct}% of cancer patients have smoking history\n• {smokers_with_cancer} out of {total_cancer} cancer cases involve smoking"
        
        return f"SMOKING ANALYSIS:\n• {smokers_pct}% of patients in dataset are smokers ({smokers} out of {total})"
    
    def _age_insights(self) -> str:
        """Generate age-related insights"""
        if 'AGE' not in self.data.columns:
            return "Age data not available in dataset."
        
        avg_age = round(self.data['AGE'].mean(), 1)
        median_age = self.data['AGE'].median()
        age_range = f"{self.data['AGE'].min()}-{self.data['AGE'].max()}"
        
        if 'LUNG_CANCER' in self.data.columns:
            cancer_cases = self.data[self.data['LUNG_CANCER'] == 'YES']
            if len(cancer_cases) > 0:
                cancer_avg_age = round(cancer_cases['AGE'].mean(), 1)
                return f"AGE ANALYSIS:\n• Average age in dataset: {avg_age} years\n• Average age of cancer patients: {cancer_avg_age} years\n• Age range: {age_range} years\n• Median age: {median_age} years"
        
        return f"AGE ANALYSIS:\n• Average age: {avg_age} years\n• Median age: {median_age} years\n• Age range: {age_range} years"
    
    def _gender_insights(self) -> str:
        """Generate gender-related insights"""
        if 'GENDER' not in self.data.columns:
            return "Gender data not available in dataset."
        
        gender_dist = self.data['GENDER'].value_counts()
        total = len(self.data)
        
        insights = "GENDER ANALYSIS:\n"
        for gender, count in gender_dist.items():
            pct = round((count / total) * 100, 1)
            insights += f"• {gender}: {count} patients ({pct}%)\n"
        
        if 'LUNG_CANCER' in self.data.columns:
            cancer_cases = self.data[self.data['LUNG_CANCER'] == 'YES']
            if len(cancer_cases) > 0:
                cancer_gender_dist = cancer_cases['GENDER'].value_counts()
                insights += "Cancer cases by gender:\n"
                for gender, count in cancer_gender_dist.items():
                    insights += f"• {gender}: {count} cases\n"
        
        return insights
    
    def _symptom_insights(self) -> str:
        """Generate symptom-related insights"""
        symptom_features = ['COUGHING', 'SHORTNESS_OF_BREATH', 'CHEST_PAIN', 'WHEEZING', 'FATIGUE']
        available_symptoms = [s for s in symptom_features if s in self.data.columns]
        
        if not available_symptoms:
            return "Symptom data not fully available in dataset."
        
        insights = "SYMPTOM ANALYSIS:\n"
        
        for symptom in available_symptoms:
            symptom_present = len(self.data[self.data[symptom] == 1])
            total = len(self.data)
            pct = round((symptom_present / total) * 100, 1)
            insights += f"• {symptom.replace('_', ' ').title()}: {pct}% of patients\n"
        
        return insights
    
    def _general_statistics(self) -> str:
        """Generate general dataset statistics"""
        total = len(self.data)
        features = len(self.features)
        
        insights = f"DATASET STATISTICS:\n• Total records: {total}\n• Features analyzed: {features}\n"
        
        if 'LUNG_CANCER' in self.data.columns:
            cancer_cases = len(self.data[self.data['LUNG_CANCER'] == 'YES'])
            cancer_rate = round((cancer_cases / total) * 100, 1)
            insights += f"• Cancer cases: {cancer_cases} ({cancer_rate}%)\n"
            insights += f"• Non-cancer cases: {total - cancer_cases}\n"
        
        return insights
    
    def _general_insights(self) -> str:
        """Generate general insights"""
        return f"LUNG CANCER DATASET:\n• {len(self.data)} patient records available\n• {len(self.features)} clinical features analyzed\n• Comprehensive symptom and risk factor data\n• Statistical analysis and correlations available"
    
    def get_basic_info(self) -> dict:
        """Override base method with specific info"""
        info = super().get_basic_info()
        info.update({
            'name': 'Lung Cancer Analysis',
            'description': 'Comprehensive lung cancer dataset with patient symptoms, risk factors, and outcomes',
            'total_records': len(self.data),
            'category': 'Oncology',
            'features': self.features,
            'data_quality': 'complete' if not self.data.empty else 'unavailable'
        })
        return info