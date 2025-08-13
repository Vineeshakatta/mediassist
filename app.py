import streamlit as st
import os
from health_analyzer import HealthAnalyzer
from file_processor import FileProcessor
import tempfile

# Configure page
st.set_page_config(
    page_title="Health Report Analyzer",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("🏥 Health Report Analyzer")
    st.markdown("Upload your medical reports for AI-powered analysis and summaries")
    
    # Privacy notice
    with st.expander("📋 Privacy & Data Usage Notice", expanded=False):
        st.markdown("""
        **Your Privacy Matters:**
        - Your health reports are processed securely and temporarily
        - No data is permanently stored on our servers
        - Files are automatically deleted after processing
        - Analysis is performed using encrypted connections
        - We do not share your health information with third parties
        
        **Disclaimer:** This tool provides general information only and should not replace professional medical advice.
        Always consult with healthcare professionals for medical decisions.
        """)
    
    # Sidebar for instructions
    with st.sidebar:
        st.header("📖 Instructions")
        st.markdown("""
        **Supported Formats:**
        - PDF documents
        - Images (JPG, PNG, etc.)
        - Text files
        
        **What we analyze:**
        - Blood pressure readings
        - Cholesterol levels
        - Blood glucose levels
        - Lab test results
        - Vital signs
        - General health metrics
        
        **Tips:**
        - Ensure text is clearly visible
        - Upload complete reports
        - Check image quality for OCR
        """)
    
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
                    display_analysis_results(analysis_result, extracted_text)
                    
            except Exception as e:
                st.error(f"❌ Error processing file: {str(e)}")
                if tmp_file_path:
                    try:
                        os.unlink(tmp_file_path)
                    except:
                        pass

def display_analysis_results(analysis_result, extracted_text):
    """Display the analysis results in a structured format"""
    
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
Generated by Health Report Analyzer

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

if __name__ == "__main__":
    main()
