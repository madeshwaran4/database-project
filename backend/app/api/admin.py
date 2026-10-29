import math
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.security import require_admin, require_operator
from app.db.session import get_db
from app.schemas.candidate import (
    CandidateCreate,
    CandidateUpdate,
    CandidateResponse,
    CandidateVoteResult,
    ElectionResultsResponse,
)
from app.schemas.verification import PaginatedLogsResponse, VerificationLogItem
from app.schemas.admin import PollingStatusResponse, ElectionStatsResponse

router = APIRouter(prefix="/api", tags=["Admin & Election Management"])


def _get_polling_status(cursor) -> str:
    cursor.execute("SELECT state_value FROM ELECTION_STATE WHERE state_key = :1", ("polling_status",))
    row = cursor.fetchone()
    if row:
        return row["state_value"].lower()
    return "closed"


# -----------------------------------------------------------------------------
# Polling Lifecycle Endpoints
# -----------------------------------------------------------------------------
@router.get(
    "/admin/polling/status",
    response_model=PollingStatusResponse,
    summary="Get current polling lifecycle status",
)
def get_polling_status(db=Depends(get_db)) -> PollingStatusResponse:
    cursor = db.cursor()
    cursor.execute("SELECT state_value, updated_at FROM ELECTION_STATE WHERE state_key = :1", ("polling_status",))
    row = cursor.fetchone()
    status_val = row["state_value"].lower() if row else "closed"
    updated_at = row["updated_at"] if row else datetime.now(timezone.utc).isoformat()
    return PollingStatusResponse(
        polling_status=status_val,
        is_open=(status_val == "open"),
        updated_at=str(updated_at),
    )


@router.post(
    "/admin/polling/open",
    response_model=PollingStatusResponse,
    summary="Open polling for voting (Admin Only)",
)
def open_polling(
    current_user: dict = Depends(require_admin),
    db=Depends(get_db),
) -> PollingStatusResponse:
    cursor = db.cursor()
    now_str = datetime.now(timezone.utc).isoformat()
    cursor.execute(
        "UPDATE ELECTION_STATE SET state_value = 'open', updated_at = CURRENT_TIMESTAMP WHERE state_key = 'polling_status'"
    )
    return PollingStatusResponse(polling_status="open", is_open=True, updated_at=now_str)


@router.post(
    "/admin/polling/close",
    response_model=PollingStatusResponse,
    summary="Close polling and finalize election (Admin Only)",
)
def close_polling(
    current_user: dict = Depends(require_admin),
    db=Depends(get_db),
) -> PollingStatusResponse:
    cursor = db.cursor()
    now_str = datetime.now(timezone.utc).isoformat()
    cursor.execute(
        "UPDATE ELECTION_STATE SET state_value = 'closed', updated_at = CURRENT_TIMESTAMP WHERE state_key = 'polling_status'"
    )
    return PollingStatusResponse(polling_status="closed", is_open=False, updated_at=now_str)


# -----------------------------------------------------------------------------
# Candidate CRUD (Blocked once polling opens)
# -----------------------------------------------------------------------------
@router.get(
    "/candidates",
    response_model=List[CandidateResponse],
    summary="List all registered election candidates",
)
def list_candidates(db=Depends(get_db)) -> List[CandidateResponse]:
    cursor = db.cursor()
    cursor.execute("SELECT candidate_id, name, party, description FROM CANDIDATE ORDER BY name ASC")
    rows = cursor.fetchall()
    return [
        CandidateResponse(
            candidate_id=r["candidate_id"],
            name=r["name"],
            party=r["party"],
            description=r["description"],
        )
        for r in rows
    ]


@router.post(
    "/candidates",
    response_model=CandidateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a candidate (Admin Only - blocked during polling)",
)
def create_candidate(
    req: CandidateCreate,
    current_user: dict = Depends(require_admin),
    db=Depends(get_db),
) -> CandidateResponse:
    cursor = db.cursor()
    if _get_polling_status(cursor) == "open":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add candidates while polling is currently open.",
        )

    cand_id = str(uuid.uuid4())
    cursor.execute(
        "INSERT INTO CANDIDATE (candidate_id, name, party, description) VALUES (:1, :2, :3, :4)",
        (cand_id, req.name.strip(), req.party.strip(), req.description.strip() if req.description else None),
    )
    return CandidateResponse(
        candidate_id=cand_id,
        name=req.name.strip(),
        party=req.party.strip(),
        description=req.description.strip() if req.description else None,
    )


