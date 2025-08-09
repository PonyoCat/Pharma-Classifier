# backend/app/schemas.py
from typing import List, Literal, Optional
from pydantic import BaseModel, Field

Sentiment = Literal["POSITIVE", "NEGATIVE", "NEUTRAL", "MIXED", "UNKNOWN"]

class AnalyzeIn(BaseModel):
    text: str = Field(min_length=1, max_length=4000)

class Entity(BaseModel):
    value: str
    type: str = "OTHER"        # e.g. DRUG, DOSAGE, SYMPTOM
    start_index: Optional[int] = None
    end_index: Optional[int] = None

class ReportOut(BaseModel):
    id: str
    userId: str
    createdAt: int             # epoch seconds
    text: str
    labels: List[str] = []
    entities: List[Entity] = []
    score: float = 0.0
    sentiment: Sentiment = "UNKNOWN"
    summary: str = ""
    source: str = "manual"

class ReportsList(BaseModel):
    items: List[ReportOut]
    nextToken: Optional[str] = None  # if you add DynamoDB pagination later
