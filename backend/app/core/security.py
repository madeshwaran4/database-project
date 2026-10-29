import base64
import hashlib
import hmac
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

import jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings

bearer_scheme = HTTPBearer(auto_error=False)


def hash_id(id_number: str, salt: Optional[str] = None) -> tuple[str, str]:
    """Computes id_last4 and a high-entropy salted cryptographic hash of a National/Government ID.
    Constraint (AGENTS.md Rule 4): Raw ID numbers must NEVER be stored.
    """
    clean_id = id_number.strip().upper()
    id_last4 = clean_id[-4:] if len(clean_id) >= 4 else clean_id.rjust(4, "0")
    active_salt = salt or settings.ID_HASH_SALT
    # Salted SHA-256
    hasher = hashlib.sha256()
    hasher.update(active_salt.encode("utf-8"))
    hasher.update(clean_id.encode("utf-8"))
    id_hash = hasher.hexdigest()
    return id_last4, id_hash


def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256."""
    salt = os.urandom(16).hex()
    iterations = 100000
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    )
    return f"pbkdf2:sha256:{iterations}${salt}${derived.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against PBKDF2 hash string."""
    try:
        parts = hashed_password.split("$")
        if len(parts) != 3:
            return False
        meta, salt, hash_hex = parts
        _, _, iterations_str = meta.split(":")
        iterations = int(iterations_str)
        derived = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations,
        )
        return hmac.compare_digest(derived.hex(), hash_hex)
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Generate signed JWT access token for operators or administrators."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a signed JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please authenticate again.",
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
        )


def create_vote_token(voter_id: str) -> str:
    """Generate a cryptographically signed, short-lived single-use vote authorization token.
    Expiry: 2 minutes. Contains random unique UUID (jti) for replay prevention.
    """
    token_jti = str(uuid.uuid4())
    payload = {
        "jti": token_jti,
        "sub": voter_id,
        "purpose": "cast_ballot",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.VOTE_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_and_verify_vote_token(token: str) -> dict:
    """Verify validity and signature of a vote token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("purpose") != "cast_ballot":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token purpose for voting.",
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Vote token has expired. Voter must re-verify at the booth.",
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or forged vote token.",
        )


# Role-based dependency injectors
def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Dict[str, Any]:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required.",
        )
    payload = decode_access_token(credentials.credentials)
    username = payload.get("sub")
    role = payload.get("role")
    if not username or not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token payload.",
        )
    return {"username": username, "role": role}


def require_role(allowed_roles: list[str]):
    def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role")
        # Normalize operator roles: 'operator' and 'booth-operator' are treated as operator
        normalized_user_role = "operator" if user_role in ("booth-operator", "operator") else user_role
        normalized_allowed = ["operator" if r in ("booth-operator", "operator") else r for r in allowed_roles]

        if user_role not in allowed_roles and normalized_user_role not in normalized_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of roles: {', '.join(allowed_roles)}",
            )
        return current_user
    return role_checker


require_admin = require_role(["admin"])
require_operator = require_role(["admin", "booth-operator", "operator"])
