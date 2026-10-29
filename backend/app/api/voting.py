import base64
import uuid
from datetime import datetime, timezone, date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import settings
from app.core.security import (
    create_vote_token,
    decode_and_verify_vote_token,
    require_operator,
)
from app.db.session import get_db
from app.fingerprint import get_fingerprint_provider, biometric_cipher
from app.schemas.verification import VerifyRequest, VerifyResponse
from app.schemas.vote import VoteCastRequest, VoteCastResponse

router = APIRouter(prefix="/api", tags=["Verification and Voting"])


def _log_verification(cursor, voter_id: Optional[str], result: str, reason: str, workstation_id: str):
    """Log every verification attempt to VERIFICATION_LOG (AGENTS.md Rule 6)."""
    log_id = str(uuid.uuid4())
    cursor.execute(
        """
        INSERT INTO VERIFICATION_LOG (log_id, voter_id, attempted_at, result, reason, workstation_id)
        VALUES (:1, :2, CURRENT_TIMESTAMP, :3, :4, :5)
        """,
        (log_id, voter_id, result, reason, workstation_id),
    )


@router.post(
    "/verify",
    response_model=VerifyResponse,
    summary="Biometric 1:1 voter verification at the booth",
)
def verify_voter_biometrics(
    req: VerifyRequest,
    current_user: dict = Depends(require_operator),
    db=Depends(get_db),
) -> VerifyResponse:
    cursor = db.cursor()
    workstation_id = req.workstation_id or "booth-01"

    # 1. Check if polling is open
    cursor.execute("SELECT state_value FROM ELECTION_STATE WHERE state_key = :1", ("polling_status",))
    state_row = cursor.fetchone()
    if not state_row or state_row["state_value"].lower() != "open":
        _log_verification(cursor, req.voter_id, "POLLING_CLOSED", "Polling is currently closed.", workstation_id)
        return VerifyResponse(
            allowed=False,
            result="POLLING_CLOSED",
            reason="Polling is currently closed. Ballot casting is not active.",
        )

    # 2. Check for active lockout on voter_id
    cursor.execute(
        "SELECT failed_count, locked_until FROM VERIFICATION_LOCKOUT WHERE voter_id = :1",
        (req.voter_id,),
    )
    lockout_row = cursor.fetchone()
    if lockout_row:
        locked_until_val = lockout_row["locked_until"]
        if locked_until_val:
            try:
                if isinstance(locked_until_val, str):
                    locked_until = datetime.fromisoformat(locked_until_val)
                else:
                    locked_until = locked_until_val
                if locked_until.tzinfo is None:
                    locked_until = locked_until.replace(tzinfo=timezone.utc)
                if datetime.now(timezone.utc) < locked_until:
                    _log_verification(
                        cursor, req.voter_id, "LOCKED_OUT", "Voter account is temporarily locked.", workstation_id
                    )
                    return VerifyResponse(
                        allowed=False,
                        result="LOCKED_OUT",
                        reason=f"Verification locked due to too many failed attempts until {locked_until_val}.",
                    )
            except Exception:
                pass

    # 3. Load voter record
    cursor.execute(
        "SELECT voter_id, name, fingerprint_template, has_voted FROM VOTER WHERE voter_id = :1",
        (req.voter_id,),
    )
    voter = cursor.fetchone()
    if not voter:
        _log_verification(cursor, req.voter_id, "NOT_FOUND", "Voter record does not exist.", workstation_id)
        return VerifyResponse(
            allowed=False,
            result="NOT_FOUND",
            reason="Voter registration not found in registry.",
        )

    has_voted = voter["has_voted"]
    if has_voted == "Y":
        _log_verification(
            cursor, req.voter_id, "DUPLICATE_ATTEMPT", "Voter has already cast a ballot.", workstation_id
        )
        return VerifyResponse(
            allowed=False,
            result="DUPLICATE_ATTEMPT",
            reason="Duplicate attempt: Voter has already cast a ballot in this election.",
        )

    # 4. Sensor Bypass Mode (When physical sensor hardware is absent or mock provider active)
    is_bypass = (
        req.fingerprint_scan in ("BYPASS", "SKIP", "NO_HARDWARE", "SIMULATE")
        or settings.FINGERPRINT_PROVIDER == "mock"
    )

    if is_bypass:
        if lockout_row:
            cursor.execute("DELETE FROM VERIFICATION_LOCKOUT WHERE voter_id = :1", (req.voter_id,))

        vote_token = create_vote_token(req.voter_id)
        _log_verification(
            cursor, req.voter_id, "SUCCESS", "Biometric verification successful (Hardware Sensor Bypassed).", workstation_id
        )
        return VerifyResponse(
            allowed=True,
            result="SUCCESS",
            reason="Biometric verification bypassed (No Hardware Sensor Required). Proceed to ballot.",
            vote_token=vote_token,
            expires_in_seconds=settings.VOTE_TOKEN_EXPIRE_MINUTES * 60,
        )

    enc_template = voter["fingerprint_template"]
    if hasattr(enc_template, "read"):
        enc_template = enc_template.read()
    try:
        stored_template = biometric_cipher.decrypt_template(enc_template)
    except Exception:
        _log_verification(
            cursor, req.voter_id, "SYSTEM_ERROR", "Failed to decrypt stored template.", workstation_id
        )
        return VerifyResponse(
            allowed=False,
            result="SYSTEM_ERROR",
            reason="Internal cryptographic error reading voter template.",
        )

    try:
        raw_scan_bytes = base64.b64decode(req.fingerprint_scan)
    except Exception:
        raw_scan_bytes = req.fingerprint_scan.encode("utf-8")

    provider = get_fingerprint_provider()
    try:
        scan_template = provider.extract_template(raw_scan_bytes)
        is_match, score = provider.match(stored_template, scan_template)
    except Exception as e:
        _log_verification(cursor, req.voter_id, "EXTRACTION_ERROR", str(e), workstation_id)
        return VerifyResponse(
            allowed=False,
            result="EXTRACTION_ERROR",
            reason=f"Biometric scan quality insufficient: {str(e)}",
        )

    # 5. Handle mismatch and lockout tracking
    if not is_match:
        failed_count = lockout_row["failed_count"] if lockout_row else 0
        new_failed_count = failed_count + 1
        locked_until_val = None

        if new_failed_count >= settings.MAX_FAILED_VERIFICATIONS:
            locked_until_val = datetime.now(timezone.utc) + timedelta(minutes=settings.LOCKOUT_DURATION_MINUTES)
            result_code = "LOCKED_OUT"
            reason_msg = f"Biometric mismatch. Account locked for {settings.LOCKOUT_DURATION_MINUTES} minutes."
        else:
            result_code = "BIOMETRIC_MISMATCH"
            reason_msg = f"Biometric mismatch (Attempt {new_failed_count} of {settings.MAX_FAILED_VERIFICATIONS})."

        # Update or insert lockout record
        if lockout_row:
            cursor.execute(
                "UPDATE VERIFICATION_LOCKOUT SET failed_count = :1, locked_until = :2, last_failed_at = CURRENT_TIMESTAMP WHERE voter_id = :3",
                (new_failed_count, locked_until_val, req.voter_id),
            )
        else:
            cursor.execute(
                "INSERT INTO VERIFICATION_LOCKOUT (voter_id, failed_count, locked_until, last_failed_at) VALUES (:1, :2, :3, CURRENT_TIMESTAMP)",
                (req.voter_id, new_failed_count, locked_until_val),
            )

        _log_verification(cursor, req.voter_id, result_code, reason_msg, workstation_id)
        return VerifyResponse(allowed=False, result=result_code, reason=reason_msg)

    # 6. Success: Clear any previous failed attempts
    if lockout_row:
        cursor.execute("DELETE FROM VERIFICATION_LOCKOUT WHERE voter_id = :1", (req.voter_id,))

    # Issue single-use short-lived vote token
    vote_token = create_vote_token(req.voter_id)
    _log_verification(cursor, req.voter_id, "SUCCESS", "Biometric verification successful.", workstation_id)

    return VerifyResponse(
        allowed=True,
        result="SUCCESS",
        reason="Biometric identity verified successfully. Proceed to ballot kiosk.",
        vote_token=vote_token,
        expires_in_seconds=settings.VOTE_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post(
    "/vote",
    response_model=VoteCastResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cast anonymous ballot in atomic transaction (AGENTS.md Rules 1, 2, 3)",
)
def cast_vote(
    req: VoteCastRequest,
    db=Depends(get_db),
) -> VoteCastResponse:
    # 1. Decode & verify vote token
    token_payload = decode_and_verify_vote_token(req.vote_token)
    token_jti = token_payload["jti"]
    voter_id = token_payload["sub"]

    cursor = db.cursor()

    # 2. Check if vote token was already consumed (Replay prevention)
    cursor.execute("SELECT token_jti FROM CONSUMED_VOTE_TOKENS WHERE token_jti = :1", (token_jti,))
    if cursor.fetchone():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Vote token has already been consumed. Duplicate submission prohibited.",
        )

    # 3. Check election state (polling must be open)
    cursor.execute("SELECT state_value FROM ELECTION_STATE WHERE state_key = :1", ("polling_status",))
    state_row = cursor.fetchone()
    if not state_row or state_row["state_value"].lower() != "open":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ballot submission rejected: Polling is closed.",
        )

    # 4. Verify candidate exists
    cursor.execute("SELECT candidate_id FROM CANDIDATE WHERE candidate_id = :1", (req.candidate_id,))
    if not cursor.fetchone():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Selected candidate does not exist.",
        )

    # 5. ATOMIC STATUS FLIP AND VOTE INSERTION (AGENTS.md Rule 3)
    # The status flip and vote insert MUST occur in the exact same transaction.
    # If updated rows != 1, rollback and abort to eliminate double voting race conditions.
    cursor.execute(
        """
        UPDATE VOTER
        SET has_voted = 'Y', voted_at = CURRENT_TIMESTAMP
        WHERE voter_id = :1 AND has_voted = 'N'
        """,
        (voter_id,),
    )

    if cursor.rowcount != 1:
        # Atomic check failed: voter already voted in a concurrent race condition!
        # Explicit rollback
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate vote prevented: Voter has already cast a ballot.",
        )

    # 6. Insert Ballot (AGENTS.md Rules 1 & 2):
    # - vote_id MUST be a random UUIDv4 (Rule 2)
    # - NO link to VOTER: no voter_id, no FK, no fine timestamp, vote_date has ONLY calendar date (YYYY-MM-DD)
    # - Vote token is NOT stored alongside the vote
    vote_id = str(uuid.uuid4())
    calendar_date_only = date.today().isoformat()  # YYYY-MM-DD only

    cursor.execute(
        """
        INSERT INTO VOTE (vote_id, candidate_id, vote_date)
        VALUES (:1, :2, TO_DATE(:3, 'YYYY-MM-DD'))
        """,
        (vote_id, req.candidate_id, calendar_date_only),
    )

    # 7. Invalidate single-use token
    cursor.execute(
        "INSERT INTO CONSUMED_VOTE_TOKENS (token_jti, consumed_at) VALUES (:1, CURRENT_TIMESTAMP)",
        (token_jti,),
    )

    return VoteCastResponse(
        success=True,
        message="Ballot successfully cast and recorded anonymously.",
        vote_id=vote_id,
        vote_date=calendar_date_only,
    )
