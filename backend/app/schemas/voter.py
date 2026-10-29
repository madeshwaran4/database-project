from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class VoterEnrollRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Full name of the voter")
    id_type: str = Field(..., min_length=2, max_length=50, description="Type of ID (e.g. National ID, Passport)")
    id_number: str = Field(..., min_length=4, max_length=100, description="Full government ID number")
    fingerprint_image: str = Field(..., description="Base64 encoded fingerprint image or minutiae sample")


class VoterEnrollResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    voter_id: str
    name: str
    id_type: str
    id_last4: str
    has_voted: str
    enrolled_at: str


class VoterSearchItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    voter_id: str
    name: str
    id_type: str
    id_last4: str
    has_voted: str
    enrolled_at: str
