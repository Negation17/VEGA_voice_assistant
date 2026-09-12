from fastapi import FastAPI, UploadFile, File, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.schemas import HomeResponse, AskResponse, SpeakResponse, TranscribeResponse, ChatResponse
from app.services.llm import llm_service
from app.services.stt import stt_service
from app.services.tts import tts_service

app = FastAPI(
    title="FastAPI",
    version=settings.VERSION,
    description="VEGA AI Voice Assistant API - Voice, Text, and PCM Multimodal Backend"
)

# Enable CORS for cross-origin browser clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get(
    "/",
    response_model=HomeResponse,
    summary="Home",
    operation_id="home__get"
)
async def home():
    """Root endpoint returning API status."""
    return {"message": "VEGA API is running!"}

@app.post(
    "/ask",
    response_model=AskResponse,
    summary="Ask",
    operation_id="ask_ask_post"
)
async def ask(question: str = Query(..., title="Question", description="User question")):
    """Ask VEGA a text question and receive an LLM response."""
    answer = await llm_service.generate_answer(question)
    return {"question": question, "answer": answer}

@app.post(
    "/speak",
    response_model=SpeakResponse,
    summary="Speak",
    operation_id="speak_speak_post"
)
async def speak(text: str = Query(..., title="Text", description="Text to synthesize to speech")):
    """Synthesize speech from input text."""
    await tts_service.speak(text)
    return {"message": "VEGA finished speaking", "text": text}

@app.post(
    "/transcribe",
    response_model=TranscribeResponse,
    summary="Transcribe",
    operation_id="transcribe_transcribe_post"
)
async def transcribe(file: UploadFile = File(..., title="File", description="Audio file to transcribe")):
    """Transcribe an uploaded audio file (WAV, MP3, OGG, etc.) to text."""
    content = await file.read()
    text = await stt_service.transcribe_audio_bytes(content, filename=file.filename or "audio.wav")
    return {"text": text}

@app.post(
    "/chat",
    response_model=ChatResponse,
    summary="Chat",
    operation_id="chat_chat_post"
)
async def chat(file: UploadFile = File(..., title="File", description="Audio recording of user query")):
    """End-to-end voice chat: transcribe speech, query LLM, and trigger speech output."""
    audio_bytes = await file.read()
    question = await stt_service.transcribe_audio_bytes(audio_bytes, filename=file.filename or "audio.wav")

    if not question:
        return {
            "question": "",
            "answer": "",
            "message": "No speech detected"
        }

    answer = await llm_service.generate_answer(question)
    await tts_service.speak(answer)
    return {"question": question, "answer": answer}

@app.post(
    "/chat_pcm",
    response_model=ChatResponse,
    summary="Chat Pcm",
    operation_id="chat_pcm_chat_pcm_post"
)
async def chat_pcm(request: Request):
    """Stream raw PCM audio bytes (16kHz, 16-bit mono) from microcontrollers or edge clients."""
    pcm_bytes = await request.body()

    if not pcm_bytes or stt_service.is_silence_pcm(pcm_bytes):
        return {
            "question": "",
            "answer": "",
            "message": "No speech detected from PCM audio"
        }

    question = await stt_service.transcribe_pcm(pcm_bytes)

    if not question:
        return {
            "question": "",
            "answer": "",
            "message": "No speech detected from PCM audio"
        }

    answer = await llm_service.generate_answer(question)
    await tts_service.speak(answer)
    return {"question": question, "answer": answer}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
