import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from dotenv import load_dotenv

load_dotenv()

# Password hashing configuration using passlib[bcrypt]
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_jwt_secret_key() -> str:
    secret = os.getenv("JWT_SECRET_KEY")
    if not secret:
        raise RuntimeError("JWT_SECRET_KEY environment variable must be set")
    return secret

def get_jwt_algorithm() -> str:
    return os.getenv("JWT_ALGORITHM", "HS256")

def hash_password(password: str) -> str:
    """Hashes a raw password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against its bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(user_id: int, email: str, expires_delta: Optional[timedelta] = None) -> str:
    """Generates a signed JWT access token with 24 hours expiration."""
    secret_key = get_jwt_secret_key()
    algorithm = get_jwt_algorithm()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(hours=24)
        
    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "email": email,
        "exp": int(expire.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
    }
    
    encoded_jwt = jwt.encode(payload, secret_key, algorithm=algorithm)
    return encoded_jwt

def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodes and validates a JWT access token."""
    secret_key = get_jwt_secret_key()
    algorithm = get_jwt_algorithm()
    
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
