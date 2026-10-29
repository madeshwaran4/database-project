from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class CandidateCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    party: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class CandidateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    party: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class CandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    candidate_id: str
    name: str
    party: str
    description: Optional[str] = None


class CandidateVoteResult(BaseModel):
    candidate_id: str
    name: str
    party: str
    vote_count: int
    percentage: float


class ElectionResultsResponse(BaseModel):
    total_votes: int
    polling_status: str
    results: List[CandidateVoteResult]
