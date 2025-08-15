# 🎙️ AI VOICE AGENTS

## Project Overview:

This project is part of the 30 Days of AI Voice Agents Challenge.
It is an AI-powered voice interaction system with the following key features:

1.Text-to-Speech (TTS) using Murf API
2.Speech-to-Text (STT) transcription using AssemblyAI API
3.Conversational AI Agent powered by Google Gemini API
4.Simple, responsive frontend UI built with HTML, CSS, JavaScript
5.Backend server implemented with FastAPI (Python)

The system allows users to record their voice, get transcriptions, interact with a conversational agent, and listen to AI-generated audio replies.

## 🛠️ Tech Stack:

### Frontend:

1.HTML5
2.CSS3
3.JavaScript (Vanilla)

### Backend:

1.FastAPI (Python)

### APIs & AI Models:

1.Murf API → Text-to-Speech conversion
2.AssemblyAI API → Speech-to-Text transcription
3.Google Gemini API → Conversational responses

## ⚙️ Features:

1.🎧 Text-to-Speech (TTS) – Converts typed text into natural-sounding audio using Murf AI.
2.🎙️ Echo Bot v2 – Captures audio input, sends it for transcription, and plays it back.
3.💬 LLM Audio Reply – Sends the transcription to Google Gemini and returns an AI-generated voice reply.
4.🖥️ Simple UI – Easy-to-use interface with start/stop recording controls.
5.🔄 Real-time Feedback – Displays transcription output instantly.

## 📂 Project Structure:

├── index.html        # Frontend UI
├── .env              # For API keys
├── script.js         # Frontend logic (recording, API calls)
├── main.py           # FastAPI backend server
├── requirements.txt  # Python dependencies
└── README.md         # Project documentation

## 🚀 Getting Started:

### 1.Install Dependencies
'pip install -r requirements.txt'

### 2.Set Environment Variables
Create a .env file in the root directory and add:
- MURF_API_KEY=your_murf_api_key
- ASSEMBLYAI_API_KEY=your_assemblyai_api_key
-  GEMINI_API_KEY=your_gemini_api_key

### 3.Run the Backend
uvicorn main:app --reload

### 4.Open the Frontend
Open index.html in your browser or use Live Server.

## 📌 How it Works  

1. **🎙 Start Speaking** → Click the **Start** button to begin recording your voice.  
2. **⚙ Processing** → The voice data is sent to the AI backend for transcription and analysis.  
3. **💬 Response Generation** → AI processes the transcript and generates an appropriate reply.  
4. **🔊 Playback** → The reply is converted to speech and played back to the user.  
5. **❗ Error Handling** → If no voice is detected or there’s a network issue, an error message appears.  





