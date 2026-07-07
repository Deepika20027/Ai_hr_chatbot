
# AI-Powered HR Chatbot for Smart Candidate Screening

An AI-driven HR chatbot web application that automates candidate screening by generating interview questions and evaluating candidate answers using Google Gemini 2.0 Flash — replacing subjective manual review with objective, data-driven scoring.

## 📌 Overview

This project was developed as a Capstone Project (Summer Internship Program 2025) at **IGDTUW's IT Department**, in association with **Sansoftech Services Private Limited**. It streamlines the initial candidate screening process for HR teams by leveraging Generative AI for dynamic question generation and automated answer evaluation.

## 🎯 Objectives

- Automate HR screening question generation and candidate answer evaluation
- Enhance objectivity and consistency in recruitment using AI-based scoring
- Build a full-stack application with separate candidate and recruiter interfaces
- Apply prompt engineering to control LLM output format and evaluation criteria

## ✨ Features

**Candidate Interface**
- Register/Login
- Dashboard showing application status (Not Started / Completed)
- Interactive chat-based interview (AI-generated questions)
- Auto-submission and confirmation on completion

**Recruiter Interface**
- Recruiter Login/Signup
- Dashboard listing all candidates with average scores and status (selected / completed / not started)
- Filter candidates by status
- Detailed candidate view: question-wise answers, AI-generated scores (out of 5.0), and justifications
- Select/Reject candidate actions with AI-based suggestions

## 🛠️ Tech Stack

**Backend**
- Flask (Python web framework)
- Flask-SQLAlchemy (ORM)
- SQL (database)
- Werkzeug.security (password hashing)
- python-dotenv (environment variable management)
- Flask-CORS (cross-origin handling)

**Frontend**
- Next.js
- Tailwind CSS
- JavaScript (ES6+)

**Generative AI**
- Google Gemini 2.0 Flash API (question generation + answer evaluation)

## 🧠 How the AI Works

1. **Question Generation**: Gemini generates 10 HR screening questions, returned as a structured JSON array.
2. **Answer Evaluation**: For each candidate answer, Gemini returns:
   - A **score** (1.0–5.0)
   - A **justification** (brief text)

   Evaluation considers: relevance, clarity, depth and insight, professionalism, and conciseness.

   Prompt engineering techniques used:
   - Strict `responseSchema` enforcement for structured JSON output
   - Low `temperature` (0.2) for consistent scoring
   - `maxOutputTokens` limit to keep justifications concise

## 📂 Project Structure

```
ai_hr_chatbot/
├── backend/          # Flask API, Gemini integration, DB models
├── frontend/         # Next.js + Tailwind CSS UI (candidate + recruiter)
├── .env.example       # Sample environment variables
├── requirements.txt   # Python dependencies
└── README.md
```

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.9+
- Node.js & npm
- Google Gemini API key

### Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

Create a `.env` file in the backend folder:
```
GEMINI_API_KEY=your_api_key_here
GEMINI_API_BASE_URL=your_gemini_api_base_url
```

Run the Flask server:
```bash
python app.py
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:3000` in your browser.

## 📊 Evaluation Approach

Since this project uses prompt engineering (not model training), evaluation was qualitative:
- Manual testing with real user inputs
- Edge case testing (short/irrelevant answers)
- Visual inspection of question coherence and justification clarity
- API latency/responsiveness monitoring

## ⚠️ Limitations

- Performance depends entirely on prompt quality
- May lack deep industry-specific nuance
- Potential for inherited LLM bias
- API latency from sequential Gemini calls

## 🚀 Future Scope

- Sentiment analysis / keyword extraction for deeper insights
- Role-specific personalized question generation
- Multi-turn conversational interviews with follow-ups
- Bias detection and mitigation
- Recruiter feedback loop to improve AI performance
- Migration to PostgreSQL and cloud deployment (Docker, AWS/GCP)
- Enhanced dashboards and richer reporting

