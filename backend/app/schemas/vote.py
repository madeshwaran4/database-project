from pydantic import BaseModel, Field


class VoteCastRequest(BaseModel):
    candidate_id: str = Field(..., description="UUID of the selected candidate")
    vote_token: str = Field(..., description="Single-use vote token issued by /api/verify")


class VoteCastResponse(BaseModel):
    success: bool
    message: str
    vote_id: str
    vote_date: str  # Note: Date only, no time, adhering to Rule 1!
