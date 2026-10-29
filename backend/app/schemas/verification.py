from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class VerifyRequest(BaseModel):
    voter_id: str = Field(..., description="UUID of the voter to verify")
    fingerprint_scan: str = Field(..., description="Base64 encoded live fingerprint scan")
    workstation_id: Optional[str] = Field("booth-01", description="Identifier of the voting kiosk")


class VerifyResponse(BaseModel):
    allowed: bool
    result: str  # "SUCCESS", "DUPLICATE_ATTEMPT", "BIOMETRIC_MISMATCH", "LOCKED_OUT", "NOT_FOUND"
    reason: str
    vote_token: Optional[str] = None
    expires_in_seconds: Optional[int] = None


class VerificationLogItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    log_id: str
    voter_id: Optional[str] = None
    attempted_at: str
    result: str
    reason: str
    workstation_id: Optional[str] = "booth-01"


class PaginatedLogsResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[VerificationLogItem]
