import io
import math
import wave
import struct
import logging
from typing import Optional
from openai import OpenAI
from app.config import settings

logger = logging.getLogger("vega.stt")

class STTService:
    """Speech-to-text service handling WAV, MP3, and raw PCM audio streams."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self._client = None

    @property
    def client(self) -> Optional[OpenAI]:
        if self._client is None and self.api_key:
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def is_silence_pcm(self, pcm_bytes: bytes, threshold: float = None) -> bool:
        """Calculate root mean square (RMS) energy to detect silence in 16-bit PCM audio."""
        if not pcm_bytes or len(pcm_bytes) < 2:
            return True

        if threshold is None:
            threshold = settings.SILENCE_THRESHOLD_RMS

        count = len(pcm_bytes) // 2
        format_str = f"<{count}h"
        try:
            samples = struct.unpack(format_str, pcm_bytes[:count * 2])
            sum_squares = sum(s * s for s in samples)
            rms = math.sqrt(sum_squares / count)
            return rms < threshold
        except Exception as e:
            logger.warning(f"Error analyzing PCM RMS: {e}")
            return False

    def pcm_to_wav(self, pcm_bytes: bytes, sample_rate: int = None, channels: int = None, sampwidth: int = None) -> bytes:
        """Encapsulate raw PCM frames into a standard RIFF/WAV container."""
        sample_rate = sample_rate or settings.PCM_SAMPLE_RATE
        channels = channels or settings.PCM_CHANNELS
        sampwidth = sampwidth or settings.PCM_SAMPLE_WIDTH

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sampwidth)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm_bytes)
        return buf.getvalue()

    async def transcribe_audio_bytes(self, audio_bytes: bytes, filename: str = "audio.wav") -> str:
        """Transcribe audio bytes using Whisper API or mock engine."""
        if not audio_bytes:
            return ""

        if settings.STT_ENGINE == "mock" or not self.client:
            logger.info("Using mock STT transcription or missing API key.")
            return ""

        try:
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = filename

            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            return (transcript.text or "").strip()
        except Exception as e:
            logger.error(f"Whisper transcription error: {e}")
            return ""

    async def transcribe_pcm(self, pcm_bytes: bytes) -> str:
        """Transcribe raw PCM audio bytes with silence pre-filtering."""
        if not pcm_bytes or self.is_silence_pcm(pcm_bytes):
            return ""

        wav_bytes = self.pcm_to_wav(pcm_bytes)
        return await self.transcribe_audio_bytes(wav_bytes, filename="stream.wav")

stt_service = STTService()
