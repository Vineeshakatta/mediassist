from datetime import datetime, timedelta
import pytz

class HealthTracker:
    """Manages health tracking features"""
    
    @staticmethod
    def create_medication_reminder(medicine_name, dosage, frequency, times, start_date, end_date=None):
        """Create a medication reminder"""
        est_tz = pytz.timezone('US/Eastern')
        return {
            'id': f"reminder_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'medicine_name': medicine_name,
            'dosage': dosage,
            'frequency': frequency,
            'times': times,
            'start_date': start_date,
            'end_date': end_date,
            'active': True,
            'created_at': datetime.now(est_tz).strftime('%Y-%m-%d %H:%M EST'),
            'history': []
        }
    
    @staticmethod
    def log_medication_taken(reminder, taken_at=None):
        """Log when medication was taken"""
        est_tz = pytz.timezone('US/Eastern')
        if taken_at is None:
            taken_at = datetime.now(est_tz).strftime('%Y-%m-%d %H:%M EST')
        
        reminder['history'].append({
            'taken_at': taken_at,
            'status': 'taken'
        })
        return reminder
    
    @staticmethod
    def create_health_goal(goal_type, target_value, current_value, target_date, notes=''):
        """Create a health goal"""
        est_tz = pytz.timezone('US/Eastern')
        return {
            'id': f"goal_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'goal_type': goal_type,
            'target_value': target_value,
            'current_value': current_value,
            'target_date': target_date,
            'notes': notes,
            'progress': [],
            'status': 'active',
            'created_at': datetime.now(est_tz).strftime('%Y-%m-%d %H:%M EST')
        }
    
    @staticmethod
    def update_goal_progress(goal, new_value, date=None):
        """Update progress on a health goal"""
        est_tz = pytz.timezone('US/Eastern')
        if date is None:
            date = datetime.now(est_tz).strftime('%Y-%m-%d')
        
        goal['progress'].append({
            'date': date,
            'value': new_value,
            'recorded_at': datetime.now(est_tz).strftime('%Y-%m-%d %H:%M EST')
        })
        goal['current_value'] = new_value
        
        # Check if goal is achieved
        if goal['goal_type'] in ['weight_loss', 'blood_pressure_reduction', 'cholesterol_reduction']:
            if new_value <= goal['target_value']:
                goal['status'] = 'achieved'
        elif goal['goal_type'] in ['exercise_minutes', 'steps']:
            if new_value >= goal['target_value']:
                goal['status'] = 'achieved'
        
        return goal
    
    @staticmethod
    def log_symptom(symptom_name, severity, description='', duration='', triggers=''):
        """Log a symptom"""
        est_tz = pytz.timezone('US/Eastern')
        return {
            'id': f"symptom_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'symptom_name': symptom_name,
            'severity': severity,
            'description': description,
            'duration': duration,
            'triggers': triggers,
            'logged_at': datetime.now(est_tz).strftime('%Y-%m-%d %H:%M EST')
        }
    
    @staticmethod
    def analyze_symptom_patterns(symptoms):
        """Analyze patterns in logged symptoms"""
        if not symptoms:
            return {
                'recurring_symptoms': [],
                'severity_trends': {},
                'insights': []
            }
        
        # Count symptom occurrences
        symptom_counts = {}
        severity_by_symptom = {}
        
        for symptom in symptoms:
            name = symptom['symptom_name']
            symptom_counts[name] = symptom_counts.get(name, 0) + 1
            
            if name not in severity_by_symptom:
                severity_by_symptom[name] = []
            severity_by_symptom[name].append(symptom['severity'])
        
        # Find recurring symptoms (3+ occurrences)
        recurring = [name for name, count in symptom_counts.items() if count >= 3]
        
        # Calculate average severity
        severity_trends = {}
        for name, severities in severity_by_symptom.items():
            severity_map = {'mild': 1, 'moderate': 2, 'severe': 3}
            avg_severity = sum(severity_map.get(s, 0) for s in severities) / len(severities)
            severity_trends[name] = 'increasing' if avg_severity > 1.5 else 'stable'
        
        # Generate insights
        insights = []
        if recurring:
            insights.append(f"You have {len(recurring)} recurring symptom(s): {', '.join(recurring)}")
        
        for name, trend in severity_trends.items():
            if trend == 'increasing':
                insights.append(f"{name} shows increasing severity - consider consulting a doctor")
        
        return {
            'recurring_symptoms': recurring,
            'severity_trends': severity_trends,
            'insights': insights
        }
