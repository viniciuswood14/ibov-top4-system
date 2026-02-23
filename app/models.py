from typing import Optional
from datetime import date, datetime
from sqlmodel import SQLModel, Field, Column, JSON

class Snapshot(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    as_of: date = Field(index=True)
    universe_size: int
    ranking: dict = Field(sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)
