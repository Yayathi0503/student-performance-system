from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models import User
from app.schemas import Credentials, UserOut
from app.security import current_user, get_db, issue_token, passwords

router = APIRouter(prefix="/auth", tags=["Authentication"])
DUMMY_HASH = passwords.hash("dummy-password-for-timing")


@router.post("/register", response_model=UserOut, status_code=201)
def register(body: Credentials, db=Depends(get_db)):
    user = User(email=str(body.email).lower(), password_hash=passwords.hash(body.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Account already exists")
    return user


@router.post("/login")
def login(request: Request, form: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    user = db.scalar(select(User).where(User.email == form.username.strip().lower()))
    valid = passwords.verify(form.password, user.password_hash if user else DUMMY_HASH)
    if user is None or not valid:
        raise HTTPException(401, "Incorrect email or password", headers={"WWW-Authenticate": "Bearer"})
    return {"access_token": issue_token(user.id, request.app.state.settings), "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
def me(user=Depends(current_user)):
    return user
