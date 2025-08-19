import streamlit as st
import os
from health_analyzer import HealthAnalyzer
from file_processor import FileProcessor
import tempfile
import json
from datetime import datetime
import pandas as pd

# Configure page
st.set_page_config(
    page_title="Smart Medi Assist AI",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    # Initialize session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'dashboard'
    if 'reports_history' not in st.session_state:
        st.session_state.reports_history = []
    if 'health_data' not in st.session_state:
        st.session_state.health_data = {}
    
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
            'insurance': '💼 Insurance Claims',
            'history': '📚 Health History'
        }
        
        for page_key, page_name in pages.items():
            if st.button(page_name, key=f"nav_{page_key}", use_container_width=True):
                st.session_state.current_page = page_key
        
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
    elif st.session_state.current_page == 'insurance':
        show_insurance_page()
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
    
    # Health Score Visualization
    if st.session_state.reports_history:
        st.markdown("### 📊 Health Score Trends")
        
        # Create health score trend chart
        if len(st.session_state.reports_history) > 1:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Calculate scores for each report
                scores = []
                dates = []
                for i in range(len(st.session_state.reports_history)):
                    subset = st.session_state.reports_history[:i+1]
                    score, _ = calculate_health_score(subset)
                    scores.append(score)
                    dates.append(st.session_state.reports_history[i]['date'][:10])
                
                # Create trend chart
                trend_data = pd.DataFrame({
                    'Date': dates,
                    'Health Score': scores
                })
                st.line_chart(trend_data.set_index('Date'))
            
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
                
                # Status indicator
                if recent_score >= 85:
                    st.success("🟢 Excellent Health Status")
                elif recent_score >= 70:
                    st.info("🟡 Good Health Status")
                else:
                    st.warning("🔴 Monitor Health Status")
    
    st.markdown("---")
    
    # Recent Activity
    st.markdown("---")
    
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
        if st.button("📁 Upload First Report"):
            st.session_state.current_page = 'upload'
            st.rerun()
    

def show_upload_page():
    """Upload and analysis page (original functionality)"""
    st.title("📋 Health Report Analysis")
    st.markdown("Upload your medical reports for AI-powered analysis and summaries")
    
    # Initialize processors
    if 'health_analyzer' not in st.session_state:
        st.session_state.health_analyzer = HealthAnalyzer()
    
    if 'file_processor' not in st.session_state:
        st.session_state.file_processor = FileProcessor()
    
    # File upload section
    st.header("📁 Upload Your Health Report")
    
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['pdf', 'txt', 'png', 'jpg', 'jpeg', 'bmp', 'tiff'],
        help="Upload your medical report in PDF, image, or text format"
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
                    display_analysis_results(analysis_result, extracted_text, uploaded_file.name)
                    
            except Exception as e:
                st.error(f"❌ Error processing file: {str(e)}")
                if tmp_file_path:
                    try:
                        os.unlink(tmp_file_path)
                    except:
                        pass

def display_analysis_results(analysis_result, extracted_text, filename):
    """Display the analysis results in a structured format"""
    
    # Save to history
    report_data = {
        'filename': filename,
        'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'summary': analysis_result.get('summary', ''),
        'concerns': analysis_result.get('concerns', []),
        'recommendations': analysis_result.get('recommendations', []),
        'metrics': analysis_result.get('metrics', []),
        'extracted_text': extracted_text
    }
    st.session_state.reports_history.append(report_data)
    
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

