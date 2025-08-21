# MediAssist AI - Technical Architecture Document
## System Design & Implementation Details

---

## 📋 Architecture Overview

MediAssist AI is built as a modern healthcare intelligence platform using a modular architecture that separates concerns and ensures scalability, security, and maintainability.

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend Layer                          │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐  │
│  │   Streamlit     │ │   UI Components │ │   Navigation    │  │
│  │   Web App       │ │   & Branding    │ │   System        │  │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│                      Application Layer                         │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐  │
│  │   File          │ │   Health        │ │   Utils &       │  │
│  │   Processor     │ │   Analyzer      │ │   Validation    │  │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│                       Services Layer                           │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐  │
│  │   OpenAI        │ │   OCR           │ │   PDF           │  │
│  │   GPT-4 API     │ │   Processing    │ │   Processing    │  │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Core Components

### 1. Frontend Architecture (app.py)

**Framework**: Streamlit with custom configuration
**Layout**: Wide layout with persistent sidebar navigation
**State Management**: Session-based with Streamlit's session state

```python
# Core UI Structure
st.set_page_config(
    page_title="MediAssist AI",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Navigation System
PAGES = {
    "📊 Dashboard": "dashboard",
    "📋 Report Analysis": "upload", 
    "📈 Report Summary": "summary",
    "🤖 Query Assistant": "assistant",
    "💼 Insurance Claims": "insurance",
    "📚 Health History": "history"
}
```

**Key Features**:
- Responsive design with mobile compatibility
- Professional healthcare branding
- Gradient-styled metric cards
- Color-coded health indicators
- Icon-based navigation system

### 2. File Processing Layer (file_processor.py)

**Multi-Format Support Architecture**:

```python
class FileProcessor:
    def process_file(self, uploaded_file):
        # Format detection and routing
        if file_type == "pdf":
            return self._extract_from_pdf(file)
        elif file_type in ["jpg", "jpeg", "png"]:
            return self._extract_from_image(file) 
        elif file_type == "txt":
            return self._extract_from_text(file)
```

**Processing Pipeline**:
1. **File Upload** → Streamlit file uploader
2. **Format Detection** → File extension analysis
3. **Temporary Storage** → Python tempfile module
4. **Content Extraction** → Format-specific processors
5. **Security Cleanup** → Automatic file deletion

**Extraction Methods**:
- **PDF Processing**: PyPDF2 library for digital text extraction
- **Image Processing**: PIL + pytesseract for OCR
- **Text Processing**: Direct file reading with encoding detection

### 3. AI Analysis Engine (health_analyzer.py)

**OpenAI Integration Architecture**:

```python
class HealthAnalyzer:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
    def analyze_health_report(self, text_content):
        # Dual analysis approach
        extracted_metrics = self._extract_metrics_with_regex(text_content)
        ai_analysis = self._get_ai_analysis(text_content)
        return self._combine_results(extracted_metrics, ai_analysis)
```

**Analysis Pipeline**:
1. **Regex Pattern Matching** → Standard health metrics
2. **AI Analysis** → GPT-4 powered interpretation
3. **Result Synthesis** → Combined structured output
4. **Validation** → Health metric verification
5. **Formatting** → User-friendly presentation

**Health Metrics Extracted**:
- Blood Pressure (systolic/diastolic)
- Heart Rate and Pulse
- Cholesterol (Total, HDL, LDL, Triglycerides)
- Blood Glucose levels
- BMI and Weight measurements
- Temperature readings
- Laboratory values (CBC, CMP, etc.)

### 4. Utility Functions (utils.py)

**Text Processing Pipeline**:

```python
def sanitize_text(text):
    # Multi-stage cleaning
    text = remove_special_characters(text)
    text = normalize_whitespace(text) 
    text = fix_encoding_issues(text)
    return text

def validate_health_metric(metric_name, value):
    # Range validation against medical standards
    normal_ranges = {
        "systolic_bp": (90, 140),
        "diastolic_bp": (60, 90),
        "heart_rate": (60, 100),
        # ... additional ranges
    }
```

**Key Utilities**:
- Text sanitization and normalization
- Health metric validation
- Date parsing and formatting
- Number extraction and conversion
- Medical terminology standardization

---

## 🔐 Security Architecture

### Data Privacy Implementation

**File Security Model**:
```python
# Temporary file handling
with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
    tmp_file.write(uploaded_file.getvalue())
    file_path = tmp_file.name

try:
    # Process file
    result = process_document(file_path)
finally:
    # Guaranteed cleanup
    os.unlink(file_path)
```

**Privacy Principles**:
- **No Permanent Storage** → Files deleted immediately after processing
- **Session-Only Data** → Health information exists only during session
- **Secure API Calls** → Encrypted communication with OpenAI
- **Local Processing** → OCR and regex processing done locally
- **Environment Secrets** → API keys stored in environment variables

### API Security

