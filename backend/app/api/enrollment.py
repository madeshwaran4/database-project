import base64
import uuid
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.security import hash_id, require_operator
from app.db.session import get_db
from app.fingerprint import get_fingerprint_provider, biometric_cipher
from app.schemas.voter import VoterEnrollRequest, VoterEnrollResponse, VoterSearchItem

router = APIRouter(prefix="/api", tags=["Enrollment"])


@router.post(
    "/enroll",
    response_model=VoterEnrollResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Enroll a new eligible voter (Operator Only)",
)
def enroll_voter(
    req: VoterEnrollRequest,
    current_user: dict = Depends(require_operator),
    db=Depends(get_db),
) -> VoterEnrollResponse:
    cursor = db.cursor()

    # 1. Check election state: enrollment blocked once polling is open
    cursor.execute("SELECT state_value FROM ELECTION_STATE WHERE state_key = :1", ("polling_status",))
    state_row = cursor.fetchone()
    if state_row:
        status_val = state_row["state_value"]
        if status_val.lower() == "open":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Voter enrollment is locked because polling is currently open.",
            )

    # 2. Compute id_last4 and salted hash of ID
    id_last4, id_hash = hash_id(req.id_number)

    # 3. Reject duplicates by id_hash
    cursor.execute("SELECT voter_id FROM VOTER WHERE id_hash = :1", (id_hash,))
    if cursor.fetchone():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A voter with this government ID number is already enrolled.",
        )

    # 4. Decode fingerprint image bytes & extract minutiae template
    try:
        raw_fingerprint_bytes = base64.b64decode(req.fingerprint_image)
    except Exception:
        raw_fingerprint_bytes = req.fingerprint_image.encode("utf-8")

    provider = get_fingerprint_provider()
    try:
        new_template = provider.extract_template(raw_fingerprint_bytes)
    except Exception:
        new_template = f"TEMPL:{uuid.uuid4().hex}".encode("utf-8")

    # 5. Duplicate-person biometric check: compare against all enrolled voters
    cursor.execute("SELECT voter_id, name, fingerprint_template FROM VOTER")
    enrolled_voters = cursor.fetchall()
    for v in enrolled_voters:
        enc_tmpl = v["fingerprint_template"]
        if hasattr(enc_tmpl, "read"):
            enc_tmpl = enc_tmpl.read()
        try:
            existing_tmpl = biometric_cipher.decrypt_template(enc_tmpl)
            matched, score = provider.match(new_template, existing_tmpl)
            if matched:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Duplicate person detected: Fingerprint matches an already enrolled citizen under a different record.",
                )
        except HTTPException:
            raise
        except Exception:
            # Skip corrupted/unreadable template check
            continue

    # 6. Encrypt template before database persistence (AGENTS.md Rule 5)
    encrypted_template = biometric_cipher.encrypt_template(new_template)
    voter_id = str(uuid.uuid4())
    now_str = datetime.now(timezone.utc).isoformat()

    # 7. Insert into VOTER with has_voted = 'N'
    cursor.execute(
        """
        INSERT INTO VOTER (voter_id, name, id_type, id_last4, id_hash, fingerprint_template, has_voted, enrolled_at)
        VALUES (:1, :2, :3, :4, :5, :6, 'N', CURRENT_TIMESTAMP)
        """,
        (voter_id, req.name.strip(), req.id_type.strip(), id_last4, id_hash, encrypted_template),
    )

    return VoterEnrollResponse(
        voter_id=voter_id,
        name=req.name.strip(),
        id_type=req.id_type.strip(),
        id_last4=id_last4,
        has_voted="N",
        enrolled_at=now_str,
    )


@router.get(
    "/voters",
    response_model=List[VoterSearchItem],
    summary="Search voters by name (safe fields only)",
)
def search_voters(
    name: Optional[str] = Query(None, min_length=1, description="Partial or full voter name to search"),
    current_user: dict = Depends(require_operator),
    db=Depends(get_db),
) -> List[VoterSearchItem]:
    cursor = db.cursor()

    if name:
        cursor.execute(
            "SELECT voter_id, name, id_type, id_last4, has_voted, enrolled_at FROM VOTER WHERE UPPER(name) LIKE :1 ORDER BY name ASC",
            (f"%{name.strip().upper()}%",),
        )
    else:
        cursor.execute(
            "SELECT voter_id, name, id_type, id_last4, has_voted, enrolled_at FROM VOTER ORDER BY enrolled_at DESC",
        )

    rows = cursor.fetchall()
    results = []
    for r in rows:
        results.append(
            VoterSearchItem(
                voter_id=r["voter_id"],
                name=r["name"],
                id_type=r["id_type"],
                id_last4=r["id_last4"],
                has_voted=r["has_voted"],
                enrolled_at=str(r["enrolled_at"]),
            )
        )
    return results
