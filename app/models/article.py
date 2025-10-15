from sqlmodel import SQLModel, Field
from typing import Optional, List
from datetime import datetime
import json

class Article(SQLModel, table=True):
    id: str = Field(primary_key=True)
    title: str
    description: Optional[str] = None
    url: Optional[str] = None
    publication_date: Optional[datetime] = Field(default=None)
    source_name: Optional[str] = None
    category_json: Optional[str] = None
    relevance_score: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    @property
    def categories(self) -> List[str]:
        try:
            return json.loads(self.category_json or "[]")
        except Exception:
            return []

    @categories.setter
    def categories(self, v: List[str]):
        self.category_json = json.dumps(v or [])
