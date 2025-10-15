# app/models/user_event.py
from sqlmodel import SQLModel, Field
from datetime import datetime
import uuid

class UserEvent(SQLModel, table=True):
    """
    Stores user interaction events for computing trending news.
    Each record represents a single interaction (view, click, share).
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    article_id: str = Field(index=True)
    user_id: str = Field(index=True)
    event_type: str = Field(index=True)  # e.g., "view", "click", "share"
    latitude: float = Field()
    longitude: float = Field()
    timestamp: datetime = Field(default_factory=datetime.utcnow)
