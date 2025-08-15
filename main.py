from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import tempfile
import time
import requests
from dotenv import load_dotenv

# Import Google GenAI SDK
from google import genai
from google.genai.types import GenerateContentConfig, Tool, ToolCodeExecution

load_dotenv()

ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
MURF_API_KEY = os.getenv("MURF_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise Exception("GEMINI_API_KEY not set in environment variables.")

# Initialize Gemini client
client = genai.Client(api_key=GEMINI_API_KEY)

app = FastAPI()

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------
# Day 1–7 Endpoint
# --------------------------
@app.post("/process-to-murf")
async def process_audio(file: UploadFile = File(...)):
    try:
        print("⏺️ Received audio file")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
        print(f"✅ Temp audio saved: {tmp_path}")

        # Upload to AssemblyAI
        with open(tmp_path, "rb") as f:
            upload_res = requests.post(
                "https://api.assemblyai.com/v2/upload",
                headers={"authorization": ASSEMBLYAI_API_KEY},
                data=f
            )
        print("📤 AssemblyAI Upload:", upload_res.status_code, upload_res.text)
        if upload_res.status_code != 200:
            return JSONResponse({"error": "AssemblyAI upload failed"}, status_code=500)

        audio_url = upload_res.json().get("upload_url")
        if not audio_url:
            return JSONResponse({"error": "Upload URL missing"}, status_code=500)

        # Transcription request
        transcribe_res = requests.post(
            "https://api.assemblyai.com/v2/transcript",
            headers={
                "authorization": ASSEMBLYAI_API_KEY,
                "content-type": "application/json"
            },
            json={"audio_url": audio_url}
        )
        print("📝 Transcript Request:", transcribe_res.status_code, transcribe_res.text)
        if transcribe_res.status_code != 200:
            return JSONResponse({"error": "Transcription request failed"}, status_code=500)

        transcript_id = transcribe_res.json()["id"]
        print(f"🧾 Transcript ID: {transcript_id}")

        # Poll until transcription complete
        while True:
            status_res = requests.get(
                f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
                headers={"authorization": ASSEMBLYAI_API_KEY}
            ).json()
            status = status_res.get("status")
            print(f"⏳ AssemblyAI Status: {status}")
            if status == "completed":
                text_result = status_res["text"]
                print("✅ Transcription:", text_result)
                break
            elif status == "error":
                return JSONResponse({"error": "Transcription failed"}, status_code=500)
            time.sleep(3)

        # Send transcript to Murf for TTS
        murf_url = "https://api.murf.ai/v1/speech/generate"
        murf_headers = {
            "api-key": MURF_API_KEY,
            "Content-Type": "application/json"
        }
        murf_payload = {
            "voiceId": "en-US-natalie",
            "text": text_result
        }

        murf_res = requests.post(murf_url, headers=murf_headers, json=murf_payload)
        print("🗣️ Murf Response:", murf_res.status_code, murf_res.text)
        if murf_res.status_code != 200:
            return JSONResponse({"error": "Murf AI TTS failed"}, status_code=500)

        murf_audio_url = murf_res.json().get("audioFile") or murf_res.json().get("url")
        if not murf_audio_url:
            return JSONResponse({"error": "Murf did not return audio URL"}, status_code=500)

        print("🔊 Murf Audio URL:", murf_audio_url)
        return {
            "murf_audio_url": murf_audio_url,
            "transcript": text_result
        }

    except Exception as e:
        print("❌ Exception:", str(e))
        return JSONResponse({"error": str(e)}, status_code=500)


# --------------------------
# Day 8 Endpoint
# --------------------------
class PromptRequest(BaseModel):
    text: str

@app.post("/llm/query")
async def llm_query(request: PromptRequest):
    prompt = request.text
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=GenerateContentConfig(
                tools=[Tool(code_execution=ToolCodeExecution())]
            )
        )
        return {"response": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calling Gemini API: {e}")


# --------------------------
# Day 9 Endpoint: Full Pipeline
# --------------------------
@app.post("/llm/full_pipeline")
async def llm_full_pipeline(file: UploadFile = File(...)):
    try:
        print("🎤 Day 9: Received audio for full pipeline")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        with open(tmp_path, "rb") as f:
            upload_res = requests.post(
                "https://api.assemblyai.com/v2/upload",
                headers={"authorization": ASSEMBLYAI_API_KEY},
                data=f
            )
        if upload_res.status_code != 200:
            return JSONResponse({"error": "AssemblyAI upload failed"}, status_code=500)
        audio_url = upload_res.json().get("upload_url")

        transcribe_res = requests.post(
            "https://api.assemblyai.com/v2/transcript",
            headers={
                "authorization": ASSEMBLYAI_API_KEY,
                "content-type": "application/json"
            },
            json={"audio_url": audio_url}
        )
        if transcribe_res.status_code != 200:
            return JSONResponse({"error": "Transcription request failed"}, status_code=500)
        transcript_id = transcribe_res.json()["id"]

        while True:
            status_res = requests.get(
                f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
                headers={"authorization": ASSEMBLYAI_API_KEY}
            ).json()
            status = status_res.get("status")
            if status == "completed":
                user_text = status_res["text"]
                break
            elif status == "error":
                return JSONResponse({"error": "Transcription failed"}, status_code=500)
            time.sleep(3)

        print(f"📝 Transcript: {user_text}")

        try:
            llm_res = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_text,
                config=GenerateContentConfig(
                    tools=[Tool(code_execution=ToolCodeExecution())]
                )
            )
            llm_reply = llm_res.text
        except Exception as e:
            return JSONResponse({"error": f"Gemini API error: {e}"}, status_code=500)

        print(f"🤖 Gemini Reply: {llm_reply}")

        murf_url = "https://api.murf.ai/v1/speech/generate"
        murf_headers = {
            "api-key": MURF_API_KEY,
            "Content-Type": "application/json"
        }
        murf_payload = {
            "voiceId": "en-US-natalie",
            "text": llm_reply
        }
        murf_res = requests.post(murf_url, headers=murf_headers, json=murf_payload)
        if murf_res.status_code != 200:
            return JSONResponse({"error": "Murf AI TTS failed"}, status_code=500)

        murf_audio_url = murf_res.json().get("audioFile") or murf_res.json().get("url")
        if not murf_audio_url:
            return JSONResponse({"error": "No audio URL from Murf"}, status_code=500)

        print("🔊 Murf Audio URL:", murf_audio_url)

        return {
            "transcript": user_text,
            "llm_reply": llm_reply,
            "murf_audio_url": murf_audio_url
        }

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# --------------------------
# Day 10 Endpoint: Chat History
# --------------------------
chat_history_store = {}

