from flask import Flask, request
from flask_cors import CORS
from dotenv import load_dotenv
import os
import requests
import base64
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
import tempfile
import json
import jsonify
import assemblyai as aai

load_dotenv() # Load environment variables from .env file
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MURF_API_KEY = os.getenv("MURF_API_KEY")
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

aai.settings.api_key = ASSEMBLYAI_API_KEY

model = init_chat_model(
    "google_genai:gemini-2.5-flash",
    api_key=GOOGLE_API_KEY,
)

checkpointer = InMemorySaver()

agent = create_agent(
    model=model,
    tools=[],
    checkpointer=checkpointer
)

current_subject = ""
thread_id = "interview_1"
question_count = 0

INTERVIEW_PROMPT = """You are Anisha, a friendly and conversational interviewer conducting a natural {subject} interview.

IMPORTANT GUIDELINES:
1. Ask exactly 5 questions total throughout the interview
2. Keep questions SHORT and CRISP (1-2 sentences maximum)
3. ALWAYS reference what the candidate ACTUALLY said in their previous answer - do NOT make up or assume their answers
4. Show genuine interest with brief acknowledgments based on their REAL responses
5. Adapt questions based on their ACTUAL responses - go deeper if they're strong, adjust if uncertain
6. Be warm and conversational but CONCISE
7. No lengthy explanations - just ask clear, direct questions

CRITICAL: Read the conversation history carefully. Only acknowledge what the candidate truly said, not what you think they might have said.

Keep it short, conversational, and adaptive!"""

FEEDBACK_PROMPT = """Based on our complete interview conversation, provide detailed feedback as JSON only:
    {{
    "subject": "<topic>",
    "candidate_score": <1-5>,
    "feedback": "<detailed strengths with specific examples 
    from their ACTUAL answers>",
    "areas_of_improvement": "<constructive suggestions based 
    on gaps you noticed>"
    }}
    Be specific - reference ACTUAL things they said during the interview."""

app = Flask(__name__)
CORS(app)

def stream_audio(text):
    
    url = "https://global.api.murf.ai/v1/speech/stream"
    headers = {
        "api-key": MURF_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
    "voice_id": "Anisha",
    "style": "Conversation",
    "text": text,
    "locale": "en-IN",
    "model": "FALCON",
    "format": "MP3",
    "sampleRate": 24000,
    "channelType": "MONO"
    }

    response = requests.post(url, headers=headers, json=data, stream=True)

    if response.status_code == 200:
        for chunk in response.iter_content(chunk_size=4096):
            if chunk:
                yield base64.b64encode(chunk).decode('utf-8') + "\n"
    else:
        print(f"Error: {response.status_code}")



@app.route('/start-interview', methods=['POST'])
def start_interview():
    # Handle the start interview logic here
    global current_subject, question_count, checkpointer, agent
    
    data = request.json
    current_subject = data.get("subject","python")
    question_count = 1

    checkpointer = InMemorySaver() # Reset conversation history

    agent = create_agent(
        model=model,
        tools=[],
        checkpointer=checkpointer
    )

    config = {"configurable": {"thread_id": thread_id}}
    formatted_prompt = INTERVIEW_PROMPT.format(subject=current_subject)

    response = agent.invoke({"messages": [{"role": "system", "content": formatted_prompt}, 
                               {"role": "user", "content": f"Start the interview with a warm greeting and ask the first question about {current_subject}. Keep it SHORT (1-2 sentences)."}]
                               }, config = config)
    
    question = response["messages"][-1].content
    return stream_audio(question), {"Content-Type": "text/plain"}

def speech_to_text(audio_path):
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio_path)
    return transcript.text if transcript.text else ""

@app.route('/submit-answer', methods=['POST'])
def submit_answer():
    global question_count
    audio_file = request.files['audio']
    question_count += 1
    temp_path = (tempfile.NamedTemporaryFile(delete=False, suffix=".webm")).name
    audio_file.save(temp_path)
    answer = speech_to_text(temp_path)
    os.unlink(temp_path)
    if not answer:
        answer = "Empty answer"
    
    config = {"configurable": {"thread_id": thread_id}}
    agent.invoke({"messages": [{"role": "user", "content": answer}]}, 
                 config = config)
    
    prompt = f"""The candidate just answered question {question_count - 1}.
Look at their ACTUAL answer above. Do NOT assume or make up what they said.
Now ask question {question_count} of 5:
1. Briefly acknowledge what they ACTUALLY said (1 sentence) quote their exact words if needed
2. Ask your next question that builds on their REAL response (1-2 sentences)
3. If they said "I don't know" or gave a wrong answer, acknowledge that and ask something simpler
4. Keep the TOTAL response under 3 sentences
Be conversational but CONCISE. Only reference what they truly said."""
    response = agent.invoke({"messages": [ {"role": "system", "content": prompt}]},
                 config=config)

    question = response["messages"][-1].content

    return (stream_audio(question), {"Content-Type": "text/plain", "X-Question-Number": str(question_count)})

@app.route("/get-feedback", methods=["POST"])
def get_feedback():

    config = {"configurable": {"thread_id": thread_id}}
    response = agent.invoke({"messages": [{"role": "user", "content": f"{FEEDBACK_PROMPT} \n Review the entire interview on {current_subject} and provide feedback based on their Actual answers."}]}, config=config)
    text = response["messages"][-1].content
    cleaned = text.strip()
    if "```" in cleaned:
        cleaned = cleaned.split("```")[1]
    if cleaned.startswith("json"):
        cleaned = cleaned[4:].strip()
    feedback = json.loads(cleaned)
    return jsonify({"success": True, "feedback": feedback})

app.run(debug=True, port=5000)


