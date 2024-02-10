from datetime import datetime

from pydantic import BaseModel


class Audio(BaseModel):
    id: int
    create_date: datetime
    original_audio_path: str
    original_text: str
    processed_audio_path: str
    processed_text: str
    onset: float
    offset: float