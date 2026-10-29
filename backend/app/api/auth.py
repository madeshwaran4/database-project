from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.config import settings
from app.core.security import verify_password, create_access_token
from app.db.session import get_db
from app.schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse, summary="Operator and Administrator Login")
def login(req: LoginRequest, db=Depends(get_db)) -> TokenResponse:
    cursor = db.cursor()
    cursor.execute(
        "SELECT admin_id, username, password_hash, role FROM ADMIN_USER WHERE username = :1",
        (req.username.strip(),),
    )
    user = cursor.fetchone()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    stored_hash = user["password_hash"]
    user_role = user["role"]
    username = user["username"]

    if not verify_password(req.password, stored_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"sub": username, "role": user_role},
        expires_delta=expires,
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        role=user_role,
        username=username,
        expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