@app.post("/agent/chat/{session_id}")
async def chat_with_history(session_id: str, file: UploadFile = File(...)):
    try:
        print(f"🎤 Day 10: Received audio for session {session_id}")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        with open(tmp_path, "rb") as f:
            upload_res = requests.post(
                "https://api.assemblyai.com/v2/upload",
                headers={"authorization": ASSEMBLYAI_API_KEY},
                data=f
            )
        if upload_res.status_code != 200:
            return JSONResponse({"error": "AssemblyAI upload failed"}, status_code=500)
        audio_url = upload_res.json().get("upload_url")

        transcribe_res = requests.post(
            "https://api.assemblyai.com/v2/transcript",
            headers={
                "authorization": ASSEMBLYAI_API_KEY,
                "content-type": "application/json"
            },
            json={"audio_url": audio_url}
        )
        if transcribe_res.status_code != 200:
            return JSONResponse({"error": "Transcription request failed"}, status_code=500)
        transcript_id = transcribe_res.json()["id"]

        while True:
            status_res = requests.get(
                f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
                headers={"authorization": ASSEMBLYAI_API_KEY}
            ).json()
            status = status_res.get("status")
            if status == "completed":
                user_text = status_res["text"]
                break
            elif status == "error":
                return JSONResponse({"error": "Transcription failed"}, status_code=500)
            time.sleep(3)

        print(f"📝 Transcript for session {session_id}: {user_text}")

        if session_id not in chat_history_store:
            chat_history_store[session_id] = []
        chat_history_store[session_id].append({"role": "user", "content": user_text})

        conversation_text = ""
        for msg in chat_history_store[session_id]:
            conversation_text += f"{msg['role'].capitalize()}: {msg['content']}\n"

        try:
            llm_res = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=conversation_text,
                config=GenerateContentConfig(
                    tools=[Tool(code_execution=ToolCodeExecution())]
                )
            )
            llm_reply = llm_res.text
        except Exception as e:
            return JSONResponse({"error": f"Gemini API error: {e}"}, status_code=500)

        print(f"🤖 Gemini Reply for session {session_id}: {llm_reply}")

        chat_history_store[session_id].append({"role": "assistant", "content": llm_reply})

        murf_url = "https://api.murf.ai/v1/speech/generate"
        murf_headers = {
            "api-key": MURF_API_KEY,
            "Content-Type": "application/json"
        }
        murf_payload = {
            "voiceId": "en-US-natalie",
            "text": llm_reply
        }
        murf_res = requests.post(murf_url, headers=murf_headers, json=murf_payload)
        if murf_res.status_code != 200:
            return JSONResponse({"error": "Murf AI TTS failed"}, status_code=500)

        murf_audio_url = murf_res.json().get("audioFile") or murf_res.json().get("url")
        if not murf_audio_url:
            return JSONResponse({"error": "No audio URL from Murf"}, status_code=500)

        print(f"🔊 Murf Audio URL for session {session_id}: {murf_audio_url}")

        return {
            "session_id": session_id,
            "transcript": user_text,
            "llm_reply": llm_reply,
            "murf_audio_url": murf_audio_url,
            "chat_history": chat_history_store[session_id]
        }

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
