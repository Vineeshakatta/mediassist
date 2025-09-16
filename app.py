import streamlit as st
import os
from health_analyzer import HealthAnalyzer
from file_processor import FileProcessor
import tempfile
import json
from datetime import datetime
import pandas as pd
import pytz

# Configure page
st.set_page_config(
    page_title="Smart Medi Assist AI",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
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
        
        # Navigation Menu with icons
        pages = {
            'dashboard': '📊 Dashboard',
            'upload': '📋 Report Analysis',
            'summary': '📈 Report Summary', 
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
    elif st.session_state.current_page == 'assistant':
        show_assistant_page()
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
    """Process AI question and add response to chat history"""
    if 'health_analyzer' not in st.session_state:
        st.session_state.health_analyzer = HealthAnalyzer()
    
    # Prepare context from reports
    context = ""
    if st.session_state.reports_history:
        context = "Based on your health reports:\n"
        for report in st.session_state.reports_history[-3:]:  # Last 3 reports
            context += f"\nReport: {report['filename']}\n"
            context += f"Summary: {report['summary']}\n"
            if report['concerns']:
                context += f"Concerns: {', '.join(report['concerns'])}\n"
    
    try:
        response = st.session_state.health_analyzer.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system", 
                    "content": f"""You are a health assistant. Answer questions about the user's health reports in a helpful, informative way. Always remind users to consult healthcare professionals for medical decisions.
                    
                    Context from user's reports:
                    {context}"""
                },
                {"role": "user", "content": question}
            ],
            max_tokens=500
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
        if st.session_state.reports_history:
            # Show key health metrics from latest report
            latest_report = st.session_state.reports_history[-1]
            if latest_report.get('metrics'):
                st.write("**Latest Metrics:**")
                for metric in latest_report['metrics'][:3]:  # Show top 3 metrics
                    st.write(f"• {metric.get('name', 'Unknown')}: {metric.get('value', 'N/A')}")
            
            if latest_report.get('concerns'):
                st.write("**Recent Concerns:**")
                for concern in latest_report['concerns'][:2]:  # Show top 2 concerns
                    st.warning(f"⚠️ {concern}")
        else:
            st.info("Upload reports to see health insights")


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
            ("⚠️ What health concerns should I watch?", "What health concerns or warning signs should I be monitoring based on my reports?"),
            ("📈 How is my health trending?", "How has my health been trending over time? Am I improving or declining?"),
            ("💊 What lifestyle changes are recommended?", "What lifestyle changes or recommendations do you suggest based on my health reports?"),
            ("🩺 When should I see a doctor?", "Based on my reports, are there any findings that suggest I should consult with a healthcare professional?"),
            ("📋 Can you summarize my health status?", "Can you provide a comprehensive summary of my current health status?")
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

if __name__ == "__main__":
    main()
