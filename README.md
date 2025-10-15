# 🤖 AI-Powered Resume Ranking System

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3.0-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![AI](https://img.shields.io/badge/AI-Powered-purple.svg)](https://openai.com)

> **Transform your hiring process with intelligent AI-driven resume analysis and ranking**

An advanced machine learning solution that revolutionizes recruitment by automatically analyzing, scoring, and ranking resumes against job descriptions with intelligent hiring recommendations.

## ✨ Features

### 🎯 **Dual Analysis Modes**
- **Multiple Resume Ranking**: Compare and rank multiple candidates simultaneously
- **Single Resume Analysis**: Deep-dive analysis of individual candidates with detailed section breakdowns

### 🧠 **AI-Powered Intelligence**
- **Natural Language Processing**: Advanced text analysis using sentence transformers
- **Semantic Similarity**: Context-aware matching between job requirements and candidate profiles
- **Section-wise Scoring**: Detailed analysis of Experience, Skills, Education, Projects, Certifications, and Achievements

### 🎨 **Professional HR Interface**
- **Modern Gradient Design**: Sleek, professional UI that impresses HR professionals
- **Interactive Threshold Control**: Customizable hiring thresholds with real-time slider
- **Smart Color Coding**: Green for recommended hires, red for non-recommendations
- **Responsive Design**: Works perfectly on all devices and screen sizes

### 📊 **Advanced Analytics**
- **Hiring Statistics Dashboard**: Total candidates, recommended hires, success rates
- **Visual Score Representations**: Progress bars and percentage displays
- **Detailed Section Breakdown**: Granular scoring for each resume section
- **Export-Ready Results**: Clean, professional result displays

### 🔧 **Technical Excellence**
- **Modular Architecture**: Clean, maintainable codebase with separation of concerns
- **Type Safety**: Pydantic models for robust data validation
- **Error Handling**: Comprehensive validation and user-friendly error messages
- **Security**: GDPR compliant with secure file handling

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- OpenAI API key

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/resume-ranking-system.git
cd resume-ranking-system
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
# Create .env file
echo "Open_API_key=your_openai_api_key_here" > .env
```

5. **Run the application**
```bash
python main.py
```

6. **Access the application**
Open your browser and navigate to `http://localhost:5000`

## 🎮 Usage Guide

### Step 1: Choose Analysis Mode
- **Multiple Resume Ranking**: Perfect for bulk hiring and candidate comparison
- **Single Resume Analysis**: Detailed individual candidate evaluation

### Step 2: Set Hiring Threshold
- Use the interactive slider to set your hiring threshold (0-100%)
- Candidates above the threshold will be marked for hiring (Green)
- Candidates below the threshold will be marked as not recommended (Red)

### Step 3: Enter Job Description
- Provide a detailed job description in the text area
- Include required skills, experience, and qualifications for best results

### Step 4: Upload Resumes
- **Multiple Mode**: Upload multiple PDF files simultaneously
- **Single Mode**: Upload one PDF file for detailed analysis
- Drag & drop or click to upload (Max 16MB per file)

### Step 5: Get AI-Powered Results
- **Multiple Mode**: View ranked candidates with hiring recommendations
- **Single Mode**: Get detailed section-wise analysis and hiring decision
- Export or share results with your team

## 🏗️ Project Architecture

```
resume-ranking-system/
│
├── app/
│   ├── __init__.py                 # Flask application factory
│   ├── api/v1/endpoints/
│   │   ├── __init__.py            # API endpoint aggregator
│   │   └── resume_endpoint.py     # Resume ranking endpoints
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py            # Application configuration
│   ├── core/
│   │   ├── __init__.py
│   │   └── file_utils.py          # File handling utilities
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py             # Pydantic data models
│   └── services/
│       ├── __init__.py
│       ├── resume_service.py      # Core resume processing
│       └── ranking_service.py     # Ranking algorithms
│
├── templates/
│   └── index.html                 # Modern web interface
├── static/                        # Static assets (auto-generated)
├── uploads/                       # Temporary file storage
├── main.py                        # Application entry point
├── requirements.txt               # Python dependencies
├── .env                          # Environment variables
├── .gitignore                    # Git ignore rules
└── README.md                     # This file
```

## 🛠️ Technology Stack

### Backend
- **Flask**: Web framework
- **Python 3.8+**: Core language
- **OpenAI GPT-4**: Text summarization and analysis
- **Sentence Transformers**: Semantic text analysis
- **scikit-learn**: Machine learning utilities
- **PyMuPDF**: PDF text extraction
- **Pydantic**: Data validation and serialization

### Frontend  
- **HTML5 & CSS3**: Modern web standards
- **Bootstrap 5.3**: Responsive framework
- **Font Awesome**: Icon library
- **Inter Font**: Professional typography
- **Vanilla JavaScript**: Interactive functionality

### AI & ML
- **all-MiniLM-L6-v2**: Fast semantic similarity
- **all-mpnet-base-v2**: High-accuracy text embeddings
- **Cosine Similarity**: Mathematical similarity scoring
- **Natural Language Processing**: Context-aware analysis

## 📡 API Documentation

### Endpoints

#### `GET /` 
Web interface for resume ranking

#### `POST /`
Process resumes via web form
- **Form Fields**: `job_desc`, `analysis_mode`, `threshold`, `resumes`
- **Returns**: HTML with results

#### `POST /api/rank`
JSON API for resume ranking
- **Content-Type**: `multipart/form-data`
- **Fields**: 
  - `job_desc` (string): Job description
  - `resumes` (files): PDF resume files
- **Returns**: JSON with ranking results

#### `GET /health`
Health check endpoint
- **Returns**: `{"status": "healthy", "service": "resume-ranking-api"}`

### Response Format

```json
{
  "ranked_resumes": [
    {
      "resume_name": "candidate.pdf",
      "combined_score": 0.85,
      "rank": 1,
      "should_hire": true,
      "hire_status": "HIRE"
    }
  ],
  "total_resumes": 1
}
```

## 🧪 Testing

Run the application test script:
```bash
python test_refactored_app.py
```

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**: Follow the existing code style and architecture
4. **Add tests**: Ensure your changes are tested
5. **Commit changes**: `git commit -m 'Add amazing feature'`
6. **Push to branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

### Development Guidelines
- Follow PEP 8 style guidelines
- Add type hints to new functions
- Update documentation for new features
- Ensure backwards compatibility

## 🐛 Issue Reporting

Found a bug or have a feature request? Please open an issue with:
- **Bug Reports**: Steps to reproduce, expected vs actual behavior
- **Feature Requests**: Detailed description and use case
- **Questions**: Use the discussion section

## 🔒 Security & Privacy

- **GDPR Compliant**: No permanent storage of personal data
- **Secure File Handling**: Automatic cleanup of uploaded files
- **API Key Security**: Environment-based configuration
- **Input Validation**: Comprehensive file and data validation

## 📊 Performance

- **Processing Speed**: ~2-3 seconds per resume
- **File Support**: PDF files up to 16MB
- **Concurrent Users**: Supports multiple simultaneous analyses
- **Scalability**: Modular architecture for easy scaling

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** for providing GPT-4 API
- **Hugging Face** for sentence transformer models
- **Flask Community** for the excellent web framework
- **Bootstrap Team** for the responsive CSS framework

<div align="center">

**Built with ❤️ for HR professionals worldwide**

⭐ **Star this repo if it helped you!** ⭐

</div>
