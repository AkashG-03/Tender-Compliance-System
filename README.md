# 🎯 Tender Compliance System

AI-powered tender requirements compliance checker using LLM-based document analysis.

## ✨ Features

- 🤖 **LLM-based Requirements Extraction** using Groq AI
- 📄 **Multi-format Document Support** (PDF, DOCX, TXT)
- 🔍 **Intelligent Compliance Analysis** with semantic matching
- 📊 **Company Comparison Dashboard** with visual analytics
- 🏢 **Multi-company Evaluation** for each tender
- 📈 **Detailed Compliance Reports** with requirement-level analysis

## 🏗️ Architecture

tender-analyzer-new/
├── backend/ # FastAPI backend
│ ├── main.py # API endpoints
│ ├── models.py # Data models
│ ├── database.py # JSON database handler
│ ├── requirements_extractor.py # Basic extractor
│ ├── llm_requirements_extractor.py # LLM-based extractor
│ ├── compliance_checker.py # Compliance analysis
│ ├── config.py # Configuration
│ └── data/ # Data storage (auto-created)
│
└── frontend/ # React frontend
├── src/
│ ├── components/ # React components
│ ├── App.js # Main application
│ └── App.css # Styling
└── public/ # Static files



## 🚀 Setup Instructions

### Prerequisites

- Python 3.11+
- Node.js 18+
- Groq API Key ([Get it here](https://console.groq.com/keys))

### Backend Setup

1. **Clone the repository**
git clone https://github.com/Khaushik-Yahav/Tender.git
cd Tender
git checkout version-3


2. **Create virtual environment**

python -m venv venv

Windows
venv\Scripts\activate

Linux/Mac
source venv/bin/activate


3. **Install dependencies**


cd backend
pip install -r requirements.txt


4. **Configure environment variables**


Copy example env file
cp .env.example .env

Edit .env and add your Groq API key
GROQ_API_KEY=your_actual_api_key_here


5. **Run backend server**

uvicorn main:app --reload --host 127.0.0.1 --port 8000


Backend will start at: `http://127.0.0.1:8000`
API docs at: `http://127.0.0.1:8000/docs`

### Frontend Setup

1. **Install dependencies**


cd frontend
npm install


2. **Start development server**
npm start


Frontend will open at: `http://localhost:3000`

## 📖 Usage Guide

### 1. Create a Tender

1. Click **"Create New Tender"**
2. Enter tender name and description
3. Click **"Create Tender"**

### 2. Upload Requirements Document

1. Select the tender from the list
2. Click **"Upload Req"**
3. Upload the government requirements document (PDF/DOCX)
4. System will automatically extract requirements using LLM

### 3. Submit Company Responses

1. Click **"Submit"** on the tender
2. Enter company name
3. Select document type (Proposal, Technical, Financial, etc.)
4. Upload company's response documents
5. Repeat for multiple documents from the same company
6. Repeat for multiple companies

### 4. Analyze Compliance

1. After uploading all documents, click **"Analyze Compliance"**
2. System will check each requirement against company documents
3. View detailed compliance report

### 5. Compare Companies

1. Click **"Compare"** to see side-by-side comparison
2. View rankings, compliance percentages, and visual charts

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GROQ_API_KEY` | Your Groq API key (required) | - |
| `GROQ_MODEL` | LLM model to use | `llama-3.1-70b-versatile` |
| `USE_LLM_EXTRACTION` | Enable LLM-based extraction | `true` |
| `API_HOST` | Backend host | `127.0.0.1` |
| `API_PORT` | Backend port | `8000` |

### Document Types

Companies can submit multiple document types:
- **Proposal** - Main proposal document
- **Technical Response** - Technical specifications and approach
- **Financial Bid** - Pricing and financial details
- **Compliance Document** - Compliance certificates
- **Experience & Credentials** - Past projects and qualifications
- **Other** - Supporting documents

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Groq AI** - LLM for intelligent requirements extraction
- **PyMuPDF** - PDF processing
- **python-docx** - DOCX processing
- **Pydantic** - Data validation

### Frontend
- **React** - UI framework
- **React Bootstrap** - UI components
- **Chart.js** - Data visualization
- **Axios** - HTTP client

## 📊 System Flow

Government uploads tender requirements document
↓

LLM extracts specific requirements (20-30 precise requirements)
↓

Companies submit response documents (multiple files per company)
↓

System analyzes each requirement against company documents
↓

Generate compliance report (% match, met/missing requirements)
↓

Compare multiple companies and rank them


## 🐛 Troubleshooting

### Backend won't start
- Ensure virtual environment is activated
- Check all dependencies are installed: `pip install -r requirements.txt`
- Verify Python version: `python --version` (should be 3.11+)

### LLM extraction not working
- Check `.env` file has valid `GROQ_API_KEY`
- Verify API key at https://console.groq.com/keys
- Check logs for error messages

### Frontend won't start
- Delete `node_modules` and `package-lock.json`
- Run `npm install` again
- Check Node.js version: `node --version` (should be 18+)

### CORS errors
- Ensure backend is running on port 8000
- Check CORS settings in `backend/main.py`

## 📝 API Documentation

Once backend is running, visit:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is open source and available under the MIT License.

## 👤 Author

**Khaushik Yahav**
- GitHub: [@Khaushik-Yahav](https://github.com/Khaushik-Yahav)

## 🙏 Acknowledgments

- Groq AI for LLM API
- FastAPI community
- React community


