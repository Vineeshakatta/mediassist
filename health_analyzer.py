import json
import os
import re
from openai import OpenAI

class HealthAnalyzer:
    def __init__(self):
        """Initialize the Health Analyzer with OpenAI client"""
        self.api_key = os.getenv("OPENAI_API_KEY", "default_key")
        self.client = OpenAI(api_key=self.api_key)
        
        # Common health metrics patterns
        self.metric_patterns = {
            'blood_pressure': r'(?:blood pressure|BP)[\s:]*(\d{2,3})/(\d{2,3})',
            'cholesterol': r'(?:cholesterol|chol)[\s:]*(\d{1,3}(?:\.\d)?)',
            'glucose': r'(?:glucose|blood sugar|BS)[\s:]*(\d{1,3}(?:\.\d)?)',
            'heart_rate': r'(?:heart rate|HR|pulse)[\s:]*(\d{2,3})',
            'temperature': r'(?:temperature|temp)[\s:]*(\d{2,3}(?:\.\d)?)',
            'weight': r'(?:weight|wt)[\s:]*(\d{2,3}(?:\.\d)?)',
            'height': r'(?:height|ht)[\s:]*(\d{1,3}(?:\.\d)?)'
        }
    
    def analyze_health_report(self, text):
        """
        Analyze health report text using AI and extract key insights
        """
        try:
            # Extract basic metrics using regex
            extracted_metrics = self._extract_basic_metrics(text)
            
            # Get AI analysis
            ai_analysis = self._get_ai_analysis(text)
            
            # Combine results
            result = {
                'summary': ai_analysis.get('summary', ''),
                'concerns': ai_analysis.get('concerns', []),
                'recommendations': ai_analysis.get('recommendations', []),
                'metrics': self._merge_metrics(extracted_metrics, ai_analysis.get('metrics', []))
            }
            
            return result
            
        except Exception as e:
            return {
                'summary': f"Error analyzing report: {str(e)}",
                'concerns': [],
                'recommendations': [],
                'metrics': []
            }
    
    def _extract_basic_metrics(self, text):
        """Extract basic health metrics using regex patterns"""
        metrics = []
        text_lower = text.lower()
        
        for metric_name, pattern in self.metric_patterns.items():
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                if metric_name == 'blood_pressure':
                    systolic, diastolic = match.groups()
                    metrics.append({
                        'name': 'Blood Pressure',
                        'value': f"{systolic}/{diastolic} mmHg",
                        'normal_range': '90-120/60-80 mmHg',
                        'raw_values': {'systolic': int(systolic), 'diastolic': int(diastolic)}
                    })
                else:
                    value = match.group(1)
                    metric_info = {
                        'name': metric_name.replace('_', ' ').title(),
                        'value': f"{value} {self._get_unit(metric_name)}",
                        'normal_range': self._get_normal_range(metric_name),
                        'raw_value': float(value)
                    }
                    metrics.append(metric_info)
        
        return metrics
    
    def _get_unit(self, metric_name):
        """Get appropriate unit for metric"""
        units = {
            'cholesterol': 'mg/dL',
            'glucose': 'mg/dL',
            'heart_rate': 'bpm',
            'temperature': '°F',
            'weight': 'lbs',
            'height': 'ft'
        }
        return units.get(metric_name, '')
    
    def _get_normal_range(self, metric_name):
        """Get normal range for metric"""
        ranges = {
            'cholesterol': '<200 mg/dL',
            'glucose': '70-100 mg/dL (fasting)',
            'heart_rate': '60-100 bpm',
            'temperature': '97-99°F',
            'weight': 'varies by individual',
            'height': 'varies by individual'
        }
        return ranges.get(metric_name, 'consult healthcare provider')
    
    def _get_ai_analysis(self, text):
        """Get comprehensive AI analysis of the health report"""
        try:
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a medical AI assistant that analyzes health reports. 
                        Provide a comprehensive analysis in JSON format with the following structure:
                        {
                            "summary": "A clear, easy-to-understand summary of the health report",
                            "concerns": ["List of any concerning findings or values"],
                            "recommendations": ["List of general health recommendations"],
                            "metrics": [
                                {
                                    "name": "Metric name",
                                    "value": "Value with units",
                                    "status": "normal/high/low/concerning",
                                    "notes": "Additional context or explanation"
                                }
                            ]
                        }
                        
                        Focus on:
                        - Key health indicators
                        - Values outside normal ranges
                        - Overall health trends
                        - General wellness recommendations
                        
                        Always include disclaimers about consulting healthcare professionals.
                        Use simple, non-medical language when possible."""
                    },
                    {
                        "role": "user",
                        "content": f"Please analyze this health report and provide insights:\n\n{text}"
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=1500
            )
            
            content = response.choices[0].message.content
            if content:
                result = json.loads(content)
                return result
            else:
                return {
                    'summary': "AI analysis unavailable: Empty response received.",
                    'concerns': [],
                    'recommendations': ["Consult with a healthcare professional for proper medical advice."],
                    'metrics': []
                }
            
        except Exception as e:
            return {
                'summary': f"AI analysis unavailable: {str(e)}. Please check your OpenAI API key.",
                'concerns': [],
                'recommendations': ["Consult with a healthcare professional for proper medical advice."],
                'metrics': []
            }
    
    def _merge_metrics(self, regex_metrics, ai_metrics):
        """Merge metrics from regex extraction and AI analysis"""
        # Start with regex metrics as they're more reliable for specific values
        merged = regex_metrics.copy()
        
        # Add AI metrics that don't overlap with regex metrics
        regex_names = {metric['name'].lower() for metric in regex_metrics}
        
        for ai_metric in ai_metrics:
            ai_name = ai_metric.get('name', '').lower()
            if ai_name not in regex_names:
                merged.append(ai_metric)
        
        return merged
