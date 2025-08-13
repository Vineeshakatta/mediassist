import re
import datetime
from typing import Dict, List, Any

def sanitize_text(text: str) -> str:
    """
    Clean and sanitize extracted text
    """
    if not text:
        return ""
    
    # Remove extra whitespace and normalize line breaks
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n+', '\n', text)
    
    # Remove special characters that might interfere with processing
    text = re.sub(r'[^\w\s\n\.\,\:\;\-\(\)\/\%]', '', text)
    
    return text.strip()

def format_metric_value(value: Any, metric_type: str) -> str:
    """
    Format metric values for display
    """
    if value is None:
        return "N/A"
    
    try:
        if metric_type == "blood_pressure":
            return str(value)  # Already formatted as "120/80"
        elif metric_type in ["cholesterol", "glucose"]:
            return f"{float(value):.1f}"
        elif metric_type == "heart_rate":
            return f"{int(float(value))}"
        elif metric_type == "temperature":
            return f"{float(value):.1f}"
        else:
            return str(value)
    except (ValueError, TypeError):
        return str(value)

def validate_health_metric(metric_name: str, value: Any) -> Dict[str, Any]:
    """
    Validate health metrics against normal ranges
    """
    validation_rules = {
        'systolic_bp': {'min': 90, 'max': 120, 'unit': 'mmHg'},
        'diastolic_bp': {'min': 60, 'max': 80, 'unit': 'mmHg'},
        'cholesterol': {'min': 0, 'max': 200, 'unit': 'mg/dL'},
        'glucose_fasting': {'min': 70, 'max': 100, 'unit': 'mg/dL'},
        'heart_rate': {'min': 60, 'max': 100, 'unit': 'bpm'},
        'temperature': {'min': 97.0, 'max': 99.0, 'unit': '°F'}
    }
    
    if metric_name not in validation_rules:
        return {'status': 'unknown', 'message': 'No validation rules available'}
    
    rules = validation_rules[metric_name]
    
    try:
        numeric_value = float(value)
        
        if numeric_value < rules['min']:
            return {'status': 'low', 'message': f'Below normal range ({rules["min"]}-{rules["max"]} {rules["unit"]})'}
        elif numeric_value > rules['max']:
            return {'status': 'high', 'message': f'Above normal range ({rules["min"]}-{rules["max"]} {rules["unit"]})'}
        else:
            return {'status': 'normal', 'message': f'Within normal range ({rules["min"]}-{rules["max"]} {rules["unit"]})'}
            
    except (ValueError, TypeError):
        return {'status': 'invalid', 'message': 'Invalid numeric value'}

def extract_dates_from_text(text: str) -> List[str]:
    """
    Extract dates from text to identify report dates
    """
    date_patterns = [
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY or MM-DD-YYYY
        r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',    # YYYY/MM/DD or YYYY-MM-DD
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b',  # Month DD, YYYY
    ]
    
    dates = []
    for pattern in date_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        dates.extend([match.group() for match in matches])
    
    return list(set(dates))  # Remove duplicates

def generate_report_id() -> str:
    """
    Generate a unique report ID for tracking
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"RPT_{timestamp}"

def calculate_bmi(weight_lbs: float, height_ft: float) -> Dict[str, Any]:
    """
    Calculate BMI from weight in pounds and height in feet
    """
    try:
        # Convert to metric
        weight_kg = weight_lbs * 0.453592
        height_m = height_ft * 0.3048
        
        bmi = weight_kg / (height_m ** 2)
        
        # Categorize BMI
        if bmi < 18.5:
            category = "Underweight"
        elif bmi < 25:
            category = "Normal weight"
        elif bmi < 30:
            category = "Overweight"
        else:
            category = "Obese"
        
        return {
            'bmi': round(bmi, 1),
            'category': category,
            'status': 'normal' if 18.5 <= bmi < 25 else 'concerning'
        }
        
    except (ValueError, TypeError, ZeroDivisionError):
        return {'error': 'Invalid height or weight values'}

def format_concerns_list(concerns: List[str]) -> str:
    """
    Format a list of concerns for display
    """
    if not concerns:
        return "No specific concerns identified."
    
    formatted = []
    for i, concern in enumerate(concerns, 1):
        formatted.append(f"{i}. {concern}")
    
    return "\n".join(formatted)

def format_recommendations_list(recommendations: List[str]) -> str:
    """
    Format a list of recommendations for display
    """
    if not recommendations:
        return "Continue following your healthcare provider's guidance."
    
    formatted = []
    for i, rec in enumerate(recommendations, 1):
        formatted.append(f"{i}. {rec}")
    
    return "\n".join(formatted)