**OpenAI Integration Security**:
- API key stored in environment variables
- Request timeout handling
- Error handling without exposing sensitive data
- Rate limiting awareness
- Secure JSON communication

---

## 📊 Data Flow Architecture

### Complete Processing Flow

```
User Upload
    ↓
┌───────────────────┐
│ File Upload       │ ← Streamlit file uploader
│ (PDF/Image/Text)  │
└───────┬───────────┘
        ↓
┌───────────────────┐
│ Temporary Storage │ ← Python tempfile
│ & Format Check    │
└───────┬───────────┘
        ↓
┌───────────────────┐
│ Content Extraction│ ← Format-specific processors
│ (OCR/PDF/Text)    │
└───────┬───────────┘
        ↓
┌───────────────────┐
│ Text Processing   │ ← Sanitization & validation
│ & Sanitization    │
└───────┬───────────┘
        ↓
┌───────────────────┐
│ Dual Analysis     │ ← Regex patterns + AI
│ (Regex + GPT-4)   │
└───────┬───────────┘
        ↓
┌───────────────────┐
│ Results Synthesis │ ← Combine & structure results
│ & Validation      │
└───────┬───────────┘
        ↓
┌───────────────────┐
│ UI Presentation   │ ← Streamlit display
│ & Storage         │
└───────┬───────────┘
        ↓
┌───────────────────┐
│ Secure Cleanup    │ ← File deletion
│ & Session Store   │
└───────────────────┘
```

### State Management

**Session State Architecture**:
```python
# Initialize session state
if 'reports_history' not in st.session_state:
    st.session_state.reports_history = []

if 'health_analyzer' not in st.session_state:
    st.session_state.health_analyzer = HealthAnalyzer()

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
```

**Data Structures**:
```python
# Report storage structure
report_data = {
    'filename': str,
    'timestamp': datetime,
    'raw_text': str,
    'summary': str,
    'metrics': list,
    'concerns': list,
    'recommendations': list,
    'health_score': float
}

# Chat history structure  
chat_message = {
    'role': 'user' | 'assistant',
    'content': str,
    'timestamp': datetime
}
```

---

## 🧠 AI Integration Architecture

### GPT-4 Prompt Engineering

**System Prompt Structure**:
```python
HEALTH_ANALYSIS_PROMPT = """
You are a medical analysis assistant. Analyze the provided health report and:

1. Extract key health metrics with values and units
2. Identify any concerning findings or abnormal values  
3. Provide clear, actionable health recommendations
4. Summarize overall health status
5. Flag any urgent medical attention needs

Always include appropriate medical disclaimers and remind users to consult healthcare professionals.

Context: {patient_history}
Report Content: {document_text}
"""
```

**Response Processing Pipeline**:
1. **Context Preparation** → Include patient history
2. **Prompt Construction** → Medical analysis instructions  
3. **API Request** → GPT-4 processing
4. **Response Parsing** → Extract structured data
5. **Validation** → Verify medical logic
6. **Formatting** → User-friendly display

### Query Assistant AI System

**Conversational AI Architecture**:
```python
def process_ai_question(question):
    # Context building from user history
    context = build_medical_context(st.session_state.reports_history)
    
    # AI processing with medical safety
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": MEDICAL_ASSISTANT_PROMPT},
            {"role": "user", "content": question}
        ],
        max_tokens=500
    )
```

**Quick Questions System**:
- Pre-defined medical queries
- One-click question processing
- Context-aware responses
- Medical safety disclaimers

---

## 🏥 Health Intelligence Features

### Health Score Calculation Algorithm

```python
def calculate_health_score(metrics, concerns):
    base_score = 100
    
    # Deduct points for abnormal metrics
    for metric in metrics:
        if is_abnormal(metric):
            severity = assess_severity(metric)
            base_score -= severity_penalties[severity]
    
    # Additional deductions for identified concerns
    for concern in concerns:
        concern_weight = assess_concern_severity(concern)
        base_score -= concern_weight
    
    # Ensure score bounds
    return max(0, min(100, base_score))
```

**Trend Analysis System**:
```python
def calculate_health_trend(historical_scores):
    if len(historical_scores) < 2:
        return "neutral"
        
    recent_avg = mean(historical_scores[-3:])  # Last 3 scores
    previous_avg = mean(historical_scores[-6:-3])  # Previous 3 scores
    
    if recent_avg > previous_avg + 5:
        return "improving"
    elif recent_avg < previous_avg - 5:
        return "declining" 
    else:
        return "stable"
```

### Insurance Claims Generation

**Professional Documentation System**:
```python
def generate_insurance_claim(claim_type, selected_reports):
    # Template-based generation
    claim_template = get_claim_template(claim_type)
    
    # Medical evidence compilation
    evidence = compile_medical_evidence(selected_reports)
    
    # Professional formatting
    formatted_claim = format_insurance_document(
        claim_type=claim_type,
        evidence=evidence,
        justification=generate_justification(evidence),
        patient_summary=create_patient_summary(selected_reports)
    )
    
    return formatted_claim
```

