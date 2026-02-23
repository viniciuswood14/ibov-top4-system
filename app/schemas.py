from __future__ import annotations
from typing import List
from pydantic import BaseModel, Field

class Position(BaseModel):
    ticker: str
    quantity: float
    avg_price: float
    last_price: float

class PortfolioInput(BaseModel):
    cash_brl: float = 0.0
    positions: List[Position] = Field(default_factory=list)

class RecommendationItem(BaseModel):
    ticker: str
    action: str
    target_value: float
    current_value: float
    diff_value: float
    est_qty: float

class RecommendationsResponse(BaseModel):
    as_of: str
    top4: List[str]
    orders: List[RecommendationItem]
    notes: List[str]