@router.put(
    "/candidates/{candidate_id}",
    response_model=CandidateResponse,
    summary="Update candidate (Admin Only - blocked during polling)",
)
def update_candidate(
    candidate_id: str,
    req: CandidateUpdate,
    current_user: dict = Depends(require_admin),
    db=Depends(get_db),
) -> CandidateResponse:
    cursor = db.cursor()
    if _get_polling_status(cursor) == "open":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify candidates while polling is open.",
        )

    cursor.execute("SELECT candidate_id, name, party, description FROM CANDIDATE WHERE candidate_id = :1", (candidate_id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found.")

    new_name = req.name.strip() if req.name else row["name"]
    new_party = req.party.strip() if req.party else row["party"]
    new_desc = req.description.strip() if req.description is not None else row["description"]

    cursor.execute(
        "UPDATE CANDIDATE SET name = :1, party = :2, description = :3 WHERE candidate_id = :4",
        (new_name, new_party, new_desc, candidate_id),
    )
    return CandidateResponse(candidate_id=candidate_id, name=new_name, party=new_party, description=new_desc)


@router.delete(
    "/candidates/{candidate_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete candidate (Admin Only - blocked during polling)",
)
def delete_candidate(
    candidate_id: str,
    current_user: dict = Depends(require_admin),
    db=Depends(get_db),
):
    cursor = db.cursor()
    if _get_polling_status(cursor) == "open":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete candidates while polling is open.",
        )

    cursor.execute("SELECT candidate_id FROM CANDIDATE WHERE candidate_id = :1", (candidate_id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found.")

    cursor.execute("DELETE FROM CANDIDATE WHERE candidate_id = :1", (candidate_id,))
    return None


# -----------------------------------------------------------------------------
# Results Endpoints (CRITICAL: Only after polling closes)
# -----------------------------------------------------------------------------
@router.get(
    "/results",
    response_model=ElectionResultsResponse,
    summary="View election results (Only accessible after polling closes)",
)
def get_election_results(db=Depends(get_db)) -> ElectionResultsResponse:
    cursor = db.cursor()
    polling_status = _get_polling_status(cursor)

    # Phase 6 Constraint: Only after polling closes
    if polling_status == "open":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Election results are sealed and locked while polling is currently active.",
        )

    # Total votes cast
    cursor.execute("SELECT COUNT(*) as total FROM VOTE")
    total_votes = cursor.fetchone()["total"]

    # Candidate tallies
    cursor.execute("""
        SELECT c.candidate_id, c.name, c.party, COUNT(v.vote_id) as vote_count
        FROM CANDIDATE c
        LEFT JOIN VOTE v ON c.candidate_id = v.candidate_id
        GROUP BY c.candidate_id, c.name, c.party
        ORDER BY vote_count DESC, c.name ASC
    """)
    rows = cursor.fetchall()
    results = []
    for r in rows:
        count = r["vote_count"]
        pct = (count / total_votes * 100.0) if total_votes > 0 else 0.0
        results.append(
            CandidateVoteResult(
                candidate_id=r["candidate_id"],
                name=r["name"],
                party=r["party"],
                vote_count=count,
                percentage=round(pct, 2),
            )
        )

    return ElectionResultsResponse(
        total_votes=total_votes,
        polling_status=polling_status,
        results=results,
    )


# -----------------------------------------------------------------------------
# Logs & Stats Endpoints
# -----------------------------------------------------------------------------
@router.get(
    "/logs",
    response_model=PaginatedLogsResponse,
    summary="Paginated verification audit logs with filters (Operator / Admin)",
)
def get_verification_logs(
    result: Optional[str] = Query(None, description="Filter by result code (e.g. SUCCESS, DUPLICATE_ATTEMPT)"),
    voter_id: Optional[str] = Query(None, description="Filter by voter UUID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(require_operator),
    db=Depends(get_db),
) -> PaginatedLogsResponse:
    cursor = db.cursor()
    where_clauses = []
    params = []
    bind_idx = 1

    if result:
        where_clauses.append(f"result = :{bind_idx}")
        params.append(result.strip().upper())
        bind_idx += 1
    if voter_id:
        where_clauses.append(f"voter_id = :{bind_idx}")
        params.append(voter_id.strip())
        bind_idx += 1

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    # Count total
    cursor.execute(f"SELECT COUNT(*) as total FROM VERIFICATION_LOG {where_sql}", tuple(params))
    total = cursor.fetchone()["total"]

    # Paginate using Oracle OFFSET FETCH (12c+ syntax, supported by 21c XE)
    offset = (page - 1) * page_size
    query_params = list(params) + [offset, page_size]
    cursor.execute(
        f"""
        SELECT log_id, voter_id, attempted_at, result, reason, workstation_id
        FROM VERIFICATION_LOG
        {where_sql}
        ORDER BY attempted_at DESC
        OFFSET :{bind_idx} ROWS FETCH NEXT :{bind_idx + 1} ROWS ONLY
        """,
        tuple(query_params),
    )
    rows = cursor.fetchall()

    items = [
        VerificationLogItem(
            log_id=r["log_id"],
            voter_id=r["voter_id"],
            attempted_at=str(r["attempted_at"]),
            result=r["result"],
            reason=r["reason"],
            workstation_id=r.get("workstation_id") or "booth-01",
        )
        for r in rows
    ]

    total_pages = math.ceil(total / page_size) if total > 0 else 1
    return PaginatedLogsResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=items,
    )


@router.get(
    "/stats",
    response_model=ElectionStatsResponse,
    summary="Election turnout and verification statistics (Operator / Admin)",
)
def get_election_stats(
    current_user: dict = Depends(require_operator),
    db=Depends(get_db),
) -> ElectionStatsResponse:
    cursor = db.cursor()

    # Enrolled voters
    cursor.execute("SELECT COUNT(*) as count FROM VOTER")
    enrolled = cursor.fetchone()["count"]

    # Votes cast
    cursor.execute("SELECT COUNT(*) as count FROM VOTE")
    votes_cast = cursor.fetchone()["count"]

    # Denied attempts (any non-SUCCESS verification in log)
    cursor.execute("SELECT COUNT(*) as count FROM VERIFICATION_LOG WHERE result != 'SUCCESS'")
    denied = cursor.fetchone()["count"]

    turnout = round((votes_cast / enrolled * 100.0), 2) if enrolled > 0 else 0.0
    status_val = _get_polling_status(cursor)

    return ElectionStatsResponse(
        enrolled_voters=enrolled,
        votes_cast=votes_cast,
        denied_attempts=denied,
        turnout_percentage=turnout,
        polling_status=status_val,
    )
