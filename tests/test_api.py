import io
import wave
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app

client = TestClient(app)

def create_mock_wav(duration_sec: float = 0.5, sample_rate: int = 16000) -> bytes:
    """Helper to generate a valid in-memory WAV file."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"\x00\x00" * int(sample_rate * duration_sec))
    return buf.getvalue()

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "VEGA API is running!"}

def test_ask_endpoint():
    with patch("app.main.llm_service.generate_answer", new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = "The capital of France is Paris."
        response = client.post("/ask", params={"question": "What is the capital of France?"})
        assert response.status_code == 200
        data = response.json()
        assert data["question"] == "What is the capital of France?"
        assert data["answer"] == "The capital of France is Paris."

def test_speak_endpoint():
    with patch("app.main.tts_service.speak", new_callable=AsyncMock) as mock_speak:
        mock_speak.return_value = True
        response = client.post("/speak", params={"text": "Hello world"})
        assert response.status_code == 200
        assert response.json() == {"message": "VEGA finished speaking", "text": "Hello world"}
        mock_speak.assert_called_once_with("Hello world")

def test_transcribe_endpoint_empty():
    wav_bytes = create_mock_wav()
    response = client.post(
        "/transcribe",
        files={"file": ("silence.wav", wav_bytes, "audio/wav")}
    )
    assert response.status_code == 200
    assert response.json() == {"text": ""}

def test_transcribe_endpoint_with_text():
    wav_bytes = create_mock_wav()
    with patch("app.main.stt_service.transcribe_audio_bytes", new_callable=AsyncMock) as mock_stt:
        mock_stt.return_value = "Hello assistant"
        response = client.post(
            "/transcribe",
            files={"file": ("audio.wav", wav_bytes, "audio/wav")}
        )
        assert response.status_code == 200
        assert response.json() == {"text": "Hello assistant"}

def test_chat_silence():
    wav_bytes = create_mock_wav()
    response = client.post(
        "/chat",
        files={"file": ("silence.wav", wav_bytes, "audio/wav")}
    )
    assert response.status_code == 200
    assert response.json() == {
        "question": "",
        "answer": "",
        "message": "No speech detected"
    }

def test_chat_with_speech():
    wav_bytes = create_mock_wav()
    with patch("app.main.stt_service.transcribe_audio_bytes", new_callable=AsyncMock) as mock_stt, \
         patch("app.main.llm_service.generate_answer", new_callable=AsyncMock) as mock_llm, \
         patch("app.main.tts_service.speak", new_callable=AsyncMock) as mock_speak:

        mock_stt.return_value = "How is the weather today?"
        mock_llm.return_value = "It is sunny and 22 degrees."
        mock_speak.return_value = True

        response = client.post(
            "/chat",
            files={"file": ("speech.wav", wav_bytes, "audio/wav")}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["question"] == "How is the weather today?"
        assert data["answer"] == "It is sunny and 22 degrees."
        mock_speak.assert_called_once_with("It is sunny and 22 degrees.")

def test_chat_pcm_silence():
    silence_pcm = b"\x00\x00" * 16000
    response = client.post(
        "/chat_pcm",
        content=silence_pcm,
        headers={"Content-Type": "application/octet-stream"}
    )
    assert response.status_code == 200
    assert response.json() == {
        "question": "",
        "answer": "",
        "message": "No speech detected from PCM audio"
    }

def test_chat_pcm_with_speech():
    dummy_pcm = b"\x50\x20" * 8000
    with patch("app.main.stt_service.transcribe_pcm", new_callable=AsyncMock) as mock_stt, \
         patch("app.main.llm_service.generate_answer", new_callable=AsyncMock) as mock_llm, \
         patch("app.main.tts_service.speak", new_callable=AsyncMock) as mock_speak:

        mock_stt.return_value = "Turn on the lights"
        mock_llm.return_value = "Lights are now turned on."
        mock_speak.return_value = True

        response = client.post(
            "/chat_pcm",
            content=dummy_pcm,
            headers={"Content-Type": "application/octet-stream"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["question"] == "Turn on the lights"
        assert data["answer"] == "Lights are now turned on."
