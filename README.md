# AI Interview Assistant (Backend)

A Flask-based AI conversational agent backend designed to conduct voice-driven, interactive technical interviews. Powered by Gemini 2.5 Flash, the assistant dynamically adjusts its questioning based on the candidate's real-time audio responses, provides streamed conversational audio output, and generates comprehensive performance feedback metrics.

## Key Features
- **Dynamic Conversational AI:** Formulates an adaptive, 5-question interview loop using LangGraph orchestration (`InMemorySaver`) and the `gemini-2.5-flash` model.
- **Voice-to-Text Pipeline:** Automatically processes incoming speech audio data using AssemblyAI's transcription engine.
- **Streamed Text-to-Speech (TTS):** Generates natural conversational vocal responses using the Murf AI Falcon model, streaming encoded chunks (`base64`) back to the frontend to eliminate playback latency.
- **Structured JSON Evaluation:** Delivers automated performance scorecards, identifying technical strengths and targeted areas of improvement.

---

## Technical Stack
- **Framework:** Python, Flask, Flask-CORS
- **AI Infrastructure:** LangChain, LangGraph (`google_genai`)
- **API integrations:** AssemblyAI (STT), Murf AI (TTS)

---

## Core API Endpoints

### 1. Start Interview
- **Endpoint:** `/start-interview`
- **Method:** `POST`
- **Payload:**
  ```json
  { "subject": "React JS" }
Returns: Streamed chunked base64 audio chunks (text/plain).

2. Submit Answer
Endpoint: /submit-answer
Method: POST
Payload: multipart/form-data containing an audio recording blob (audio).
Returns: Streamed base64 audio for the subsequent question alongside custom response header X-Question-Number.

3. Get Performance Evaluation
Endpoint: /get-feedback
Method: POST
Returns: Structured JSON evaluation metrics.

Local Setup & Installation

1. Environment Variables Configuration
Create a .env file within your backend/ directory and configure the missing authentication credentials:

GOOGLE_API_KEY=your_gemini_api_key_here
MURF_API_KEY=your_murf_api_key_here
ASSEMBLYAI_API_KEY=your_assemblyai_api_key_here

3. Installation Steps
i Navigate into the project root directory:

cd InterviewAssistant

ii Install the necessary system dependencies:

pip install flask flask-cors python-dotenv requests assemblyai langchain-core langgraph google-genai

iii Boot up the local development engine:

python backend/app.py

---

### Step-by-Step Push Guide
To update the project files and push the changes directly up to your GitHub repository, execute these commands in your VS Code terminal:

# 1. Update the local file stage
git add README.md

# 2. Commit the new documentation structure
git commit -m "docs: upgrade README with comprehensive API routing and tech details"

# 3. Securely push changes to GitHub main branch
git push origin main