**Claim Types Supported**:
- Medical Treatment procedures
- Prescription Medications
- Diagnostic Testing
- Emergency Care
- Preventive Care
- Disability Support

---

## ⚡ Performance Architecture

### Optimization Strategies

**File Processing Optimization**:
- Asynchronous OCR processing where possible
- Efficient PDF parsing with page limits
- Image compression before OCR
- Text caching for repeated analysis

**API Optimization**:
- Request batching for multiple metrics
- Response caching for common queries
- Error handling with graceful degradation
- Timeout management for user experience

**UI Performance**:
- Lazy loading of historical data
- Efficient session state management
- Minimal DOM updates
- Progressive disclosure of information

### Scalability Considerations

**Horizontal Scaling Readiness**:
- Stateless processing design
- External API dependency isolation
- Session-based data model
- Modular component architecture

**Resource Management**:
- Memory-efficient file processing
- Automatic cleanup routines
- Limited session data retention
- Efficient regex compilation

---

## 🔧 Configuration Management

### Environment Configuration

```toml
# .streamlit/config.toml
[server]
headless = true
address = "0.0.0.0"
port = 5000

[theme]
base = "light"
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
```

**Environment Variables**:
```bash
OPENAI_API_KEY=<api_key>          # Required for AI analysis
TESSEREACT_CMD=<path>             # OCR engine path (optional)
```

### Dependency Management

```python
# Core dependencies
streamlit >= 1.28.0     # Web framework
openai >= 1.0.0         # AI analysis
pillow >= 9.0.0         # Image processing  
pytesseract >= 0.3.10   # OCR capabilities
pypdf2 >= 3.0.0         # PDF processing
pandas >= 1.5.0         # Data manipulation
```

---

## 🚀 Deployment Architecture

### Replit Deployment Configuration

**Workflow Configuration**:
```python
# Configured workflow
name: "Health Report Analyzer"
command: "streamlit run app.py --server.port 5000"
output_type: "webview"
wait_for_port: 5000
```

**Production Readiness**:
- Port 5000 configuration for Replit
- Headless server configuration
- Error handling for production use
- Security configurations applied

### Monitoring & Logging

**Application Monitoring**:
- Streamlit built-in metrics
- Error tracking and handling
- Performance monitoring
- User session analytics

**Health & Status Checks**:
- API connectivity verification
- OCR engine availability
- File processing capabilities
- Memory usage monitoring

---

## 📊 Testing Strategy

### Unit Testing Architecture

```python
# Example test structure
class TestHealthAnalyzer:
    def test_metric_extraction(self):
        # Test regex pattern matching
        sample_text = "Blood pressure: 120/80 mmHg"
        metrics = extract_metrics(sample_text)
        assert len(metrics) > 0
        
    def test_ai_analysis(self):
        # Test AI integration (with mocking)
        # Verify response structure and content
        
    def test_health_score_calculation(self):
        # Test scoring algorithm
        # Verify score bounds and logic
```

### Integration Testing

**File Processing Tests**:
- PDF extraction accuracy
- OCR functionality verification
- Text processing pipeline
- Error handling validation

**AI Integration Tests**:
- API connectivity verification
- Response parsing accuracy
- Error handling robustness
- Rate limiting compliance

---

## 🔮 Future Architecture Considerations

### Extensibility Design

**Plugin Architecture Readiness**:
- Modular component design
- Interface-based development
- Configuration-driven features
- API endpoint preparation

**Database Integration Preparation**:
- Current session-state can be replaced with database
- Data model already structured for persistence
- Migration path for user accounts
- Privacy-compliant data storage design

### Advanced Feature Architecture

**Machine Learning Integration**:
- Health trend prediction models
- Anomaly detection systems
- Personalized recommendation engines
- Risk assessment algorithms

**Enterprise Features**:
- Multi-tenant architecture support
- Role-based access control
- Audit logging capabilities
- Compliance framework integration

---

## 📚 Documentation Architecture

### Code Documentation Standards

**Docstring Format**:
```python
def analyze_health_report(self, text_content):
    """
    Analyze health report text using AI and regex extraction.
    
    Args:
        text_content (str): Raw text from medical document
        
    Returns:
        dict: Analysis results with metrics, summary, concerns
        
    Raises:
        AnalysisError: If analysis fails or API unavailable
    """
```

**Architecture Documentation**:
- System design documentation (this document)
- API documentation for integrations
- User guides and tutorials
- Deployment and configuration guides

---

**MediAssist AI - Technical Architecture Document**  
*Comprehensive system design for healthcare intelligence platform*

*Version: 1.0*  
*Last Updated: January 2025*  
*Architecture: Streamlit + OpenAI GPT-4 + Multi-format Processing*