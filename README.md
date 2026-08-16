# Tender Compliance System

An AI-powered Tender Compliance System that uses LLM-based document
analysis to extract tender requirements, evaluate company submissions,
generate compliance reports, and compare multiple companies.

## Overview

The system is designed to reduce the manual effort involved in reviewing
tender documents and evaluating company submissions against predefined
requirements. It processes tender requirement documents, extracts
structured requirements using an LLM, analyzes company documents, and
produces detailed compliance results and comparison reports.

## Key Features

-   LLM-based tender requirement extraction using Groq AI
-   Multi-format document support for PDF, DOCX, and TXT
-   Automated compliance analysis and requirement matching
-   Multi-company evaluation for a single tender
-   Company comparison dashboard
-   Detailed requirement-level compliance reports
-   Support for multiple document types per company
-   REST APIs using FastAPI
-   Interactive React frontend

## System Architecture

``` text
Tender Requirements Document
            |
            v
     Document Extraction
            |
            v
   LLM Requirement Extraction
            |
            v
   Structured Requirements
            |
            v
   Company Document Upload
            |
            v
   Compliance Analysis
            |
            v
     Compliance Results
            |
            v
   Company Comparison
            |
            v
      Final Evaluation
```

## Project Structure

``` text
Tender-Compliance-System/
|
├── backend/
│   ├── main.py
│   ├── models.py
│   ├── database.py
│   ├── compliance_checker.py
│   ├── extractor.py
│   ├── requirements_extractor.py
│   ├── config.py
│   ├── check_models.py
│   ├── requirements.txt
│   ├── requirements_extractor.py
│   ├── .env.example
│   └── .gitignore
|
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── CompanySubmission.js
│   │   │   ├── ComparisonDashboard.js
│   │   │   ├── ComplianceReport.js
│   │   │   ├── RequirementsUpload.js
│   │   │   ├── Statistics.js
│   │   │   ├── TenderCreate.js
│   │   │   └── TenderList.js
│   │   ├── App.js
│   │   ├── App.css
│   │   └── index.js
│   │
│   ├── package.json
│   └── .gitignore
|
├── .gitignore
└── README.md
```

## My Role

### Developer and Team Lead

I worked on the project as both a Developer and Team Lead.

My responsibilities included:

-   Leading the development team and coordinating project
    implementation.
-   Contributing to the overall system architecture and development
    workflow.
-   Developing backend functionality using Python and FastAPI.
-   Implementing the LLM-based tender requirement extraction workflow
    using Groq AI.
-   Working on document extraction and processing for tender and company
    submission documents.
-   Implementing and improving compliance analysis and requirement
    matching logic.
-   Contributing to the React frontend and integrating frontend
    components with backend APIs.
-   Coordinating the integration of frontend, backend,
    document-processing, and LLM components.
-   Reviewing code and debugging technical issues across the
    application.
-   Supporting team members in resolving implementation and integration
    issues.
-   Managing Git/GitHub-based collaboration and coordinating project
    versions.
-   Participating in testing, troubleshooting, and refinement of the
    overall application.

## Technology Stack

### Backend

-   Python
-   FastAPI
-   Pydantic
-   Groq AI
-   PyMuPDF
-   python-docx

### Frontend

-   React
-   React Bootstrap
-   Chart.js
-   Axios
-   JavaScript

### AI and Document Processing

-   Large Language Models
-   LLM-based requirement extraction
-   Document parsing
-   Requirement matching
-   Automated compliance evaluation

## Getting Started

### Prerequisites

-   Python 3.11+
-   Node.js 18+
-   npm
-   Groq API key

### Clone the Repository

``` bash
git clone https://github.com/AkashG-03/Tender-Compliance-System.git
cd Tender-Compliance-System
```

### Backend Setup

Navigate to the backend:

``` bash
cd backend
```

Create a virtual environment:

``` bash
python -m venv venv
```

Activate the virtual environment on Windows:

``` bash
venv\Scripts\activate
```

On Linux/macOS:

``` bash
source venv/bin/activate
```

Install the dependencies:

``` bash
pip install -r requirements.txt
```

### Configure Environment Variables

Create a `.env` file based on `.env.example` and add your Groq API key:

``` env
GROQ_API_KEY=your_actual_api_key_here
```

Do not commit the actual `.env` file or API keys to GitHub.

### Start the Backend

From the `backend` directory:

``` bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Backend:

``` text
http://127.0.0.1:8000
```

Swagger API documentation:

``` text
http://127.0.0.1:8000/docs
```

ReDoc:

``` text
http://127.0.0.1:8000/redoc
```

### Frontend Setup

Open another terminal and navigate to the frontend:

``` bash
cd frontend
```

Install dependencies:

``` bash
npm install
```

Start the React application:

``` bash
npm start
```

Frontend:

``` text
http://localhost:3000
```

## Usage

### 1. Create a Tender

Create a new tender by providing the tender name and description.

### 2. Upload Tender Requirements

Upload the tender requirements document. The system extracts and
structures individual requirements using the configured LLM.

Supported formats include:

-   PDF
-   DOCX
-   TXT

### 3. Submit Company Documents

Multiple companies can be evaluated against the same tender.

Each company can submit multiple documents, including:

-   Proposal
-   Technical Response
-   Financial Bid
-   Compliance Documents
-   Experience and Credentials
-   Other Supporting Documents

### 4. Analyze Compliance

The system evaluates company submissions against the extracted tender
requirements and generates requirement-level compliance results.

### 5. Generate Reports

The system provides:

-   Requirement-level compliance status
-   Compliance percentages
-   Company-level statistics
-   Detailed compliance reports
-   Supporting document information

### 6. Compare Companies

The comparison dashboard allows multiple companies to be evaluated side
by side using compliance percentages, rankings, statistics, and visual
analytics.

## System Workflow

``` text
Government Tender Document
            |
            v
    Extract Requirements
            |
            v
      LLM Processing
            |
            v
 Structured Requirements
            |
            v
 Company Response Documents
            |
            v
   Compliance Evaluation
            |
            v
   Compliance Percentages
            |
            v
 Company Comparison and Ranking
            |
            v
      Final Report
```

## Configuration

  Variable               Description                     Required
  ---------------------- ------------------------------- ----------
  `GROQ_API_KEY`         Groq API authentication key     Yes
  `GROQ_MODEL`           LLM model used for processing   No
  `USE_LLM_EXTRACTION`   Enables LLM-based extraction    No
  `API_HOST`             Backend host                    No
  `API_PORT`             Backend port                    No

## Supported Company Document Types

  -----------------------------------------------------------------------
  Document Type                       Purpose
  ----------------------------------- -----------------------------------
  Proposal                            Main company proposal

  Technical Response                  Technical specifications and
                                      approach

  Financial Bid                       Pricing and financial information

  Compliance Document                 Compliance certificates and
                                      supporting documents

  Experience and Credentials          Previous projects and
                                      qualifications

  Other                               Additional supporting documents
  -----------------------------------------------------------------------

## Example Use Case

A tender contains numerous technical, financial, eligibility, and
compliance requirements. Multiple companies submit their proposals and
supporting documents.

The system processes the tender requirements, evaluates each company's
documents, calculates compliance results, and provides a comparison
dashboard to support structured evaluation.

``` text
Tender Document
      |
      v
Requirement Extraction
      |
      +------------------+------------------+
      |                  |                  |
      v                  v                  v
 Company A           Company B          Company C
 Documents           Documents          Documents
      |                  |                  |
      +------------------+------------------+
                         |
                         v
               Compliance Analysis
                         |
                         v
              Comparison Dashboard
                         |
                         v
                 Final Evaluation
```

## Security

-   API keys are managed through environment variables.
-   `.env` files are excluded from version control.
-   `.env.example` is provided as a configuration template.
-   Sensitive credentials should never be committed to the repository.

## Troubleshooting

### Backend Does Not Start

Check the Python version:

``` bash
python --version
```

Install dependencies again if required:

``` bash
pip install -r requirements.txt
```

Make sure the virtual environment is activated.

### LLM Extraction Is Not Working

Verify that the `.env` file contains a valid Groq API key:

``` env
GROQ_API_KEY=your_actual_api_key_here
```

Also verify that the configured Groq model is available for your API
account.

### Frontend Does Not Start

Reinstall dependencies:

``` bash
npm install
```

If required, remove `node_modules` and reinstall the dependencies.

### CORS Errors

Ensure that the FastAPI backend is running on:

``` text
http://127.0.0.1:8000
```

and the React frontend is running on:

``` text
http://localhost:3000
```

## Future Enhancements

-   Improve semantic matching and compliance scoring
-   Add advanced document chunking and retrieval
-   Support additional document formats
-   Add authentication and role-based access control
-   Improve report export capabilities
-   Add automated RAG and compliance evaluation metrics
-   Add persistent database storage
-   Deploy the backend and frontend using cloud infrastructure
-   Add automated testing and CI/CD pipelines

## Project Information

**Project Type:** Team Project

**Role:** Developer and Team Lead

The project demonstrates practical experience in LLM integration,
document processing, automated compliance analysis, FastAPI backend
development, React frontend development, team leadership, Git/GitHub
collaboration, and full-stack system integration.

## License

This project is available under the MIT License.
