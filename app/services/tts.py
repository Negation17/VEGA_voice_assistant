import io
import logging
from typing import Optional
import edge_tts
from openai import OpenAI
from app.config import settings

logger = logging.getLogger("vega.tts")

class TTSService:
    """Text-to-speech synthesis service with multiple backend options."""

    def __init__(self):
        self.engine = settings.TTS_ENGINE
        self.voice = settings.TTS_VOICE
        self._openai_client = None

    @property
    def openai_client(self) -> Optional[OpenAI]:
        if self._openai_client is None and settings.OPENAI_API_KEY:
            self._openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        return self._openai_client

    async def synthesize(self, text: str) -> bytes:
        """Synthesize text to MP3/WAV audio bytes."""
        if not text or not text.strip():
            return b""

        if self.engine == "edge-tts":
            try:
                communicate = edge_tts.Communicate(text, self.voice)
                audio_stream = io.BytesIO()
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        audio_stream.write(chunk["data"])
                return audio_stream.getvalue()
            except Exception as e:
                logger.error(f"Edge-TTS synthesis error: {e}")

        elif self.engine == "openai" and self.openai_client:
            try:
                response = self.openai_client.audio.speech.create(
                    model="tts-1",
                    voice="alloy",
                    input=text
                )
                return response.read()
            except Exception as e:
                logger.error(f"OpenAI TTS synthesis error: {e}")

        logger.info(f"TTS simulated for: {text[:50]}...")
        return b""

    async def speak(self, text: str) -> bool:
        """Synthesize speech and trigger delivery / playback."""
        audio = await self.synthesize(text)
        logger.info(f"VEGA synthesized {len(audio)} bytes of speech for text: {text}")
        return True

tts_service = TTSService()
