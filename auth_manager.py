import json
import hashlib
import os
from datetime import datetime
import pytz

class AuthManager:
    def __init__(self):
        """Initialize authentication manager"""
        self.users_file = 'users_data.json'
        self.users = self._load_users()
    
    def _load_users(self):
        """Load users from JSON file"""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_users(self):
        """Save users to JSON file"""
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f, indent=2)
    
    def _hash_password(self, password):
        """Hash password using SHA256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, username, password, name, role='member', family_id=None):
        """Create a new user account"""
        if username in self.users:
            return False, "Username already exists"
        
        if not family_id:
            family_id = f"family_{len(self.users) + 1}"
        
        est_tz = pytz.timezone('US/Eastern')
        self.users[username] = {
            'username': username,
            'password': self._hash_password(password),
            'name': name,
            'role': role,
            'family_id': family_id,
            'created_at': datetime.now(est_tz).strftime('%Y-%m-%d %H:%M EST'),
            'profile': {
                'age': None,
                'gender': None,
                'blood_type': None,
                'allergies': [],
                'emergency_contact': None
            },
            'health_data': {
                'reports': [],
                'prescriptions': [],
                'appointments': [],
                'symptoms': [],
                'health_goals': [],
                'medication_reminders': []
            }
        }
        self._save_users()
        return True, "User created successfully"
    
    def authenticate(self, username, password):
        """Authenticate user credentials"""
        if username not in self.users:
            return False, None
        
        if self.users[username]['password'] == self._hash_password(password):
            return True, self.users[username]
        return False, None
    
    def get_user(self, username):
        """Get user data"""
        return self.users.get(username)
    
    def update_user_profile(self, username, profile_data):
        """Update user profile information"""
        if username in self.users:
            self.users[username]['profile'].update(profile_data)
            self._save_users()
            return True
        return False
    
    def update_user_health_data(self, username, health_data):
        """Update user health data"""
        if username in self.users:
            self.users[username]['health_data'].update(health_data)
            self._save_users()
            return True
        return False
    
    def get_family_members(self, family_id):
        """Get all members of a family"""
        members = []
        for username, data in self.users.items():
            if data.get('family_id') == family_id:
                members.append({
                    'username': username,
                    'name': data['name'],
                    'role': data['role'],
                    'profile': data.get('profile', {})
                })
        return members
    
    def add_family_member(self, family_id, username, password, name, role='member'):
        """Add a new family member to existing family"""
        return self.create_user(username, password, name, role, family_id)
    
    def get_user_health_data(self, username, data_type=None):
        """Get specific health data for user"""
        if username not in self.users:
            return None
        
        health_data = self.users[username].get('health_data', {})
        if data_type:
            return health_data.get(data_type, [])
        return health_data
    
    def add_health_data(self, username, data_type, data):
        """Add health data for user"""
        if username in self.users:
            if data_type not in self.users[username]['health_data']:
                self.users[username]['health_data'][data_type] = []
            self.users[username]['health_data'][data_type].append(data)
            self._save_users()
            return True
        return False
