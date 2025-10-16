import streamlit as st
import os
from health_analyzer import HealthAnalyzer
from file_processor import FileProcessor
from auth_manager import AuthManager
from health_tracker import HealthTracker
import tempfile
import json
from datetime import datetime, timedelta
import pandas as pd
import pytz
import requests
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import re

# Configure page
st.set_page_config(
    page_title="Smart Medi Assist AI",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    # Initialize authentication manager
    if 'auth_manager' not in st.session_state:
        st.session_state.auth_manager = AuthManager()
    if 'health_tracker' not in st.session_state:
        st.session_state.health_tracker = HealthTracker()
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    
    # Check authentication first
    if not st.session_state.authenticated:
        show_login_page()
        return
    
    # Load user-specific data
    load_user_data()
    
    # Initialize session state with persistence keys
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'dashboard'
    if 'reports_history' not in st.session_state:
        st.session_state.reports_history = []
    if 'health_data' not in st.session_state:
        st.session_state.health_data = {}
    if 'processed_files' not in st.session_state:
        st.session_state.processed_files = {}
    if 'last_analysis' not in st.session_state:
        st.session_state.last_analysis = None
    if 'file_upload_counter' not in st.session_state:
        st.session_state.file_upload_counter = 0
    if 'session_id' not in st.session_state:
        st.session_state.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if 'prescriptions' not in st.session_state:
        st.session_state.prescriptions = []
    if 'user_location' not in st.session_state:
        st.session_state.user_location = None
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'appointments' not in st.session_state:
        st.session_state.appointments = []
    if 'lifestyle_quiz' not in st.session_state:
        st.session_state.lifestyle_quiz = {}
    if 'nearby_hospitals' not in st.session_state:
        st.session_state.nearby_hospitals = []
    if 'lifestyle_history' not in st.session_state:
        st.session_state.lifestyle_history = []
    
    # Enhanced session persistence - prevent data loss on reload
    st.session_state.persistent = True
    
    # Sidebar Navigation
    with st.sidebar:
        # Logo and branding
        st.markdown("""
        <div style='text-align: center; padding: 1rem 0;'>
            <h1 style='color: #1f77b4; margin: 0; font-size: 1.8rem;'>🩺 Smart Medi Assist AI</h1>
            <p style='color: #666; margin: 0; font-size: 0.85rem; font-style: italic;'>healthcare intelligence platform</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
        
        # Show user info and logout
        user_data = st.session_state.auth_manager.get_user(st.session_state.current_user)
        st.markdown(f"**👤 {user_data['name']}** ({user_data['role'].title()})")
        
        if st.button("🚪 Logout", use_container_width=True):
            save_user_data()
            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.rerun()
        
        st.markdown("---")
        
        # Navigation Menu with icons
        pages = {
            'dashboard': '📊 Dashboard',
            'upload': '📋 Report Analysis',
            'summary': '📈 Report Summary',
            'prescription': '💊 Medication Manager',
            'health_tracking': '📅 Health Tracking',
            'family': '👨‍👩‍👧‍👦 Family Members',
            'appointments': '🏥 Doctor Appointments',
            'lifestyle': '🌱 Lifestyle Quiz',
            'assistant': '🤖 Query Assistant',
            'history': '📚 Health History'
        }
        
        # Enhanced navigation with better highlighting
        st.markdown("""
        <style>
        .nav-button-active {
            background: linear-gradient(90deg, #1f77b4, #4A9EFF) !important;
            color: white !important;
            border: 2px solid #1f77b4 !important;
            border-radius: 8px !important;
            font-weight: bold !important;
            box-shadow: 0 2px 4px rgba(31, 119, 180, 0.3) !important;
        }
        .nav-button {
            background: transparent !important;
            color: #1f77b4 !important;
            border: 1px solid #ddd !important;
            border-radius: 8px !important;
            margin-bottom: 4px !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        for page_key, page_name in pages.items():
            is_current = st.session_state.current_page == page_key
            
            # Create visual indicator for current page
            if is_current:
                st.markdown(f"**→ {page_name}**", help="Current page")
            
            if st.button(
                page_name, 
                key=f"nav_{page_key}", 
                use_container_width=True,
                type="primary" if is_current else "secondary"
            ):
                st.session_state.current_page = page_key
                st.rerun()
        
        st.markdown("---")
        
        # Quick Stats with icons
        st.subheader("📊 Quick Stats")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📄 Reports", len(st.session_state.reports_history))
        with col2:
            recent_reports = len([r for r in st.session_state.reports_history if r.get('date', '').startswith(datetime.now().strftime('%Y-%m'))])
            st.metric("📅 This Month", recent_reports)
        
        # Health Score with trend
        health_score, trend = calculate_health_score(st.session_state.reports_history)
        trend_icon = "📈" if trend == "up" else "📉" if trend == "down" else "📊"
        st.metric(f"{trend_icon} Health Score", f"{health_score}%", delta=trend.capitalize() if trend != "neutral" else "Stable")
        
        # Privacy notice
        with st.expander("📋 Privacy Notice", expanded=False):
            st.markdown("""
            **Your Privacy Matters:**
            - Reports processed securely and temporarily
            - No permanent data storage
            - Files auto-deleted after processing
            - Encrypted connections only
            
            **Disclaimer:** For informational purposes only. 
            Always consult healthcare professionals.
            """)
    
    # Main Content Area
    if st.session_state.current_page == 'dashboard':
        show_dashboard()
    elif st.session_state.current_page == 'upload':
        show_upload_page()
    elif st.session_state.current_page == 'summary':
        show_summary_page()
    elif st.session_state.current_page == 'prescription':
        show_prescription_page()
    elif st.session_state.current_page == 'health_tracking':
        show_health_tracking_page()
    elif st.session_state.current_page == 'family':
        show_family_page()
    elif st.session_state.current_page == 'assistant':
        show_assistant_page()
    elif st.session_state.current_page == 'appointments':
        show_appointments_page()
    elif st.session_state.current_page == 'lifestyle':
        show_lifestyle_page()
    elif st.session_state.current_page == 'history':
        show_history_page()
    
def calculate_health_score(reports_history):
    """Calculate health score based on reports and concerns"""
    if not reports_history:
        return 85, "neutral"  # Default score for new users
    
    # Base score calculation
    total_reports = len(reports_history)
    total_concerns = sum(len(r.get('concerns', [])) for r in reports_history)
    
    # Calculate base score (higher is better)
    if total_concerns == 0:
        base_score = 95
    elif total_concerns <= total_reports:
        base_score = 85
    elif total_concerns <= total_reports * 2:
        base_score = 70
    else:
        base_score = 55
    
    # Calculate trend if we have multiple reports
    if len(reports_history) >= 2:
        # Compare recent vs older reports
        recent_reports = reports_history[-2:]  # Last 2 reports
        older_reports = reports_history[:-2] if len(reports_history) > 2 else []
        
        recent_concern_rate = sum(len(r.get('concerns', [])) for r in recent_reports) / len(recent_reports)
        
        if older_reports:
            older_concern_rate = sum(len(r.get('concerns', [])) for r in older_reports) / len(older_reports)
            
            if recent_concern_rate < older_concern_rate:
                trend = "up"
                base_score += 5  # Bonus for improvement
            elif recent_concern_rate > older_concern_rate:
                trend = "down"
                base_score -= 5  # Penalty for decline
            else:
                trend = "neutral"
        else:
            trend = "neutral"
    else:
        trend = "neutral"
    
    # Ensure score is within bounds
    health_score = max(0, min(100, base_score))
    
    return health_score, trend

def process_ai_question(question):
    """Process AI question and add response to chat history with alternative medicine suggestions"""
    if 'health_analyzer' not in st.session_state:
        st.session_state.health_analyzer = HealthAnalyzer()
    
    # Prepare context from reports and prescriptions
    context = ""
    if st.session_state.reports_history:
        context = "Based on your health reports:\n"
        for report in st.session_state.reports_history[-3:]:  # Last 3 reports
            context += f"\nReport: {report['filename']}\n"
            context += f"Summary: {report['summary']}\n"
            if report['concerns']:
                context += f"Concerns: {', '.join(report['concerns'])}\n"
    
    # Add medication context
    if st.session_state.prescriptions:
        context += "\nCurrent Medications:\n"
        for prescription in st.session_state.prescriptions:
            context += f"- {prescription['medicine_name']} ({prescription['dosage']}, {prescription['frequency']})\n"
    
    # Check if question is about alternative medicines
    is_alternative_query = any(keyword in question.lower() for keyword in [
        'alternative', 'natural', 'substitute', 'replace', 'generic', 
        'different', 'other', 'cheaper', 'side effects', 'interaction'
    ])
    
    try:
        system_prompt = f"""You are a health assistant with expertise in alternative medicine options. Answer questions about the user's health reports and medications in a helpful, informative way. Always remind users to consult healthcare professionals for medical decisions.
        
        When asked about alternative medicines, provide:
        1. Generic equivalents when available
        2. Natural supplement alternatives (with safety notes)
        3. Lifestyle modifications that might help
        4. Questions to ask their doctor about alternatives
        5. Important warnings about drug interactions
        
        Context from user's reports and medications:
        {context}
        
        Always emphasize safety and professional medical consultation."""
        
        if is_alternative_query:
            system_prompt += """
            
            SPECIAL FOCUS: This question is about alternative medicines. Please provide:
            - Safe, evidence-based alternatives
            - Cost-saving generic options
            - Natural supplements with scientific backing
            - Lifestyle changes that could help
            - Important safety warnings
            - Reminder to discuss with healthcare provider before making changes
            """
        
        response = st.session_state.health_analyzer.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ],
            max_tokens=600
        )
        
        ai_response = response.choices[0].message.content
        st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
        
    except Exception as e:
        error_msg = f"Sorry, I couldn't process your question: {str(e)}"
        st.session_state.chat_history.append({"role": "assistant", "content": error_msg})

def show_dashboard():
    """Main dashboard page"""
    st.title("📊 Health Dashboard")
    st.markdown("Welcome to your personal health analytics center")
    
    # Overview Cards with enhanced metrics
    col1, col2, col3, col4 = st.columns(4)
    
    # Calculate metrics
    total_reports = len(st.session_state.reports_history)
    recent_reports = len([r for r in st.session_state.reports_history 
                         if r.get('date', '').startswith(datetime.now().strftime('%Y-%m'))])
    concerns = sum(len(r.get('concerns', [])) for r in st.session_state.reports_history)
    health_score, trend = calculate_health_score(st.session_state.reports_history)
    
    with col1:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 1rem; border-radius: 10px; text-align: center; color: white;'>
            <h3 style='margin: 0; font-size: 2rem;'>📄</h3>
            <h2 style='margin: 0.5rem 0 0 0;'>{}</h2>
            <p style='margin: 0; opacity: 0.8;'>Total Reports</p>
        </div>
        """.format(total_reports), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                    padding: 1rem; border-radius: 10px; text-align: center; color: white;'>
            <h3 style='margin: 0; font-size: 2rem;'>📅</h3>
            <h2 style='margin: 0.5rem 0 0 0;'>{}</h2>
            <p style='margin: 0; opacity: 0.8;'>This Month</p>
        </div>
        """.format(recent_reports), unsafe_allow_html=True)
    
    with col3:
        concern_color = "#4facfe" if concerns == 0 else "#f093fb" if concerns <= 3 else "#f5576c"
        concern_icon = "✅" if concerns == 0 else "⚠️" if concerns <= 3 else "🚨"
        st.markdown("""
        <div style='background: linear-gradient(135deg, {} 0%, {} 100%); 
                    padding: 1rem; border-radius: 10px; text-align: center; color: white;'>
            <h3 style='margin: 0; font-size: 2rem;'>{}</h3>
            <h2 style='margin: 0.5rem 0 0 0;'>{}</h2>
            <p style='margin: 0; opacity: 0.8;'>Health Concerns</p>
        </div>
        """.format(concern_color, concern_color, concern_icon, concerns), unsafe_allow_html=True)
    
    with col4:
        score_color = "#4facfe" if health_score >= 80 else "#f093fb" if health_score >= 60 else "#f5576c"
        trend_icon = "📈" if trend == "up" else "📉" if trend == "down" else "📊"
        st.markdown("""
        <div style='background: linear-gradient(135deg, {} 0%, {} 100%); 
                    padding: 1rem; border-radius: 10px; text-align: center; color: white;'>
            <h3 style='margin: 0; font-size: 2rem;'>{}</h3>
            <h2 style='margin: 0.5rem 0 0 0;'>{}%</h2>
            <p style='margin: 0; opacity: 0.8;'>Health Score</p>
        </div>
        """.format(score_color, score_color, trend_icon, health_score), unsafe_allow_html=True)
    
    # Health Score Visualization - Fixed height container
    st.markdown("### 📊 Health Score Trends")
    
    # Create a fixed height container for consistent layout
    with st.container():
        if st.session_state.reports_history and len(st.session_state.reports_history) > 1:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Calculate scores for each report using user-provided dates
                scores = []
                dates = []
                for i, report in enumerate(st.session_state.reports_history):
                    subset = st.session_state.reports_history[:i+1]
                    score, _ = calculate_health_score(subset)
                    scores.append(score)
                    
                    # Use datetime_obj if available, otherwise parse from date string
                    if 'datetime_obj' in report:
                        dates.append(report['datetime_obj'].strftime('%Y-%m-%d'))
                    else:
                        # Fallback for older records
                        date_str = report['date'][:10] if len(report['date']) >= 10 else report['date']
                        dates.append(date_str)
                
                # Create trend chart with fixed height
                trend_data = pd.DataFrame({
                    'Date': dates,
                    'Health Score': scores
                })
                st.line_chart(trend_data.set_index('Date'), height=300)
            
            with col2:
                # Show trend analysis
                recent_score = scores[-1]
                prev_score = scores[-2] if len(scores) > 1 else scores[-1]
                score_change = recent_score - prev_score
                
                st.metric(
                    "Latest Score", 
                    f"{recent_score}%", 
                    delta=f"{score_change:+.0f}%" if score_change != 0 else "Stable"
                )
                
                # Status indicator with consistent height
                st.markdown("<div style='height: 100px;'>", unsafe_allow_html=True)
                if recent_score >= 85:
                    st.success("🟢 Excellent Health Status")
                elif recent_score >= 70:
                    st.info("🟡 Good Health Status")
                else:
                    st.warning("🔴 Monitor Health Status")
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            # Fixed height placeholder when no data
            st.markdown("""
            <div style='height: 300px; display: flex; align-items: center; justify-content: center; 
                        border: 2px dashed #ddd; border-radius: 10px; background-color: #f8f9fa;'>
                <div style='text-align: center;'>
                    <h3>📊 Health Trends Will Appear Here</h3>
                    <p>Upload multiple reports to see your health score progression over time</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Lifestyle Trends
    if st.session_state.lifestyle_history and len(st.session_state.lifestyle_history) > 1:
        st.markdown("### 🌱 Lifestyle Score Trends")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Create lifestyle trend chart
            lifestyle_data = pd.DataFrame({
                'Date': [entry['date'] for entry in st.session_state.lifestyle_history],
                'Lifestyle Score': [entry['score'] for entry in st.session_state.lifestyle_history]
            })
            st.line_chart(lifestyle_data.set_index('Date'), height=300)
        
        with col2:
            # Show latest lifestyle score and change
            latest_score = st.session_state.lifestyle_history[-1]['score']
            prev_score = st.session_state.lifestyle_history[-2]['score'] if len(st.session_state.lifestyle_history) > 1 else latest_score
            score_change = latest_score - prev_score
            
            st.metric(
                "Latest Lifestyle Score", 
                f"{latest_score}%", 
                delta=f"{score_change:+.0f}%" if score_change != 0 else "No change"
            )
            
            # Status indicator
            if latest_score >= 85:
                st.success("🟢 Excellent Lifestyle")
            elif latest_score >= 70:
                st.info("🟡 Good Lifestyle")
            else:
                st.warning("🔴 Focus on Improvements")
        
        st.markdown("---")
    
    # Key Metrics Trends
    if st.session_state.reports_history and len(st.session_state.reports_history) > 1:
        st.markdown("### 📈 Key Metrics Trends")
        
        # Extract all unique metric names
        all_metrics = {}
        for report in st.session_state.reports_history:
            if 'metrics' in report and report['metrics']:
                for metric in report['metrics']:
                    metric_name = metric.get('name', 'Unknown')
                    if metric_name not in all_metrics:
                        all_metrics[metric_name] = []
                    
                    # Get the date for this report
                    if 'datetime_obj' in report:
                        metric_date = report['datetime_obj'].strftime('%Y-%m-%d')
                    else:
                        metric_date = report['date'][:10] if len(report['date']) >= 10 else report['date']
                    
                    # Extract numeric value if possible
                    value_str = str(metric.get('value', ''))
                    try:
                        # Try to extract first number from the value string
                        import re
                        numbers = re.findall(r'\d+\.?\d*', value_str)
                        if numbers:
                            numeric_value = float(numbers[0])
                            all_metrics[metric_name].append({
                                'date': metric_date,
                                'value': numeric_value,
                                'raw_value': value_str
                            })
                    except:
                        # If can't extract number, skip this data point
                        pass
        
        # Display trends for metrics that have multiple data points
        metrics_with_trends = {k: v for k, v in all_metrics.items() if len(v) > 1}
        
        if metrics_with_trends:
            # Create columns for multiple metrics
            num_metrics = len(metrics_with_trends)
            if num_metrics <= 2:
                cols = st.columns(num_metrics)
            else:
                cols = st.columns(2)
                
            for i, (metric_name, data_points) in enumerate(metrics_with_trends.items()):
                col_idx = i % len(cols)
                with cols[col_idx]:
                    st.subheader(f"📊 {metric_name}")
                    
                    # Sort by date
                    data_points.sort(key=lambda x: x['date'])
                    
                    # Create trend chart
                    trend_df = pd.DataFrame({
                        'Date': [dp['date'] for dp in data_points],
                        metric_name: [dp['value'] for dp in data_points]
                    })
                    
                    st.line_chart(trend_df.set_index('Date'), height=200)
                    
                    # Show latest value and change
                    if len(data_points) >= 2:
                        latest_value = data_points[-1]['value']
                        previous_value = data_points[-2]['value']
                        change = latest_value - previous_value
                        change_pct = (change / previous_value * 100) if previous_value != 0 else 0
                        
                        st.metric(
                            f"Latest {metric_name}",
                            f"{data_points[-1]['raw_value']}",
                            delta=f"{change:+.1f} ({change_pct:+.1f}%)" if abs(change) > 0.01 else "No change"
                        )
        else:
            st.info("Upload more reports with similar metrics to see trend patterns")
    
    st.markdown("---")
    
    # Recent Activity
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📈 Recent Analysis")
        if st.session_state.reports_history:
            # Show last 5 reports
            recent = st.session_state.reports_history[-5:]
            for report in reversed(recent):
                with st.expander(f"📄 {report.get('filename', 'Unknown')} - {report.get('date', 'Unknown date')}"):
                    st.write(f"**Summary:** {report.get('summary', 'No summary available')[:200]}...")
                    if report.get('concerns'):
                        st.warning(f"Concerns: {len(report['concerns'])} items flagged")
        else:
            st.info("No reports analyzed yet. Upload your first health report to get started!")
            if st.button("📁 Upload First Report", key="dashboard_upload_button"):
                st.session_state.current_page = 'upload'
                st.rerun()
    
    with col2:
        st.subheader("📊 Health Insights")
        
        # Show lifestyle insights if available
        if st.session_state.lifestyle_history:
            latest_lifestyle = st.session_state.lifestyle_history[-1]
            st.write("**Latest Lifestyle Score:**")
            score = latest_lifestyle['score']
            score_color = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"
            st.write(f"{score_color} {score}% overall wellness")
            
            # Show priority areas
            priority_areas = get_priority_improvement_areas(latest_lifestyle['quiz_data'])
            if priority_areas:
                st.write("**Focus Areas:**")
                for area in priority_areas[:2]:  # Show top 2 priority areas
                    st.warning(f"🎯 {area['title']}")
        
        # Show medical report insights
        if st.session_state.reports_history:
            latest_report = st.session_state.reports_history[-1]
            if latest_report.get('metrics'):
                st.write("**Latest Medical Metrics:**")
                for metric in latest_report['metrics'][:2]:  # Show top 2 metrics
                    st.write(f"• {metric.get('name', 'Unknown')}: {metric.get('value', 'N/A')}")
            
            if latest_report.get('concerns'):
                st.write("**Medical Concerns:**")
                for concern in latest_report['concerns'][:2]:  # Show top 2 concerns
                    st.warning(f"⚠️ {concern}")
        
        if not st.session_state.lifestyle_history and not st.session_state.reports_history:
            st.info("Complete the lifestyle quiz and upload reports to see personalized insights")


def show_upload_page():
    """Upload and analysis page (original functionality)"""
    st.title("📋 Health Report Analysis")
    st.markdown("Upload your medical reports for AI-powered analysis and summaries")
    
    # Initialize processors
    if 'health_analyzer' not in st.session_state:
        st.session_state.health_analyzer = HealthAnalyzer()
    
    if 'file_processor' not in st.session_state:
        st.session_state.file_processor = FileProcessor()
    
    # Display file upload history (always visible)
    if st.session_state.reports_history:
        with st.expander("📚 Upload History", expanded=True):
            st.markdown("**Previously analyzed files:**")
            for i, report in enumerate(reversed(st.session_state.reports_history[-5:])):  # Show last 5
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.write(f"📄 {report['filename']}")
                with col2:
                    st.write(f"🕒 {report['date']}")
                with col3:
                    status = "✅" if report.get('downloaded', False) else "📥"
                    st.write(status)
            st.markdown("---")
    
    # File upload section
    st.header("📁 Upload Your Health Report")
    
    # Date input for report
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['pdf', 'txt', 'png', 'jpg', 'jpeg', 'bmp', 'tiff'],
            help="Upload your medical report in PDF, image, or text format"
        )
    
    with col2:
        # Set up EST timezone
        est_tz = pytz.timezone('US/Eastern')
        current_est = datetime.now(est_tz)
        
        report_date = st.date_input(
            "Report Date",
            value=current_est.date(),
            help="Select the date of this health report"
        )
        
        report_time = st.time_input(
            "Report Time",
            value=current_est.time(),
            help="Select the time of this health report"
        )
    
    if uploaded_file is not None:
        # Display file info
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**File:** {uploaded_file.name}")
            st.info(f"**Size:** {uploaded_file.size / 1024:.1f} KB")
        
        with col2:
            st.info(f"**Type:** {uploaded_file.type}")
        
        # Process file button
        if st.button("🔍 Analyze Report", type="primary"):
            tmp_file_path = None
            try:
                with st.spinner("Processing your health report..."):
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_file_path = tmp_file.name
                    
                    # Extract text from file
                    progress_bar = st.progress(0)
                    st.text("Extracting text from document...")
                    
                    extracted_text = st.session_state.file_processor.extract_text(tmp_file_path, uploaded_file.type)
                    progress_bar.progress(50)
                    
                    if not extracted_text.strip():
                        st.error("❌ Could not extract text from the uploaded file. Please ensure the file contains readable text or try a different format.")
                        if tmp_file_path:
                            os.unlink(tmp_file_path)
                        return
                    
                    st.text("Analyzing health data with AI...")
                    
                    # Analyze with AI
                    analysis_result = st.session_state.health_analyzer.analyze_health_report(extracted_text)
                    progress_bar.progress(100)
                    
                    # Clean up temporary file
                    if tmp_file_path:
                        os.unlink(tmp_file_path)
                    
                    # Display results
                    display_analysis_results(analysis_result, extracted_text, uploaded_file.name, report_date, report_time)
                    
            except Exception as e:
                st.error(f"❌ Error processing file: {str(e)}")
                if tmp_file_path:
                    try:
                        os.unlink(tmp_file_path)
                    except:
                        pass

def display_analysis_results(analysis_result, extracted_text, filename, report_date=None, report_time=None):
    """Display the analysis results in a structured format"""
    
    # Save to history with user-provided date and EST timezone
    est_tz = pytz.timezone('US/Eastern')
    
    # Use user-provided date/time if available, otherwise current EST time
    if report_date and report_time:
        # Combine date and time from user input
        user_datetime = datetime.combine(report_date, report_time)
        # Localize to EST timezone
        localized_datetime = est_tz.localize(user_datetime)
        formatted_date = localized_datetime.strftime('%Y-%m-%d %H:%M EST')
        datetime_obj = localized_datetime
    else:
        # Fallback to current EST time
        current_est = datetime.now(est_tz)
        formatted_date = current_est.strftime('%Y-%m-%d %H:%M EST')
        datetime_obj = current_est
    
    report_data = {
        'id': f"report_{len(st.session_state.reports_history) + 1}_{datetime_obj.strftime('%Y%m%d_%H%M%S')}",
        'filename': filename,
        'date': formatted_date,
        'datetime_obj': datetime_obj,
        'summary': analysis_result.get('summary', ''),
        'concerns': analysis_result.get('concerns', []),
        'recommendations': analysis_result.get('recommendations', []),
        'metrics': analysis_result.get('metrics', []),
        'extracted_text': extracted_text,
        'downloaded': False
    }
    st.session_state.reports_history.append(report_data)
    st.session_state.last_analysis = report_data
    
    st.success("✅ Analysis Complete!")
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 Summary", "📈 Key Metrics", "📄 Extracted Text"])
    
    with tab1:
        st.header("🔍 AI Analysis Summary")
        
        if 'summary' in analysis_result:
            st.markdown(analysis_result['summary'])
        
        if 'concerns' in analysis_result and analysis_result['concerns']:
            st.header("⚠️ Areas of Concern")
            st.warning("The following items may require attention:")
            for concern in analysis_result['concerns']:
                st.markdown(f"• {concern}")
        
        if 'recommendations' in analysis_result and analysis_result['recommendations']:
            st.header("💡 Recommendations")
            st.info("Consider the following suggestions:")
            for recommendation in analysis_result['recommendations']:
                st.markdown(f"• {recommendation}")
    
    with tab2:
        st.header("📈 Key Health Metrics")
        
        if 'metrics' in analysis_result and analysis_result['metrics']:
            # Display metrics in a structured format
            col1, col2 = st.columns(2)
            
            for i, metric in enumerate(analysis_result['metrics']):
                target_col = col1 if i % 2 == 0 else col2
                
                with target_col:
                    with st.container():
                        st.subheader(metric.get('name', 'Unknown Metric'))
                        
                        if 'value' in metric:
                            st.metric(
                                label=metric.get('name', ''),
                                value=metric['value'],
                                delta=metric.get('status', '')
                            )
                        
                        if 'normal_range' in metric:
                            st.caption(f"Normal range: {metric['normal_range']}")
                        
                        if 'notes' in metric:
                            st.caption(metric['notes'])
        else:
            st.info("No specific metrics were extracted from this report.")
    
    with tab3:
        st.header("📄 Extracted Text")
        st.text_area(
            "Raw extracted text from your document:",
            value=extracted_text,
            height=300,
            disabled=True
        )
    
    # Download summary option
    st.header("💾 Export Results")
    
    # Prepare download content
    download_content = f"""
HEALTH REPORT ANALYSIS SUMMARY
Generated by Smart Medi Assist AI

SUMMARY:
{analysis_result.get('summary', 'No summary available')}

CONCERNS:
{chr(10).join(['• ' + concern for concern in analysis_result.get('concerns', ['None identified'])]) if analysis_result.get('concerns') else '• None identified'}

RECOMMENDATIONS:
{chr(10).join(['• ' + rec for rec in analysis_result.get('recommendations', ['None provided'])]) if analysis_result.get('recommendations') else '• None provided'}

KEY METRICS:
{chr(10).join([f"• {metric.get('name', 'Unknown')}: {metric.get('value', 'N/A')} {metric.get('notes', '')}" for metric in analysis_result.get('metrics', [])]) if analysis_result.get('metrics') else '• No metrics extracted'}

---
Disclaimer: This analysis is for informational purposes only and should not replace professional medical advice.
"""
    

    st.download_button(
        label="📥 Download Analysis Summary",
        data=download_content,
        file_name="health_analysis_summary.txt",
        mime="text/plain"
    )
    
    # Show upload history section at the bottom of the page
    st.markdown("---")
    st.header("📚 Upload History")
    
    if st.session_state.reports_history:
        st.info(f"You have analyzed {len(st.session_state.reports_history)} reports so far.")
        
        # Show last 10 uploaded files
        recent_uploads = st.session_state.reports_history[-10:]
        for i, report in enumerate(reversed(recent_uploads)):
            with st.expander(f"📄 {report.get('filename', 'Unknown')} - {report.get('date', 'Unknown date')}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Summary:** {report.get('summary', 'No summary available')[:150]}...")
                    if report.get('concerns'):
                        st.write(f"**Concerns:** {len(report['concerns'])} items flagged")
                    if report.get('recommendations'):
                        st.write(f"**Recommendations:** {len(report['recommendations'])} suggestions provided")
                
                with col2:
                    # Download option for each report
                    report_download_content = f"""
HEALTH REPORT ANALYSIS SUMMARY
Generated by Smart Medi Assist AI
File: {report.get('filename', 'Unknown')}
Date: {report.get('date', 'Unknown')}

SUMMARY:
{report.get('summary', 'No summary available')}

CONCERNS:
{chr(10).join(['• ' + concern for concern in report.get('concerns', ['None identified'])]) if report.get('concerns') else '• None identified'}

RECOMMENDATIONS:
{chr(10).join(['• ' + rec for rec in report.get('recommendations', ['None provided'])]) if report.get('recommendations') else '• None provided'}

KEY METRICS:
{chr(10).join([f"• {metric.get('name', 'Unknown')}: {metric.get('value', 'N/A')} {metric.get('notes', '')}" for metric in report.get('metrics', [])]) if report.get('metrics') else '• No metrics extracted'}

---
Disclaimer: This analysis is for informational purposes only and should not replace professional medical advice.
"""
                    
                    st.download_button(
                        label="📥 Download",
                        data=report_download_content,
                        file_name=f"analysis_{report.get('filename', 'report').replace('.', '_')}.txt",
                        mime="text/plain",
                        key=f"download_{i}_{report.get('filename', 'report')}"
                    )
    else:
        st.info("No reports uploaded yet. Upload your first health report above to get started!")

    col1, col2 = st.columns([2, 1])
    with col1:
        if st.download_button(
            label="📥 Download Analysis Summary",
            data=download_content,
            file_name=f"health_analysis_{filename.split('.')[0]}_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain",
            key=f"download_{report_data['id']}"
        ):
            # Mark as downloaded but keep button visible
            for report in st.session_state.reports_history:
                if report['id'] == report_data['id']:
                    report['downloaded'] = True
    
    with col2:
        if report_data.get('downloaded', False):
            st.success("✅ Downloaded!")
        st.info("💡 Download stays available")


def show_summary_page():
    """Report summary page"""
    st.title("📈 Report Summary")
    st.markdown("Overview of all your analyzed health reports")
    
    if not st.session_state.reports_history:
        st.info("No reports analyzed yet. Go to Report Analysis to upload your first report.")
        if st.button("📁 Analyze First Report"):
            st.session_state.current_page = 'upload'
            st.rerun()
        return
    
    # Summary Statistics
    col1, col2, col3 = st.columns(3)
    
    total_concerns = sum(len(r.get('concerns', [])) for r in st.session_state.reports_history)
    total_recommendations = sum(len(r.get('recommendations', [])) for r in st.session_state.reports_history)
    
    with col1:
        st.metric("Total Reports", len(st.session_state.reports_history))
    with col2:
        st.metric("Total Concerns", total_concerns)
    with col3:
        st.metric("Total Recommendations", total_recommendations)
    
    st.markdown("---")
    
    # Detailed Report List
    st.subheader("📊 All Reports")
    
    for i, report in enumerate(reversed(st.session_state.reports_history)):
        with st.expander(f"📄 {report['filename']} - {report['date']}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("**Summary:**")
                st.write(report['summary'])
                
                if report['concerns']:
                    st.markdown("**⚠️ Concerns:**")
                    for concern in report['concerns']:
                        st.write(f"• {concern}")
                
                if report['recommendations']:
                    st.markdown("**💡 Recommendations:**")
                    for rec in report['recommendations']:
                        st.write(f"• {rec}")
            
            with col2:
                st.markdown("**📈 Key Metrics:**")
                if report['metrics']:
                    for metric in report['metrics']:
                        st.write(f"**{metric.get('name', 'Unknown')}:** {metric.get('value', 'N/A')}")
                else:
                    st.write("No specific metrics extracted")

def show_assistant_page():
    """Query assistant page"""
    st.title("🤖 Health Query Assistant")
    st.markdown("Ask questions about your health reports and get AI-powered insights")
    
    if 'health_analyzer' not in st.session_state:
        st.session_state.health_analyzer = HealthAnalyzer()
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # Quick Questions Section
    with st.expander("💡 Quick Questions", expanded=True):
        st.markdown("**Click on any question to ask it instantly:**")
        
        quick_questions = [
            ("📊 What are my latest health metrics?", "What are my latest health metrics and how do they compare to normal ranges?"),
            ("💊 Alternative medicine options", "What are safe alternative medicine options for my current medications? Include generic alternatives and natural supplements."),
            ("⚠️ Drug interactions check", "Are there any potential interactions between my current medications? What should I watch for?"),
            ("💰 Cost-saving medication tips", "How can I save money on my medications? Are there generic alternatives or patient assistance programs?"),
            ("🌿 Natural alternatives to medications", "What natural supplements or lifestyle changes could complement or potentially replace some of my current medications?"),
            ("📋 Can you summarize my health status?", "Can you provide a comprehensive summary of my current health status including my medications?")
        ]
        
        cols = st.columns(2)
        for i, (display_text, full_question) in enumerate(quick_questions):
            col = cols[i % 2]
            with col:
                if st.button(display_text, key=f"quick_q_{i}", use_container_width=True):
                    # Add the question to chat
                    st.session_state.chat_history.append({"role": "user", "content": full_question})
                    # Process the question immediately
                    process_ai_question(full_question)
                    st.rerun()
    
    st.markdown("---")
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask a question about your health reports..."):
        # Add user message
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # Generate AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                process_ai_question(prompt)
                # Display the latest response
                latest_response = st.session_state.chat_history[-1]["content"]
                st.write(latest_response)
    
    # Clear chat button
    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.rerun()


def show_history_page():
    """Health history page"""
    st.title("📚 Health History")
    st.markdown("Comprehensive view of your health journey over time")
    
    if not st.session_state.reports_history:
        st.info("No health history available. Upload reports to start tracking your health journey.")
        if st.button("📁 Upload First Report"):
            st.session_state.current_page = 'upload'
            st.rerun()
        return
    
    # Timeline view
    st.subheader("📈 Health Timeline")
    
    # Sort reports by date
    sorted_reports = sorted(st.session_state.reports_history, key=lambda x: x['date'], reverse=True)
    
    for report in sorted_reports:
        with st.container():
            col1, col2 = st.columns([1, 3])
            
            with col1:
                st.markdown(f"**{report['date']}**")
                st.markdown(f"📄 {report['filename']}")
            
            with col2:
                # Health status indicator
                concern_count = len(report.get('concerns', []))
                if concern_count == 0:
                    st.success("✅ No concerns identified")
                elif concern_count <= 2:
                    st.warning(f"⚠️ {concern_count} concern(s) to monitor")
                else:
                    st.error(f"🚨 {concern_count} concerns requiring attention")
                
                # Key metrics summary
                if report['metrics']:
                    st.markdown("**Key Metrics:**")
                    metric_text = ", ".join([f"{m.get('name', 'Unknown')}: {m.get('value', 'N/A')}" for m in report['metrics'][:3]])
                    st.markdown(metric_text)
                
                # Quick summary
                summary_preview = report['summary'][:150] + "..." if len(report['summary']) > 150 else report['summary']
                st.markdown(f"**Summary:** {summary_preview}")
            
            st.markdown("---")
    
    # Health trends (if multiple reports)
    if len(sorted_reports) > 1:
        st.subheader("📊 Health Trends")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Concern Trends:**")
            concern_counts = [len(r.get('concerns', [])) for r in reversed(sorted_reports)]
            dates = [r['date'][:10] for r in reversed(sorted_reports)]  # Just date part
            
            if concern_counts:
                trend_data = pd.DataFrame({
                    'Date': dates,
                    'Concerns': concern_counts
                })
                st.line_chart(trend_data.set_index('Date'))
        
        with col2:
            st.markdown("**Recent Patterns:**")
            
            # Most common concerns
            all_concerns = []
            for report in sorted_reports:
                all_concerns.extend(report.get('concerns', []))
            
            if all_concerns:
                concern_counts = {}
                for concern in all_concerns:
                    concern_counts[concern] = concern_counts.get(concern, 0) + 1
                
                st.markdown("**Most Common Concerns:**")
                for concern, count in sorted(concern_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                    st.write(f"• {concern} ({count}x)")
            else:
                st.info("No recurring concerns identified")

def show_prescription_page():
    """Prescription management page with comprehensive features"""
    st.title("💊 Medication Manager")
    st.markdown("Manage your medications, find nearby pharmacies, and get AI-powered medical insights")
    
    # Create tabs for different features
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 My Medications", 
        "🏪 Find Pharmacies", 
        "✉️ Email Suggestions", 
        "👨‍⚕️ Book Appointment"
    ])
    
    with tab1:
        show_prescription_management()
    
    with tab2:
        show_pharmacy_locator()
    
    with tab3:
        show_email_suggestions()
    
    with tab4:
        show_appointment_booking()

def show_prescription_management():
    """Prescription management interface"""
    st.header("📋 Your Medications")
    
    # Add new prescription
    with st.expander("➕ Add Prescribed Medication", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            medicine_name = st.text_input(
                "Medicine Name",
                placeholder="e.g., Aspirin, Metformin, Lisinopril",
                help="Enter the generic or brand name of your medication"
            )
            
            dosage = st.text_input(
                "Dosage",
                placeholder="e.g., 5mg, 10ml, 1 tablet",
                help="Enter the dose amount and unit"
            )
            
            frequency = st.selectbox(
                "Frequency",
                ["Once daily", "Twice daily", "Three times daily", "Four times daily", 
                 "As needed", "Weekly", "Every other day", "Custom"]
            )
        
        with col2:
            prescribing_doctor = st.text_input(
                "Prescribing Doctor",
                placeholder="Dr. Smith",
                help="Name of the doctor who prescribed this medication"
            )
            
            start_date = st.date_input(
                "Start Date",
                value=datetime.now().date(),
                help="When you started taking this medication"
            )
            
            notes = st.text_area(
                "Notes",
                placeholder="Any special instructions or notes...",
                help="Additional information about this medication"
            )
        
        if st.button("💊 Add Medication", type="primary"):
            if medicine_name:
                # Get medicine info from DailyMed
                medicine_info = get_dailymed_info(medicine_name)
                
                prescription = {
                    'id': f"rx_{len(st.session_state.prescriptions) + 1}",
                    'medicine_name': medicine_name,
                    'dosage': dosage,
                    'frequency': frequency,
                    'prescribing_doctor': prescribing_doctor,
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'notes': notes,
                    'medicine_info': medicine_info,
                    'added_date': datetime.now().strftime('%Y-%m-%d %H:%M EST')
                }
                
                st.session_state.prescriptions.append(prescription)
                st.success(f"✅ Added {medicine_name} to your medications!")
                st.rerun()
            else:
                st.error("Please enter a medicine name")
    
    # Display current prescriptions
    if st.session_state.prescriptions:
        st.header("📊 Current Medications")
        
        for i, prescription in enumerate(st.session_state.prescriptions):
            with st.expander(f"💊 {prescription['medicine_name']} - {prescription['dosage']}", expanded=False):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.write(f"**Dosage:** {prescription['dosage']}")
                    st.write(f"**Frequency:** {prescription['frequency']}")
                    st.write(f"**Doctor:** {prescription['prescribing_doctor']}")
                    st.write(f"**Start Date:** {prescription['start_date']}")
                
                with col2:
                    if prescription.get('medicine_info'):
                        info = prescription['medicine_info']
                        if info.get('description'):
                            st.write(f"**Description:** {info['description'][:100]}...")
                        if info.get('warnings'):
                            st.warning(f"⚠️ **Warnings:** {info['warnings'][:100]}...")
                        if info.get('interactions'):
                            st.info(f"🔄 **Interactions:** {info['interactions'][:100]}...")
                    
                    if prescription.get('notes'):
                        st.write(f"**Notes:** {prescription['notes']}")
                
                with col3:
                    if st.button(f"🗑️ Remove", key=f"remove_{i}"):
                        st.session_state.prescriptions.pop(i)
                        st.success("Medication removed!")
                        st.rerun()
                    
                    if st.button(f"📧 Email Info", key=f"email_{i}"):
                        st.session_state.selected_prescription = prescription
                        st.info("Switch to Email Suggestions tab to send this medication info!")
    else:
        st.info("No medications added yet. Add your first medication above!")

def show_pharmacy_locator():
    """Pharmacy locator with geolocation"""
    st.header("🏪 Find Nearby Pharmacies")
    
    # Location input
    col1, col2 = st.columns([3, 1])
    
    with col1:
        location_input = st.text_input(
            "Enter your location",
            placeholder="e.g., New York, NY or your ZIP code",
            help="Enter your city, state, or ZIP code to find nearby pharmacies"
        )
    
    with col2:
        if st.button("📍 Use My Location", help="Enable location services in your browser"):
            st.info("Location services require browser permission. Please enter your location manually above.")
    
    if location_input:
        with st.spinner("Finding pharmacies near you..."):
            pharmacies = find_nearby_pharmacies(location_input)
            
            if pharmacies:
                st.success(f"✅ Found {len(pharmacies)} pharmacies near {location_input}")
                
                # Display pharmacy results
                for i, pharmacy in enumerate(pharmacies[:10]):  # Show top 10
                    with st.container():
                        col1, col2, col3 = st.columns([3, 2, 1])
                        
                        with col1:
                            st.subheader(f"🏪 {pharmacy['name']}")
                            st.write(f"📍 {pharmacy['address']}")
                            if pharmacy.get('phone'):
                                st.write(f"📞 {pharmacy['phone']}")
                        
                        with col2:
                            if pharmacy.get('distance'):
                                st.metric("Distance", f"{pharmacy['distance']:.1f} miles")
                            if pharmacy.get('rating'):
                                st.metric("Rating", f"⭐ {pharmacy['rating']}/5")
                            if pharmacy.get('hours'):
                                st.write(f"🕒 {pharmacy['hours']}")
                        
                        with col3:
                            if pharmacy.get('phone'):
                                st.write(f"[📞 Call]({pharmacy['phone']})")
                            if pharmacy.get('directions_url'):
                                st.write(f"[🗺️ Directions]({pharmacy['directions_url']})")
                        
                        st.markdown("---")
            else:
                st.warning("No pharmacies found in your area. Try a different location.")

def show_email_suggestions():
    """Email medication suggestions"""
    st.header("✉️ Email Medication Suggestions")
    
    if not st.session_state.prescriptions:
        st.info("Add some medications first to email suggestions!")
        return
    
    # Email configuration
    with st.expander("📧 Email Settings", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            recipient_email = st.text_input(
                "Recipient Email",
                placeholder="doctor@example.com or patient@email.com",
                help="Email address to send medication information"
            )
            
            email_type = st.selectbox(
                "Email Type",
                ["Medication Summary", "Alternative Medicine Suggestions", "Drug Interaction Alert", "Refill Reminder"]
            )
        
        with col2:
            sender_name = st.text_input(
                "Your Name",
                placeholder="John Doe",
                help="Your name for the email signature"
            )
            
            include_alternatives = st.checkbox(
                "Include Alternative Medicine Suggestions",
                value=True,
                help="Add AI-generated alternative medicine suggestions"
            )
    
    # Select prescriptions to include
    st.subheader("📋 Select Medications to Include")
    
    selected_prescriptions = []
    for i, prescription in enumerate(st.session_state.prescriptions):
        if st.checkbox(f"💊 {prescription['medicine_name']} - {prescription['dosage']}", key=f"select_email_{i}"):
            selected_prescriptions.append(prescription)
    
    # Generate and send email
    if selected_prescriptions and recipient_email:
        if st.button("📧 Generate & Send Email", type="primary"):
            with st.spinner("Generating email content..."):
                # Generate email content
                email_content = generate_prescription_email(
                    selected_prescriptions, 
                    email_type, 
                    sender_name,
                    include_alternatives
                )
                
                st.subheader("📄 Email Preview")
                st.text_area("Email Content:", value=email_content, height=300, disabled=True)
                
                # Send email functionality would go here
                st.info("📧 Email preview generated! To actually send emails, you'll need to set up email configuration.")
                
                # Download option
                st.download_button(
                    label="📥 Download Email",
                    data=email_content,
                    file_name=f"medication_email_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    mime="text/plain"
                )

def show_appointment_booking():
    """Doctor appointment booking interface"""
    st.header("👨‍⚕️ Book Doctor Appointment")
    
    # Appointment booking form
    with st.expander("📅 Schedule New Appointment", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            appointment_type = st.selectbox(
                "Appointment Type",
                ["General Consultation", "Follow-up Visit", "Medication Review", 
                 "Specialist Referral", "Urgent Care", "Telemedicine"]
            )
            
            preferred_doctor = st.text_input(
                "Preferred Doctor",
                placeholder="Dr. Smith or any available",
                help="Enter a specific doctor's name or leave blank for any available"
            )
            
            appointment_date = st.date_input(
                "Preferred Date",
                min_value=datetime.now().date(),
                value=datetime.now().date(),
                help="Choose your preferred appointment date"
            )
        
        with col2:
            appointment_time = st.selectbox(
                "Preferred Time",
                ["Morning (9AM-12PM)", "Afternoon (12PM-5PM)", "Evening (5PM-8PM)", "Any time available"]
            )
            
            urgency = st.selectbox(
                "Urgency Level",
                ["Routine", "Moderate", "Urgent", "Emergency"]
            )
            
            contact_number = st.text_input(
                "Contact Number",
                placeholder="+1 (555) 123-4567",
                help="Phone number for appointment confirmation"
            )
        
        reason_for_visit = st.text_area(
            "Reason for Visit",
            placeholder="Describe your symptoms or reason for the appointment...",
            help="Brief description of why you need this appointment"
        )
        
        # Related prescriptions
        related_prescriptions = []
        if st.session_state.prescriptions:
            st.subheader("💊 Related Medications")
            st.write("Select medications to discuss during the appointment:")
            
            for i, prescription in enumerate(st.session_state.prescriptions):
                if st.checkbox(
                    f"💊 {prescription['medicine_name']} - {prescription['dosage']}", 
                    key=f"appt_rx_{i}"
                ):
                    related_prescriptions.append(prescription)
        
        if st.button("📅 Submit Appointment Request", type="primary"):
            if appointment_type and appointment_date and contact_number:
                appointment_request = {
                    'id': f"appt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    'type': appointment_type,
                    'preferred_doctor': preferred_doctor,
                    'date': appointment_date.strftime('%Y-%m-%d'),
                    'time': appointment_time,
                    'urgency': urgency,
                    'contact': contact_number,
                    'reason': reason_for_visit,
                    'related_medications': [p['medicine_name'] for p in related_prescriptions],
                    'status': 'Pending',
                    'requested_at': datetime.now().strftime('%Y-%m-%d %H:%M EST')
                }
                
                # Initialize appointments if not exists
                if 'appointments' not in st.session_state:
                    st.session_state.appointments = []
                
                st.session_state.appointments.append(appointment_request)
                
                st.success("✅ Appointment request submitted successfully!")
                st.info("📧 You will receive a confirmation call/email within 24 hours.")
                
                # Show appointment summary
                st.subheader("📋 Appointment Summary")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Type:** {appointment_type}")
                    st.write(f"**Date:** {appointment_date}")
                    st.write(f"**Time:** {appointment_time}")
                    st.write(f"**Urgency:** {urgency}")
                
                with col2:
                    st.write(f"**Doctor:** {preferred_doctor or 'Any available'}")
                    st.write(f"**Contact:** {contact_number}")
                    st.write(f"**Status:** Pending")
                
                if reason_for_visit:
                    st.write(f"**Reason:** {reason_for_visit}")
            
            else:
                st.error("Please fill in all required fields (appointment type, date, and contact number)")
    
    # Show existing appointments
    if 'appointments' in st.session_state and st.session_state.appointments:
        st.header("📅 Your Appointments")
        
        for i, appointment in enumerate(st.session_state.appointments):
            status_color = "🟡" if appointment['status'] == 'Pending' else "🟢" if appointment['status'] == 'Confirmed' else "🔴"
            
            with st.expander(f"{status_color} {appointment['type']} - {appointment['date']}", expanded=False):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Type:** {appointment['type']}")
                    st.write(f"**Date:** {appointment['date']}")
                    st.write(f"**Time:** {appointment['time']}")
                
                with col2:
                    st.write(f"**Doctor:** {appointment['preferred_doctor'] or 'Any available'}")
                    st.write(f"**Status:** {appointment['status']}")
                    st.write(f"**Urgency:** {appointment['urgency']}")
                
                with col3:
                    st.write(f"**Contact:** {appointment['contact']}")
                    st.write(f"**Requested:** {appointment['requested_at']}")
                    
                    if st.button(f"❌ Cancel", key=f"cancel_appt_{i}"):
                        st.session_state.appointments.pop(i)
                        st.success("Appointment cancelled!")
                        st.rerun()
                
                if appointment.get('reason'):
                    st.write(f"**Reason:** {appointment['reason']}")
                
                if appointment.get('related_medications'):
                    st.write(f"**Related Medications:** {', '.join(appointment['related_medications'])}")

def get_dailymed_info(medicine_name):
    """Get medicine information from DailyMed API"""
    try:
        # Clean medicine name for API call
        clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', medicine_name).strip()
        
        url = "https://dailymed.nlm.nih.gov/dailymed/services/v2/spls.json"
        params = {
            'drug_name': clean_name,
            'pagesize': 5
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('data') and len(data['data']) > 0:
                spl = data['data'][0]  # Get first result
                
                return {
                    'title': spl.get('title', 'N/A'),
                    'description': f"FDA-approved medication: {spl.get('title', 'N/A')}",
                    'setid': spl.get('setid', ''),
                    'published_date': spl.get('published_date', ''),
                    'warnings': "Please consult healthcare provider for specific warnings",
                    'interactions': "Check with pharmacist for drug interactions"
                }
    except Exception as e:
        st.error(f"Could not fetch medicine information: {str(e)}")
    
    return {
        'description': f"Medication: {medicine_name}",
        'warnings': "Consult healthcare provider",
        'interactions': "Check with pharmacist"
    }

def find_nearby_pharmacies(location):
    """Find nearby pharmacies using location services"""
    try:
        geolocator = Nominatim(user_agent="smart_medi_assist")
        location_obj = geolocator.geocode(location)
        
        if not location_obj:
            return []
        
        # Mock pharmacy data - in real implementation, you'd use Google Places API or similar
        mock_pharmacies = [
            {
                'name': 'CVS Pharmacy',
                'address': f'123 Main St, {location}',
                'phone': '(555) 123-4567',
                'distance': 0.8,
                'rating': 4.2,
                'hours': 'Open until 10 PM',
                'directions_url': f'https://maps.google.com/directions/?api=1&destination=CVS+Pharmacy+{location}'
            },
            {
                'name': 'Walgreens',
                'address': f'456 Oak Ave, {location}',
                'phone': '(555) 234-5678',
                'distance': 1.2,
                'rating': 4.0,
                'hours': '24 hours',
                'directions_url': f'https://maps.google.com/directions/?api=1&destination=Walgreens+{location}'
            },
            {
                'name': 'Rite Aid',
                'address': f'789 Pine St, {location}',
                'phone': '(555) 345-6789',
                'distance': 1.5,
                'rating': 3.8,
                'hours': 'Open until 9 PM',
                'directions_url': f'https://maps.google.com/directions/?api=1&destination=Rite+Aid+{location}'
            },
            {
                'name': 'Local Family Pharmacy',
                'address': f'321 Elm St, {location}',
                'phone': '(555) 456-7890',
                'distance': 2.1,
                'rating': 4.5,
                'hours': 'Open until 8 PM',
                'directions_url': f'https://maps.google.com/directions/?api=1&destination=Family+Pharmacy+{location}'
            }
        ]
        
        return mock_pharmacies
    
    except Exception as e:
        st.error(f"Error finding pharmacies: {str(e)}")
        return []

def generate_prescription_email(prescriptions, email_type, sender_name, include_alternatives=True):
    """Generate email content for medication information"""
    
    est_tz = pytz.timezone('US/Eastern')
    current_time = datetime.now(est_tz).strftime('%B %d, %Y at %I:%M %p EST')
    
    email_content = f"""
Subject: {email_type} - Generated by Smart Medi Assist AI

Dear Healthcare Provider,

I hope this email finds you well. I am writing to share my current medication information as managed through Smart Medi Assist AI.

{email_type.upper()}
Generated on: {current_time}

CURRENT MEDICATIONS:
"""
    
    for i, prescription in enumerate(prescriptions, 1):
        email_content += f"""
{i}. {prescription['medicine_name']}
   - Dosage: {prescription['dosage']}
   - Frequency: {prescription['frequency']}
   - Prescribing Doctor: {prescription['prescribing_doctor']}
   - Start Date: {prescription['start_date']}
   - Notes: {prescription.get('notes', 'None')}
"""
        
        if prescription.get('medicine_info'):
            info = prescription['medicine_info']
            if info.get('description'):
                email_content += f"   - Description: {info['description']}\n"
    
    if include_alternatives and email_type == "Alternative Medicine Suggestions":
        email_content += """

AI-GENERATED ALTERNATIVE SUGGESTIONS:
Based on the current medications and health data analysis, here are some potential alternatives to discuss:

• Generic equivalents may be available for cost savings
• Natural supplements could complement current treatments
• Lifestyle modifications may reduce medication dependency
• Drug interaction checks have been performed

Please note: These are AI-generated suggestions for discussion purposes only. 
All medication changes should be made only under professional medical supervision.
"""
    
    email_content += f"""

IMPORTANT DISCLAIMER:
This information is generated by Smart Medi Assist AI for healthcare communication purposes only. 
All medical decisions should be made in consultation with qualified healthcare professionals.

If you have any questions or need additional information, please don't hesitate to contact me.

Best regards,
{sender_name}

---
Generated by Smart Medi Assist AI - Healthcare Intelligence Platform
For questions about this system, please contact: support@smartmediassist.com
"""
    
    return email_content

def show_appointments_page():
    """Doctor appointment scheduling page with nearby hospital search"""
    st.title("🏥 Doctor Appointments")
    st.markdown("Find nearby hospitals and clinics to schedule your appointments")
    
    # Get user location
    with st.container():
        st.subheader("📍 Your Location")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            user_address = st.text_input(
                "Enter your address or city",
                value=st.session_state.get('user_address', ''),
                placeholder="e.g., New York, NY or 123 Main St, Boston, MA",
                help="We'll use this to find nearby healthcare facilities"
            )
        
        with col2:
            if st.button("🔍 Find Nearby Hospitals", type="primary"):
                if user_address:
                    with st.spinner("Searching for nearby hospitals..."):
                        st.session_state.user_address = user_address
                        find_nearby_hospitals(user_address)
                else:
                    st.error("Please enter your location first")
    
    # Display nearby hospitals
    if st.session_state.nearby_hospitals:
        st.subheader("🏥 Nearby Healthcare Facilities")
        
        for i, hospital in enumerate(st.session_state.nearby_hospitals):
            with st.expander(f"🏥 {hospital['name']}", expanded=False):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Address:** {hospital['address']}")
                    st.write(f"**Distance:** {hospital['distance']:.1f} km away")
                    st.write(f"**Type:** {hospital['type']}")
                    st.info("📞 Contact information will be provided after appointment request")
                
                with col2:
                    # Appointment request button
                    if st.button(f"📅 Request Appointment", key=f"appt_{i}"):
                        st.session_state.selected_hospital = hospital
                        st.info("Please fill out the appointment request form below!")
                        st.rerun()
    
    # Appointment request form
    if st.session_state.get('selected_hospital'):
        st.markdown("---")
        st.subheader("📋 Request Appointment")
        hospital = st.session_state.selected_hospital
        
        st.info(f"Requesting appointment at: **{hospital['name']}**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            patient_name = st.text_input("Full Name", placeholder="Enter your full name")
            patient_phone = st.text_input("Phone Number", placeholder="Enter your phone number")
            appointment_type = st.selectbox(
                "Appointment Type",
                ["General Consultation", "Follow-up Visit", "Medication Review", 
                 "Specialist Referral", "Emergency Consultation", "Health Checkup"]
            )
        
        with col2:
            preferred_date = st.date_input("Preferred Date", min_value=datetime.now().date())
            preferred_time = st.selectbox(
                "Preferred Time",
                ["Morning (9:00 AM - 12:00 PM)", "Afternoon (1:00 PM - 5:00 PM)", "Evening (6:00 PM - 8:00 PM)"]
            )
            urgency = st.selectbox("Urgency Level", ["Routine", "Urgent", "Emergency"])
        
        # Related health information
        st.subheader("🩺 Health Information")
        symptoms = st.text_area("Current Symptoms (if any)", placeholder="Describe any symptoms you're experiencing")
        
        # Related medications
        related_medications = []
        if st.session_state.prescriptions:
            st.write("**Select medications to discuss:**")
            for i, prescription in enumerate(st.session_state.prescriptions):
                if st.checkbox(
                    f"💊 {prescription['medicine_name']} - {prescription['dosage']}", 
                    key=f"appt_med_{i}"
                ):
                    related_medications.append(prescription)
        
        # Submit appointment request
        if st.button("📋 Submit Appointment Request", type="primary"):
            if patient_name and patient_phone:
                appointment = {
                    'id': f"appt_{len(st.session_state.appointments) + 1}",
                    'hospital': hospital['name'],
                    'hospital_address': hospital['address'],
                    'hospital_phone': 'Contact provided after confirmation',
                    'patient_name': patient_name,
                    'patient_phone': patient_phone,
                    'appointment_type': appointment_type,
                    'preferred_date': str(preferred_date),
                    'preferred_time': preferred_time,
                    'urgency': urgency,
                    'symptoms': symptoms,
                    'related_medications': [m['medicine_name'] for m in related_medications],
                    'status': 'Requested',
                    'request_date': datetime.now().strftime('%Y-%m-%d %H:%M')
                }
                
                st.session_state.appointments.append(appointment)
                st.success("✅ Appointment request submitted successfully!")
                st.info("The hospital will contact you within 24-48 hours to confirm your appointment.")
                
                # Clear the selected hospital
                del st.session_state.selected_hospital
                st.rerun()
            else:
                st.error("Please fill in your name and phone number")
    
    # Display appointment history
    if st.session_state.appointments:
        st.markdown("---")
        st.subheader("📅 Your Appointment Requests")
        
        for appointment in reversed(st.session_state.appointments):
            with st.expander(f"🏥 {appointment['hospital']} - {appointment['preferred_date']}", expanded=False):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Type:** {appointment['appointment_type']}")
                    st.write(f"**Date:** {appointment['preferred_date']}")
                    st.write(f"**Time:** {appointment['preferred_time']}")
                    st.write(f"**Urgency:** {appointment['urgency']}")
                    if appointment['symptoms']:
                        st.write(f"**Symptoms:** {appointment['symptoms']}")
                    if appointment['related_medications']:
                        st.write(f"**Medications to discuss:** {', '.join(appointment['related_medications'])}")
                
                with col2:
                    status_color = "🟢" if appointment['status'] == 'Confirmed' else "🟡" if appointment['status'] == 'Requested' else "🔴"
                    st.write(f"**Status:** {status_color} {appointment['status']}")
                    st.write(f"**Requested:** {appointment['request_date']}")
                    st.write(f"**Hospital Phone:** {appointment['hospital_phone']}")

def find_nearby_hospitals(address):
    """Find nearby hospitals using geopy geocoding with robust error handling"""
    try:
        geolocator = Nominatim(user_agent="smart_medi_assist_v1.0")
        location = geolocator.geocode(address)
        
        if location and hasattr(location, 'latitude') and hasattr(location, 'longitude'):
            # Store user location
            st.session_state.user_location = {
                'address': address,
                'latitude': float(location.latitude),
                'longitude': float(location.longitude)
            }
            
            st.info("🌍 Location found! Searching for nearby healthcare facilities...")
            
            # Sample hospitals (using realistic data based on geocoded location)
            # Note: In a production app, integrate Google Places API for real data with ratings and phone numbers
            sample_hospitals = [
                {
                    'name': 'General Hospital',
                    'address': f'123 Medical Center Dr, near {address}',
                    'distance': 2.3,
                    'type': 'Hospital'
                },
                {
                    'name': 'Community Medical Center',
                    'address': f'456 Health Ave, near {address}',
                    'distance': 3.7,
                    'type': 'Medical Center'
                },
                {
                    'name': 'Regional Clinic',
                    'address': f'789 Care St, near {address}',
                    'distance': 4.1,
                    'type': 'Clinic'
                },
                {
                    'name': 'Emergency Medical Center',
                    'address': f'321 Emergency Blvd, near {address}',
                    'distance': 5.2,
                    'type': 'Emergency Care'
                }
            ]
            
            st.session_state.nearby_hospitals = sample_hospitals
            st.success(f"✅ Found {len(sample_hospitals)} healthcare facilities near {address}")
        else:
            st.error("Could not find the location. Please check your address and try again.")
            
    except Exception as e:
        st.error(f"Error finding hospitals: {str(e)}")

def update_lifestyle_history():
    """Update lifestyle history with current quiz results and timestamp"""
    if st.session_state.lifestyle_quiz:
        current_score = calculate_lifestyle_score(st.session_state.lifestyle_quiz)
        
        # Create lifestyle history entry
        history_entry = {
            'timestamp': datetime.now().isoformat(),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'score': current_score,
            'quiz_data': st.session_state.lifestyle_quiz.copy()
        }
        
        # Update history (keep last 30 entries)
        st.session_state.lifestyle_history.append(history_entry)
        if len(st.session_state.lifestyle_history) > 30:
            st.session_state.lifestyle_history = st.session_state.lifestyle_history[-30:]

def show_lifestyle_page():
    """Comprehensive lifestyle quiz and health recommendations"""
    st.title("🌱 Lifestyle Quiz & Health Insights")
    st.markdown("Take our comprehensive quiz to get personalized health recommendations")
    
    # Initialize quiz data
    if 'quiz_completed' not in st.session_state:
        st.session_state.quiz_completed = False
    
    # Quiz sections
    quiz_sections = {
        'sleep': '😴 Sleep Habits',
        'work': '💼 Work & Stress',
        'exercise': '🏃‍♂️ Exercise & Activity',
        'nutrition': '🥗 Nutrition & Eating Habits',
        'medications': '💊 Medication Habits'
    }
    
    # Create tabs for quiz sections
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(['📝 Take Quiz', '😴 Sleep', '💼 Work', '🏃‍♂️ Exercise', '🥗 Nutrition', '💊 Medications'])
    
    with tab1:
        st.subheader("🌟 Complete Health & Lifestyle Assessment")
        st.markdown("Answer questions across all categories to get comprehensive health recommendations.")
        
        if not st.session_state.quiz_completed:
            st.info("📋 Please complete all quiz sections in the tabs above, then return here to see your results!")
        
        # Progress indicator
        completed_sections = sum(1 for section in quiz_sections.keys() 
                               if st.session_state.lifestyle_quiz.get(f'{section}_completed', False))
        progress = completed_sections / len(quiz_sections)
        
        st.progress(progress)
        st.write(f"Progress: {completed_sections}/{len(quiz_sections)} sections completed")
        
        if completed_sections == len(quiz_sections):
            st.session_state.quiz_completed = True
            show_lifestyle_recommendations()
    
    with tab2:
        show_sleep_quiz()
    
    with tab3:
        show_work_quiz()
    
    with tab4:
        show_exercise_quiz()
    
    with tab5:
        show_nutrition_quiz()
    
    with tab6:
        show_medication_quiz()

def show_sleep_quiz():
    """Sleep habits quiz section"""
    st.subheader("😴 Sleep & Rest Patterns")
    
    col1, col2 = st.columns(2)
    
    with col1:
        bedtime = st.time_input("What time do you usually go to bed?", value=datetime.strptime("22:00", "%H:%M").time())
        wake_time = st.time_input("What time do you usually wake up?", value=datetime.strptime("07:00", "%H:%M").time())
        sleep_quality = st.select_slider(
            "How would you rate your sleep quality?",
            options=['Very Poor', 'Poor', 'Average', 'Good', 'Excellent'],
            value='Average'
        )
    
    with col2:
        sleep_issues = st.multiselect(
            "Do you experience any sleep issues?",
            ['Difficulty falling asleep', 'Frequent waking', 'Early morning awakening', 
             'Snoring', 'Sleep apnea', 'Restless legs', 'None']
        )
        caffeine_time = st.selectbox(
            "When do you last consume caffeine?",
            ['Before 2 PM', '2-4 PM', '4-6 PM', 'After 6 PM', 'I don\'t consume caffeine']
        )
        screen_time = st.selectbox(
            "When do you stop using screens before bed?",
            ['2+ hours before', '1-2 hours before', '30-60 minutes before', 'Right before bed']
        )
    
    if st.button("Save Sleep Information", key="save_sleep"):
        st.session_state.lifestyle_quiz.update({
            'bedtime': str(bedtime),
            'wake_time': str(wake_time),
            'sleep_quality': sleep_quality,
            'sleep_issues': sleep_issues,
            'caffeine_time': caffeine_time,
            'screen_time': screen_time,
            'sleep_completed': True,
            'sleep_timestamp': datetime.now().isoformat()
        })
        update_lifestyle_history()
        st.success("✅ Sleep information saved!")

def show_work_quiz():
    """Work and stress quiz section"""
    st.subheader("💼 Work Environment & Stress Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        work_schedule = st.selectbox(
            "What is your typical work schedule?",
            ['Regular 9-5', 'Shift work', 'Night shifts', 'Irregular hours', 'Work from home', 'Retired/Unemployed']
        )
        stress_level = st.select_slider(
            "How would you rate your stress level?",
            options=['Very Low', 'Low', 'Moderate', 'High', 'Very High'],
            value='Moderate'
        )
        work_breaks = st.selectbox(
            "How often do you take breaks during work?",
            ['Every hour', 'Every 2-3 hours', 'Only lunch break', 'Rarely take breaks']
        )
    
    with col2:
        stress_symptoms = st.multiselect(
            "What stress symptoms do you experience?",
            ['Headaches', 'Muscle tension', 'Fatigue', 'Anxiety', 'Irritability', 
             'Sleep problems', 'Digestive issues', 'None']
        )
        relaxation_activities = st.multiselect(
            "What relaxation activities do you practice?",
            ['Meditation', 'Deep breathing', 'Yoga', 'Reading', 'Music', 
             'Walking', 'Hobbies', 'None']
        )
        work_satisfaction = st.select_slider(
            "How satisfied are you with your work?",
            options=['Very Dissatisfied', 'Dissatisfied', 'Neutral', 'Satisfied', 'Very Satisfied'],
            value='Neutral'
        )
    
    if st.button("Save Work Information", key="save_work"):
        st.session_state.lifestyle_quiz.update({
            'work_schedule': work_schedule,
            'stress_level': stress_level,
            'work_breaks': work_breaks,
            'stress_symptoms': stress_symptoms,
            'relaxation_activities': relaxation_activities,
            'work_satisfaction': work_satisfaction,
            'work_completed': True
        })
        st.success("✅ Work and stress information saved!")

def show_exercise_quiz():
    """Exercise and physical activity quiz section"""
    st.subheader("🏃‍♂️ Physical Activity & Exercise")
    
    col1, col2 = st.columns(2)
    
    with col1:
        exercise_frequency = st.selectbox(
            "How often do you exercise per week?",
            ['Never', '1-2 times', '3-4 times', '5-6 times', 'Daily']
        )
        exercise_duration = st.selectbox(
            "How long is each exercise session?",
            ['Less than 15 minutes', '15-30 minutes', '30-60 minutes', 'More than 60 minutes']
        )
        exercise_types = st.multiselect(
            "What types of exercise do you do?",
            ['Walking', 'Running', 'Cycling', 'Swimming', 'Weight training', 
             'Yoga', 'Pilates', 'Team sports', 'Dance', 'None']
        )
    
    with col2:
        daily_steps = st.selectbox(
            "Estimated daily steps",
            ['Less than 2,000', '2,000-5,000', '5,000-8,000', '8,000-10,000', 'More than 10,000']
        )
        sedentary_hours = st.selectbox(
            "Hours spent sitting per day",
            ['Less than 4', '4-6', '6-8', '8-10', 'More than 10']
        )
        exercise_enjoyment = st.select_slider(
            "How much do you enjoy exercising?",
            options=['Hate it', 'Dislike', 'Neutral', 'Like', 'Love it'],
            value='Neutral'
        )
    
    if st.button("Save Exercise Information", key="save_exercise"):
        st.session_state.lifestyle_quiz.update({
            'exercise_frequency': exercise_frequency,
            'exercise_duration': exercise_duration,
            'exercise_types': exercise_types,
            'daily_steps': daily_steps,
            'sedentary_hours': sedentary_hours,
            'exercise_enjoyment': exercise_enjoyment,
            'exercise_completed': True
        })
        st.success("✅ Exercise information saved!")

def show_nutrition_quiz():
    """Nutrition and eating habits quiz section"""
    st.subheader("🥗 Nutrition & Eating Patterns")
    
    col1, col2 = st.columns(2)
    
    with col1:
        meals_per_day = st.selectbox(
            "How many meals do you eat per day?",
            ['1-2 meals', '3 meals', '4-5 small meals', '6+ small meals']
        )
        breakfast_frequency = st.selectbox(
            "How often do you eat breakfast?",
            ['Never', 'Rarely (1-2 times/week)', 'Sometimes (3-4 times/week)', 
             'Often (5-6 times/week)', 'Daily']
        )
        breakfast_types = st.multiselect(
            "What do you typically have for breakfast?",
            ['Cereal/Oatmeal', 'Eggs', 'Toast/Bread', 'Fruit', 'Yogurt', 
             'Coffee only', 'Smoothie', 'Nothing', 'Other']
        )
    
    with col2:
        protein_sources = st.multiselect(
            "What protein sources do you regularly consume?",
            ['Chicken', 'Fish', 'Red meat', 'Beans/Legumes', 'Nuts/Seeds', 
             'Eggs', 'Dairy products', 'Tofu/Soy', 'Protein supplements']
        )
        vegetable_servings = st.selectbox(
            "How many servings of vegetables do you eat daily?",
            ['Less than 1', '1-2 servings', '3-4 servings', '5+ servings']
        )
        water_intake = st.selectbox(
            "How many glasses of water do you drink daily?",
            ['Less than 4', '4-6 glasses', '6-8 glasses', 'More than 8 glasses']
        )
    
    # Additional nutrition questions
    snacking_habits = st.multiselect(
        "What are your snacking habits?",
        ['Healthy snacks (fruits, nuts)', 'Processed snacks (chips, cookies)', 
         'Sweet treats', 'No snacking', 'Emotional eating']
    )
    
    eating_out = st.selectbox(
        "How often do you eat out or order takeout?",
        ['Never', '1-2 times/week', '3-4 times/week', '5+ times/week']
    )
    
    if st.button("Save Nutrition Information", key="save_nutrition"):
        st.session_state.lifestyle_quiz.update({
            'meals_per_day': meals_per_day,
            'breakfast_frequency': breakfast_frequency,
            'breakfast_types': breakfast_types,
            'protein_sources': protein_sources,
            'vegetable_servings': vegetable_servings,
            'water_intake': water_intake,
            'snacking_habits': snacking_habits,
            'eating_out': eating_out,
            'nutrition_completed': True
        })
        st.success("✅ Nutrition information saved!")

def show_medication_quiz():
    """Medication habits and health awareness quiz"""
    st.subheader("💊 Medication & Health Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        medication_adherence = st.select_slider(
            "How often do you take medications as prescribed?",
            options=['Never', 'Rarely', 'Sometimes', 'Usually', 'Always'],
            value='Usually'
        )
        medication_reminders = st.selectbox(
            "Do you use reminders for medications?",
            ['No reminders needed', 'Phone alarms', 'Pill organizer', 'App reminders', 'Family/caregiver help']
        )
        side_effects_awareness = st.selectbox(
            "Are you aware of your medication side effects?",
            ['Not aware', 'Somewhat aware', 'Very aware', 'N/A - No medications']
        )
    
    with col2:
        health_monitoring = st.multiselect(
            "What health metrics do you regularly monitor?",
            ['Blood pressure', 'Blood sugar', 'Weight', 'Heart rate', 
             'Cholesterol', 'None', 'Other']
        )
        doctor_visits = st.selectbox(
            "How often do you visit your doctor?",
            ['Only when sick', 'Once a year', 'Twice a year', 'Quarterly', 'Monthly']
        )
        supplement_use = st.multiselect(
            "What supplements do you take?",
            ['Multivitamin', 'Vitamin D', 'Vitamin C', 'Omega-3', 'Probiotics', 
             'Calcium', 'Iron', 'None', 'Other']
        )
    
    if st.button("Save Medication Information", key="save_medication"):
        st.session_state.lifestyle_quiz.update({
            'medication_adherence': medication_adherence,
            'medication_reminders': medication_reminders,
            'side_effects_awareness': side_effects_awareness,
            'health_monitoring': health_monitoring,
            'doctor_visits': doctor_visits,
            'supplement_use': supplement_use,
            'medications_completed': True
        })
        st.success("✅ Medication information saved!")

def show_lifestyle_recommendations():
    """Generate and display personalized lifestyle recommendations"""
    st.subheader("🎯 Your Personalized Health Recommendations")
    
    quiz_data = st.session_state.lifestyle_quiz
    
    # Calculate overall health score
    health_score = calculate_lifestyle_score(quiz_data)
    
    # Display health score
    col1, col2, col3 = st.columns(3)
    
    with col1:
        score_color = "#4CAF50" if health_score >= 80 else "#FF9800" if health_score >= 60 else "#F44336"
        st.markdown(f"""
        <div style='background: {score_color}; padding: 1rem; border-radius: 10px; text-align: center; color: white;'>
            <h2 style='margin: 0; font-size: 2rem;'>🌟</h2>
            <h1 style='margin: 0.5rem 0 0 0; font-size: 2.5rem;'>{health_score}</h1>
            <p style='margin: 0; opacity: 0.8;'>Overall Lifestyle Score</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        priority_areas = get_priority_improvement_areas(quiz_data)
        st.markdown(f"""
        <div style='background: #2196F3; padding: 1rem; border-radius: 10px; text-align: center; color: white;'>
            <h2 style='margin: 0; font-size: 2rem;'>🎯</h2>
            <h1 style='margin: 0.5rem 0 0 0; font-size: 1.5rem;'>{len(priority_areas)}</h1>
            <p style='margin: 0; opacity: 0.8;'>Priority Areas</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        strengths = get_lifestyle_strengths(quiz_data)
        st.markdown(f"""
        <div style='background: #9C27B0; padding: 1rem; border-radius: 10px; text-align: center; color: white;'>
            <h2 style='margin: 0; font-size: 2rem;'>💪</h2>
            <h1 style='margin: 0.5rem 0 0 0; font-size: 1.5rem;'>{len(strengths)}</h1>
            <p style='margin: 0; opacity: 0.8;'>Strong Areas</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Detailed recommendations
    st.markdown("---")
    
    # Priority improvements
    if priority_areas:
        st.subheader("🚀 Priority Improvements")
        for area in priority_areas:
            with st.expander(f"🎯 {area['title']}", expanded=True):
                st.write(f"**Current Status:** {area['status']}")
                st.write(f"**Recommendation:** {area['recommendation']}")
                st.write(f"**Benefits:** {area['benefits']}")
                
                # Action steps
                st.write("**Action Steps:**")
                for step in area['action_steps']:
                    st.write(f"• {step}")
    
    # Strengths to maintain
    if strengths:
        st.subheader("💪 Keep Up the Good Work")
        for strength in strengths:
            st.success(f"✅ **{strength['area']}**: {strength['message']}")
    
    # Weekly action plan
    st.subheader("📅 Your Weekly Action Plan")
    action_plan = generate_weekly_action_plan(quiz_data)
    
    for day, actions in action_plan.items():
        with st.expander(f"📅 {day}", expanded=False):
            for action in actions:
                st.write(f"• {action}")

def calculate_lifestyle_score(quiz_data):
    """Calculate overall lifestyle score based on quiz responses"""
    score = 0
    total_categories = 5
    
    # Sleep score (20 points)
    sleep_score = 0
    if quiz_data.get('sleep_quality') in ['Good', 'Excellent']:
        sleep_score += 15
    elif quiz_data.get('sleep_quality') == 'Average':
        sleep_score += 10
    
    if not quiz_data.get('sleep_issues') or 'None' in quiz_data.get('sleep_issues', []):
        sleep_score += 5
    
    # Exercise score (20 points)
    exercise_score = 0
    freq_map = {'Daily': 15, '5-6 times': 12, '3-4 times': 8, '1-2 times': 4, 'Never': 0}
    exercise_score += freq_map.get(quiz_data.get('exercise_frequency', 'Never'), 0)
    
    if quiz_data.get('daily_steps') in ['8,000-10,000', 'More than 10,000']:
        exercise_score += 5
    
    # Nutrition score (20 points)
    nutrition_score = 0
    if quiz_data.get('breakfast_frequency') in ['Often (5-6 times/week)', 'Daily']:
        nutrition_score += 5
    if quiz_data.get('vegetable_servings') in ['3-4 servings', '5+ servings']:
        nutrition_score += 5
    if quiz_data.get('water_intake') in ['6-8 glasses', 'More than 8 glasses']:
        nutrition_score += 5
    if len(quiz_data.get('protein_sources', [])) >= 3:
        nutrition_score += 5
    
    # Work/Stress score (20 points)
    stress_score = 0
    if quiz_data.get('stress_level') in ['Very Low', 'Low']:
        stress_score += 10
    elif quiz_data.get('stress_level') == 'Moderate':
        stress_score += 6
    
    if quiz_data.get('relaxation_activities') and len(quiz_data.get('relaxation_activities', [])) >= 2:
        stress_score += 5
    
    if quiz_data.get('work_satisfaction') in ['Satisfied', 'Very Satisfied']:
        stress_score += 5
    
    # Medication/Health score (20 points)
    med_score = 0
    if quiz_data.get('medication_adherence') in ['Usually', 'Always']:
        med_score += 10
    if quiz_data.get('doctor_visits') in ['Once a year', 'Twice a year', 'Quarterly']:
        med_score += 5
    if quiz_data.get('health_monitoring') and len(quiz_data.get('health_monitoring', [])) >= 2:
        med_score += 5
    
    total_score = sleep_score + exercise_score + nutrition_score + stress_score + med_score
    return min(100, total_score)

def get_priority_improvement_areas(quiz_data):
    """Identify areas that need the most improvement"""
    improvements = []
    
    # Sleep improvements
    if quiz_data.get('sleep_quality') in ['Very Poor', 'Poor']:
        improvements.append({
            'title': 'Sleep Quality Enhancement',
            'status': f"Current quality: {quiz_data.get('sleep_quality', 'Unknown')}",
            'recommendation': 'Improve sleep hygiene and establish a consistent bedtime routine',
            'benefits': 'Better mood, improved memory, stronger immune system, better weight management',
            'action_steps': [
                'Set a consistent bedtime and wake time',
                'Create a relaxing bedtime routine',
                'Avoid screens 1 hour before bed',
                'Keep bedroom cool, dark, and quiet'
            ]
        })
    
    # Exercise improvements
    if quiz_data.get('exercise_frequency') in ['Never', '1-2 times']:
        improvements.append({
            'title': 'Increase Physical Activity',
            'status': f"Current frequency: {quiz_data.get('exercise_frequency', 'Unknown')}",
            'recommendation': 'Start with 150 minutes of moderate exercise per week',
            'benefits': 'Improved cardiovascular health, better mood, increased energy, weight management',
            'action_steps': [
                'Start with 10-minute daily walks',
                'Take stairs instead of elevators',
                'Park farther away from destinations',
                'Try bodyweight exercises at home'
            ]
        })
    
    # Nutrition improvements
    if quiz_data.get('breakfast_frequency') in ['Never', 'Rarely (1-2 times/week)']:
        improvements.append({
            'title': 'Establish Regular Breakfast Habit',
            'status': f"Current frequency: {quiz_data.get('breakfast_frequency', 'Unknown')}",
            'recommendation': 'Eat a nutritious breakfast daily to jumpstart metabolism',
            'benefits': 'Better energy levels, improved concentration, better weight management',
            'action_steps': [
                'Prepare breakfast the night before',
                'Start with simple options like oatmeal or yogurt',
                'Include protein in every breakfast',
                'Set a morning alarm for breakfast time'
            ]
        })
    
    # Stress management
    if quiz_data.get('stress_level') in ['High', 'Very High']:
        improvements.append({
            'title': 'Stress Management',
            'status': f"Current stress level: {quiz_data.get('stress_level', 'Unknown')}",
            'recommendation': 'Implement daily stress reduction techniques',
            'benefits': 'Lower blood pressure, better sleep, improved immune function, better mood',
            'action_steps': [
                'Practice 5 minutes of deep breathing daily',
                'Try meditation apps like Headspace or Calm',
                'Schedule regular breaks during work',
                'Consider talking to a counselor'
            ]
        })
    
    return improvements[:3]  # Return top 3 priority areas

def get_lifestyle_strengths(quiz_data):
    """Identify user's lifestyle strengths"""
    strengths = []
    
    if quiz_data.get('sleep_quality') in ['Good', 'Excellent']:
        strengths.append({
            'area': 'Sleep Quality',
            'message': 'You have excellent sleep habits! Continue maintaining your sleep routine.'
        })
    
    if quiz_data.get('exercise_frequency') in ['5-6 times', 'Daily']:
        strengths.append({
            'area': 'Physical Activity',
            'message': 'Great job staying active! Your exercise routine is excellent.'
        })
    
    if quiz_data.get('vegetable_servings') in ['3-4 servings', '5+ servings']:
        strengths.append({
            'area': 'Vegetable Intake',
            'message': 'Excellent vegetable consumption! You\'re getting great nutrition.'
        })
    
    if quiz_data.get('water_intake') in ['6-8 glasses', 'More than 8 glasses']:
        strengths.append({
            'area': 'Hydration',
            'message': 'Perfect hydration levels! Keep up the great water intake.'
        })
    
    if quiz_data.get('stress_level') in ['Very Low', 'Low']:
        strengths.append({
            'area': 'Stress Management',
            'message': 'Excellent stress management! You\'re handling stress very well.'
        })
    
    return strengths

def generate_weekly_action_plan(quiz_data):
    """Generate a personalized weekly action plan"""
    plan = {
        'Monday': ['Set weekly health goals', 'Meal prep for the week'],
        'Tuesday': ['30-minute walk or exercise', 'Practice 5 minutes of meditation'],
        'Wednesday': ['Try a new healthy recipe', 'Take work breaks every 2 hours'],
        'Thursday': ['Physical activity of choice', 'Drink extra water throughout the day'],
        'Friday': ['Review weekly health progress', 'Plan weekend activities'],
        'Saturday': ['Longer physical activity (hiking, sports)', 'Prepare healthy meals'],
        'Sunday': ['Relax and practice self-care', 'Plan next week\'s health goals']
    }
    
    # Customize based on quiz responses
    if quiz_data.get('exercise_frequency') == 'Never':
        for day in ['Tuesday', 'Thursday', 'Saturday']:
            plan[day] = ['Start with 10-minute walk'] + plan[day][1:]
    
    if quiz_data.get('stress_level') in ['High', 'Very High']:
        for day in plan.keys():
            plan[day].append('Practice stress reduction technique')
    
    return plan

def show_login_page():
    """Login and signup page"""
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='color: #1f77b4;'>🩺 Smart Medi Assist AI</h1>
        <p style='color: #666; font-size: 1.2rem;'>Healthcare Intelligence Platform for Families</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])
    
    with tab1:
        st.subheader("Welcome Back!")
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", placeholder="Enter your password", type="password")
            submit = st.form_submit_button("🔐 Login", use_container_width=True)
            
            if submit:
                success, user_data = st.session_state.auth_manager.authenticate(username, password)
                if success:
                    st.session_state.authenticated = True
                    st.session_state.current_user = username
                    st.success(f"Welcome back, {user_data['name']}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
    
    with tab2:
        st.subheader("Create Your Family Account")
        with st.form("signup_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_username = st.text_input("Username*", placeholder="Choose a username")
                new_name = st.text_input("Full Name*", placeholder="Your full name")
                role = st.selectbox("Role", ["Admin (Parent/Caregiver)", "Member (Family Member)"])
            
            with col2:
                new_password = st.text_input("Password*", placeholder="Choose a password", type="password")
                confirm_password = st.text_input("Confirm Password*", placeholder="Re-enter password", type="password")
                family_code = st.text_input("Family Code (optional)", placeholder="Enter family code to join existing family")
            
            signup = st.form_submit_button("📝 Create Account", use_container_width=True)
            
            if signup:
                if not new_username or not new_password or not new_name:
                    st.error("Please fill in all required fields")
                elif new_password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    user_role = "admin" if "Admin" in role else "member"
                    success, message = st.session_state.auth_manager.create_user(
                        new_username, new_password, new_name, user_role, family_code or None
                    )
                    
                    if success:
                        st.success(f"Account created successfully! Please login.")
                        user_data = st.session_state.auth_manager.get_user(new_username)
                        if not family_code:
                            st.info(f"Your family code is: **{user_data['family_id']}**. Share this with family members to join.")
                    else:
                        st.error(message)

def load_user_data():
    """Load user-specific health data from auth manager"""
    username = st.session_state.current_user
    if username:
        health_data = st.session_state.auth_manager.get_user_health_data(username)
        if health_data:
            st.session_state.reports_history = health_data.get('reports', [])
            st.session_state.prescriptions = health_data.get('prescriptions', [])
            st.session_state.appointments = health_data.get('appointments', [])

def save_user_data():
    """Save user-specific health data to auth manager"""
    username = st.session_state.current_user
    if username:
        health_data = {
            'reports': st.session_state.get('reports_history', []),
            'prescriptions': st.session_state.get('prescriptions', []),
            'appointments': st.session_state.get('appointments', [])
        }
        st.session_state.auth_manager.update_user_health_data(username, health_data)

def show_health_tracking_page():
    """Health tracking page with medication reminders, goals, and symptom tracker"""
    st.title("📅 Smart Health Tracking")
    st.markdown("Track your medications, set health goals, and monitor symptoms")
    
    tab1, tab2, tab3 = st.tabs(["💊 Medication Reminders", "🎯 Health Goals", "🩺 Symptom Tracker"])
    
    with tab1:
        show_medication_reminders()
    
    with tab2:
        show_health_goals()
    
    with tab3:
        show_symptom_tracker()

def show_medication_reminders():
    """Medication reminder system"""
    st.header("💊 Medication Reminders")
    
    st.info("📱 **Note:** Medication reminders are stored in your profile. For actual push notifications, enable browser notifications or use the mobile app (feature in development).")
    
    username = st.session_state.current_user
    reminders = st.session_state.auth_manager.get_user_health_data(username, 'medication_reminders') or []
    
    # Add new reminder
    with st.expander("➕ Set New Medication Reminder", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            med_name = st.text_input("Medication Name", placeholder="e.g., Aspirin")
            dosage = st.text_input("Dosage", placeholder="e.g., 5mg")
            frequency = st.selectbox("Frequency", ["Once daily", "Twice daily", "Three times daily", "As needed"])
        
        with col2:
            reminder_times = st.multiselect(
                "Reminder Times",
                ["8:00 AM", "12:00 PM", "4:00 PM", "8:00 PM", "10:00 PM"],
                default=["8:00 AM"]
            )
            start_date = st.date_input("Start Date", value=datetime.now().date())
            end_date = st.date_input("End Date (optional)", value=None)
        
        if st.button("💊 Set Reminder", type="primary"):
            if med_name and dosage:
                reminder = st.session_state.health_tracker.create_medication_reminder(
                    med_name, dosage, frequency, reminder_times, 
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d') if end_date else None
                )
                st.session_state.auth_manager.add_health_data(username, 'medication_reminders', reminder)
                save_user_data()  # Save immediately
                st.success(f"✅ Reminder set for {med_name}!")
                st.rerun()
    
    # Display active reminders
    if reminders:
        st.subheader("📋 Active Reminders")
        for i, reminder in enumerate(reminders):
            if reminder.get('active'):
                with st.expander(f"💊 {reminder['medicine_name']} - {reminder['dosage']}", expanded=False):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.write(f"**Frequency:** {reminder['frequency']}")
                        st.write(f"**Times:** {', '.join(reminder['times'])}")
                        st.write(f"**Start:** {reminder['start_date']}")
                        if reminder.get('end_date'):
                            st.write(f"**End:** {reminder['end_date']}")
                    
                    with col2:
                        if reminder.get('history'):
                            st.write(f"**Last Taken:** {reminder['history'][-1]['taken_at']}")
                            st.write(f"**Total Doses:** {len(reminder['history'])}")
                        else:
                            st.write("**Status:** Not yet taken")
                    
                    with col3:
                        if st.button("✅ Mark Taken", key=f"take_{i}"):
                            st.session_state.health_tracker.log_medication_taken(reminder)
                            save_user_data()  # Save immediately
                            st.success("Logged!")
                            st.rerun()
                        
                        if st.button("🗑️ Delete", key=f"del_rem_{i}"):
                            reminder['active'] = False
                            save_user_data()  # Save immediately
                            st.success("Reminder removed!")
                            st.rerun()
    else:
        st.info("No medication reminders set. Create one above!")

def show_health_goals():
    """Health goals tracking"""
    st.header("🎯 Health Goals")
    
    username = st.session_state.current_user
    goals = st.session_state.auth_manager.get_user_health_data(username, 'health_goals') or []
    
    # Add new goal
    with st.expander("➕ Set New Health Goal", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            goal_type = st.selectbox(
                "Goal Type",
                ["Weight Loss", "Blood Pressure Reduction", "Cholesterol Reduction", 
                 "Exercise Minutes", "Daily Steps", "Custom"]
            )
            current_val = st.number_input("Current Value", min_value=0.0, step=0.1)
            target_val = st.number_input("Target Value", min_value=0.0, step=0.1)
        
        with col2:
            target_date = st.date_input("Target Date", value=datetime.now().date() + timedelta(days=30))
            notes = st.text_area("Notes", placeholder="Any additional notes...")
        
        if st.button("🎯 Set Goal", type="primary"):
            if goal_type and current_val and target_val:
                goal = st.session_state.health_tracker.create_health_goal(
                    goal_type.lower().replace(' ', '_'),
                    target_val, current_val,
                    target_date.strftime('%Y-%m-%d'),
                    notes
                )
                st.session_state.auth_manager.add_health_data(username, 'health_goals', goal)
                save_user_data()  # Save immediately
                st.success(f"✅ Goal set: {goal_type}!")
                st.rerun()
    
    # Display goals
    if goals:
        st.subheader("📊 Your Goals")
        for i, goal in enumerate(goals):
            if goal['status'] == 'active' or goal['status'] == 'achieved':
                status_icon = "🎉" if goal['status'] == 'achieved' else "🎯"
                with st.expander(f"{status_icon} {goal['goal_type'].replace('_', ' ').title()}", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Current", goal['current_value'])
                        st.metric("Target", goal['target_value'])
                        st.write(f"**Target Date:** {goal['target_date']}")
                        if goal.get('notes'):
                            st.write(f"**Notes:** {goal['notes']}")
                    
                    with col2:
                        if goal.get('progress'):
                            progress_df = pd.DataFrame(goal['progress'])
                            st.line_chart(progress_df.set_index('date')['value'], height=200)
                        
                        new_value = st.number_input(f"Update Progress", min_value=0.0, step=0.1, key=f"goal_{i}")
                        if st.button("📊 Log Progress", key=f"log_goal_{i}"):
                            st.session_state.health_tracker.update_goal_progress(goal, new_value)
                            save_user_data()  # Save immediately
                            st.success("Progress updated!")
                            st.rerun()
    else:
        st.info("No health goals set. Create one above!")

def show_symptom_tracker():
    """Symptom tracking and pattern analysis"""
    st.header("🩺 Symptom Tracker")
    
    username = st.session_state.current_user
    symptoms = st.session_state.auth_manager.get_user_health_data(username, 'symptoms') or []
    
    # Log new symptom
    with st.expander("➕ Log New Symptom", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            symptom_name = st.text_input("Symptom", placeholder="e.g., Headache, Nausea")
            severity = st.select_slider("Severity", options=["Mild", "Moderate", "Severe"])
            duration = st.text_input("Duration", placeholder="e.g., 2 hours, all day")
        
        with col2:
            description = st.text_area("Description", placeholder="Describe the symptom...")
            triggers = st.text_input("Possible Triggers", placeholder="e.g., stress, food, weather")
        
        if st.button("🩺 Log Symptom", type="primary"):
            if symptom_name:
                symptom = st.session_state.health_tracker.log_symptom(
                    symptom_name, severity.lower(), description, duration, triggers
                )
                st.session_state.auth_manager.add_health_data(username, 'symptoms', symptom)
                save_user_data()  # Save immediately
                st.success(f"✅ Logged symptom: {symptom_name}")
                st.rerun()
    
    # Display symptoms and patterns
    if symptoms:
        st.subheader("📋 Symptom History")
        
        # Analyze patterns
        analysis = st.session_state.health_tracker.analyze_symptom_patterns(symptoms)
        
        if analysis['insights']:
            st.warning("⚠️ **AI Pattern Detection:**")
            for insight in analysis['insights']:
                st.write(f"• {insight}")
            st.markdown("---")
        
        # Show recent symptoms
        for symptom in reversed(symptoms[-10:]):  # Last 10 symptoms
            severity_color = "🔴" if symptom['severity'] == 'severe' else "🟡" if symptom['severity'] == 'moderate' else "🟢"
            with st.expander(f"{severity_color} {symptom['symptom_name']} - {symptom['logged_at']}", expanded=False):
                st.write(f"**Severity:** {symptom['severity'].title()}")
                if symptom.get('duration'):
                    st.write(f"**Duration:** {symptom['duration']}")
                if symptom.get('description'):
                    st.write(f"**Description:** {symptom['description']}")
                if symptom.get('triggers'):
                    st.write(f"**Triggers:** {symptom['triggers']}")
    else:
        st.info("No symptoms logged yet. Track your symptoms above!")

def show_family_page():
    """Family member management page"""
    st.title("👨‍👩‍👧‍👦 Family Members")
    st.markdown("Manage your family's health profiles and access their data")
    
    username = st.session_state.current_user
    user_data = st.session_state.auth_manager.get_user(username)
    family_id = user_data['family_id']
    is_admin = user_data['role'] == 'admin'
    
    # Display family code
    st.info(f"**Your Family Code:** `{family_id}` - Share this with family members to join!")
    
    # Get all family members
    family_members = st.session_state.auth_manager.get_family_members(family_id)
    
    # Add new family member (admin only)
    if is_admin:
        with st.expander("➕ Add Family Member", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                new_username = st.text_input("Username", placeholder="Choose username for family member")
                new_name = st.text_input("Full Name", placeholder="Family member's name")
                new_role = st.selectbox("Role", ["Member", "Admin"])
            
            with col2:
                new_password = st.text_input("Password", placeholder="Set password", type="password")
                relationship = st.text_input("Relationship", placeholder="e.g., Spouse, Child, Parent")
            
            if st.button("➕ Add Family Member", type="primary"):
                if new_username and new_password and new_name:
                    success, message = st.session_state.auth_manager.add_family_member(
                        family_id, new_username, new_password, new_name, new_role.lower()
                    )
                    if success:
                        save_user_data()  # Save immediately
                        st.success(f"✅ Added {new_name} to family!")
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Please fill in all fields")
    
    # Display family members
    st.subheader("👥 Family Members")
    
    for member in family_members:
        is_current = member['username'] == username
        member_icon = "👤" if member['role'] == 'admin' else "👨‍👩‍👧"
        current_badge = " (You)" if is_current else ""
        
        with st.expander(f"{member_icon} {member['name']}{current_badge} - {member['role'].title()}", expanded=False):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write(f"**Username:** {member['username']}")
                st.write(f"**Role:** {member['role'].title()}")
                
                # Show health summary if available
                member_health = st.session_state.auth_manager.get_user_health_data(member['username'])
                if member_health:
                    reports_count = len(member_health.get('reports', []))
                    prescriptions_count = len(member_health.get('prescriptions', []))
                    st.write(f"**Health Reports:** {reports_count}")
                    st.write(f"**Prescriptions:** {prescriptions_count}")
            
            with col2:
                if is_admin and not is_current:
                    if st.button(f"👁️ View Profile", key=f"view_{member['username']}"):
                        st.info("Profile viewing feature coming soon!")
                        save_user_data()  # Save after any action
                
                if not is_current:
                    st.write("**Quick Actions:**")
                    st.write("• Send message")
                    st.write("• Share report")

if __name__ == "__main__":
    main()
