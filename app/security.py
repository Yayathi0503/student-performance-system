from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash

from app.models import User

passwords = PasswordHash.recommended()
oauth2 = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_db(request: Request):
    with request.app.state.sessions() as db:
        yield db


def issue_token(user_id, settings):
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": str(user_id),
            "iat": now,
            "exp": now + timedelta(minutes=settings.access_token_minutes),
            "iss": "student-performance",
            "aud": "student-api",
        },
        settings.jwt_secret,
        algorithm="HS256",
    )


def current_user(request: Request, token: str = Depends(oauth2), db=Depends(get_db)):
    error = HTTPException(401, "Invalid or expired access token", headers={"WWW-Authenticate": "Bearer"})
    try:
        data = jwt.decode(
            token,
            request.app.state.settings.jwt_secret,
            algorithms=["HS256"],
            issuer="student-performance",
            audience="student-api",
            options={"require": ["sub", "exp", "iat"]},
        )
        user_id = int(data["sub"])
    except (jwt.PyJWTError, ValueError, TypeError):
        raise error
    user = db.get(User, user_id)
    if user is None:
        raise error
    return user
