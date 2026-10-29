from pydantic import BaseModel


class PollingStatusResponse(BaseModel):
    polling_status: str  # "open" or "closed"
    is_open: bool
    updated_at: str


class ElectionStatsResponse(BaseModel):
    enrolled_voters: int
    votes_cast: int
    denied_attempts: int
    turnout_percentage: float
    polling_status: str
