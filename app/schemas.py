from typing import Optional
from pydantic import BaseModel, Field

class HomeResponse(BaseModel):
    message: str = Field(default="VEGA API is running!", description="Service status message")

class AskResponse(BaseModel):
    question: str = Field(..., description="User question submitted to VEGA")
    answer: str = Field(..., description="LLM generated answer")

class SpeakResponse(BaseModel):
    message: str = Field(default="VEGA finished speaking", description="Status message")
    text: str = Field(..., description="Text synthesized by TTS")

class TranscribeResponse(BaseModel):
    text: str = Field(..., description="Transcribed text from speech")

class ChatResponse(BaseModel):
    question: str = Field(..., description="Transcribed user question")
    answer: str = Field(..., description="AI generated answer")
    message: Optional[str] = Field(None, description="Optional diagnostic or status message")