def show_insurance_page():
    """Insurance claims page"""
    st.title("💼 Insurance Claims Assistant")
    st.markdown("Generate insurance claim summaries from your health reports")
    
    # Insurance Claim Guide
    with st.expander("📚 Insurance Claim Guide", expanded=False):
        st.markdown("""
        ### How to Use This Tool
        1. **Select Claim Type**: Choose the appropriate insurance claim category
        2. **Select Reports**: Choose which health reports to include
        3. **Generate Summary**: Create a professional claim summary
        4. **Download**: Save the summary for submission
        
        ### What's Included in Claims
        - **Medical Summary**: Professional overview of health findings
        - **Supporting Evidence**: Key metrics and documented concerns
        - **Claim Justification**: Clear reasoning for insurance coverage
        - **Professional Format**: Insurance-ready documentation
        
        ### Important Notes
        - This tool generates supporting documentation only
        - Always consult with your healthcare provider
        - Review your insurance policy for specific requirements
        - Contact your insurance company for submission procedures
        """)
    
    if not st.session_state.reports_history:
        st.info("No reports available for insurance claims. Upload health reports first.")
        if st.button("📁 Upload Reports"):
            st.session_state.current_page = 'upload'
            st.rerun()
        return
    
    # Claim Type Selection
    st.subheader("🏷️ Select Claim Type")
    
    claim_types = {
        "🏥 Medical Treatment": {
            "description": "Claims for medical treatments, procedures, and consultations",
            "keywords": ["treatment", "procedure", "consultation", "therapy"]
        },
        "💊 Prescription Medications": {
            "description": "Claims for prescribed medications and pharmaceutical needs",
            "keywords": ["medication", "prescription", "pharmaceutical", "drug"]
        },
        "🔬 Diagnostic Testing": {
            "description": "Claims for lab tests, imaging, and diagnostic procedures",
            "keywords": ["lab test", "imaging", "diagnostic", "screening"]
        },
        "🚑 Emergency Care": {
            "description": "Claims for emergency room visits and urgent care",
            "keywords": ["emergency", "urgent", "acute", "immediate"]
        },
        "🏃 Preventive Care": {
            "description": "Claims for wellness exams and preventive healthcare",
            "keywords": ["wellness", "preventive", "checkup", "screening"]
        },
        "♿ Disability Support": {
            "description": "Claims for disability-related healthcare and support",
            "keywords": ["disability", "accommodation", "support", "assistance"]
        }
    }
    
    # Display claim type options
    selected_claim_type = st.radio(
        "Choose the type of insurance claim:",
        list(claim_types.keys()),
        help="Select the category that best matches your insurance claim needs"
    )
    
    # Show description for selected type
    if selected_claim_type:
        st.info(f"**{selected_claim_type}**: {claim_types[selected_claim_type]['description']}")
    
    st.markdown("---")
    st.subheader("📋 Generate Claim Summary")
    
    # Report selection
    report_options = [f"{r['filename']} ({r['date']})" for r in st.session_state.reports_history]
    selected_reports = st.multiselect(
        "Select reports for claim:",
        report_options,
        help="Choose one or more reports to include in your insurance claim"
    )
    
    if selected_reports and st.button("📄 Generate Claim Summary"):
        with st.spinner("Generating insurance claim summary..."):
            # Get selected report data
            selected_indices = [report_options.index(r) for r in selected_reports]
            claim_reports = [st.session_state.reports_history[i] for i in selected_indices]
            
            # Combine report data
            combined_summaries = []
            for r in claim_reports:
                concerns_text = ', '.join(r['concerns']) if r['concerns'] else 'None'
                
                metrics_list = []
                if r['metrics']:
                    for m in r['metrics']:
                        name = m.get('name', 'Unknown')
                        value = m.get('value', 'N/A')
                        metrics_list.append(f"{name}: {value}")
                metrics_text = ', '.join(metrics_list) if metrics_list else 'None'
                
                report_summary = (
                    f"Report: {r['filename']} (Date: {r['date']})\n"
                    f"Summary: {r['summary']}\n"
                    f"Key Concerns: {concerns_text}\n"
                    f"Metrics: {metrics_text}"
                )
                combined_summaries.append(report_summary)
            
            combined_summary = "\n\n".join(combined_summaries)
            
            # Generate enhanced claim summary with claim type
            claim_category = selected_claim_type.split(' ', 1)[1] if ' ' in selected_claim_type else selected_claim_type
            claim_summary = f"""
INSURANCE CLAIM SUMMARY
Claim Type: {selected_claim_type}
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}

CLAIM CATEGORY: {claim_category.upper()}
{claim_types[selected_claim_type]['description']}

PATIENT REPORTS SUMMARY:
{combined_summary}

MEDICAL NECESSITY JUSTIFICATION:
Based on the medical reports provided, this {claim_category.lower()} claim is supported by documented health concerns and medical findings. The reports demonstrate specific health metrics and professional medical analysis that justify the medical necessity for insurance coverage under the {claim_category.lower()} category.

SUPPORTING EVIDENCE:
- {len(claim_reports)} comprehensive medical report(s) analyzed
- AI-powered clinical analysis confirming health concerns
- Documented metrics and professional recommendations
- Evidence aligned with {claim_category.lower()} claim requirements

CLAIM SUMMARY:
This claim requests coverage for {claim_category.lower()} based on documented medical evidence. The supporting reports provide clear justification for the medical necessity of the requested coverage.

Please review the attached medical reports for complete clinical details and supporting documentation.

---
IMPORTANT DISCLAIMER: 
This summary is generated for insurance claim documentation purposes only. All medical decisions and treatments should be made in consultation with qualified healthcare professionals. This document does not constitute medical advice or guarantee insurance coverage approval.
            """
            
            st.success("✅ Claim Summary Generated!")
            st.text_area("Insurance Claim Summary:", value=claim_summary, height=400)
            
            # Download button with claim type in filename
            claim_type_safe = selected_claim_type.replace(" ", "_").replace("🏥", "").replace("💊", "").replace("🔬", "").replace("🚑", "").replace("🏃", "").replace("♿", "").strip()
            st.download_button(
                label="📥 Download Claim Summary",
                data=claim_summary,
                file_name=f"insurance_claim_{claim_type_safe}_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain"
            )

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
