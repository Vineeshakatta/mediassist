# Smart Medi Assist AI - Healthcare Intelligence Platform

## Overview

This is a comprehensive Streamlit-based health dashboard application branded as "Smart Medi Assist AI" with the tagline "healthcare intelligence platform". The application analyzes medical reports and health documents using AI-powered analysis, featuring a complete multi-page dashboard with enhanced sidebar navigation, gradient-styled metric cards, health score calculations with trend visualization, and logos/icons throughout. Users can upload various file formats (PDFs, images, text files) containing health information and receive automated analysis including key metric extraction, health summaries, concerns identification, and personalized recommendations. The system uses OpenAI's API for intelligent analysis combined with regex-based pattern matching for extracting common health metrics like blood pressure, cholesterol levels, glucose readings, and vital signs.

**Recent Enhancement**: Added comprehensive Query Assistant with 6 quick questions, enhanced Insurance Claims with detailed claim types and professional documentation guide, and created complete project documentation including technical architecture and feature demonstration guides.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit web application framework with multi-page dashboard
- **Branding**: "MediAssist AI" with medical stethoscope icon and "healthcare intelligence platform" tagline
- **Navigation**: Left sidebar navigation with 6 main sections using specific icons (📊 Dashboard, 📋 Report Analysis, 📈 Report Summary, 🤖 Query Assistant, 💼 Insurance Claims, 📚 Health History)
- **Layout**: Wide layout with persistent sidebar navigation and session state management
- **Visual Design**: Gradient-styled metric cards, color-coded health indicators, trend visualizations
- **Components**: Enhanced dashboard overview cards with gradients, health score with trend graphs, interactive chat interface, file upload system, timeline views, insurance claim generators
- **User Experience**: Multi-page application with persistent data across sessions, real-time processing, comprehensive analytics, and visual health score tracking with percentage values and trend indicators

### Backend Architecture
- **Core Processing Pipeline**: Three-layer architecture with specialized processors
  - **FileProcessor**: Handles file format detection and text extraction from multiple sources
  - **HealthAnalyzer**: Performs AI-powered analysis and metric extraction
  - **Utils Module**: Provides text sanitization, metric formatting, and validation utilities
- **Text Extraction Strategy**: Multi-format support using appropriate libraries for each file type
  - OCR for images using pytesseract and PIL
  - PDF text extraction using PyPDF2
  - Direct text file reading for plain text formats
- **Analysis Approach**: Hybrid system combining regex pattern matching for standard metrics with AI analysis for comprehensive insights

### Data Processing
- **Temporary File Handling**: Uses Python's tempfile module for secure temporary storage
- **Text Processing**: Multi-stage cleaning and sanitization pipeline
- **Metric Extraction**: Dual approach using both pattern matching and AI analysis
- **Validation**: Built-in health metric validation against normal ranges

### Security and Privacy
- **File Security**: Automatic deletion of uploaded files after processing
- **Data Privacy**: No permanent storage of user health information
- **API Security**: Encrypted connections for AI analysis requests

## External Dependencies

### AI Services
- **OpenAI API**: Primary AI analysis engine for health report interpretation and insight generation
- **Configuration**: API key-based authentication with environment variable management

### Image Processing
- **pytesseract**: Optical Character Recognition (OCR) for text extraction from medical images and scanned documents
- **PIL (Pillow)**: Image processing and format conversion for OCR preprocessing

### Document Processing
- **PyPDF2**: PDF text extraction for digital medical reports and lab results
- **Streamlit**: Web application framework for user interface and file handling

### Python Libraries
- **tempfile**: Secure temporary file management
- **re**: Regular expression pattern matching for health metric extraction
- **os**: Environment variable management and file system operations
- **json**: Data serialization for API responses
- **datetime**: Timestamp management for processing logs