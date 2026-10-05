from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_refresh_token
)
from database import SessionLocal
from models import User
from schemas import (
    UserCreate,
    Token,
    RefreshTokenRequest,
    AccessTokenResponse,
    MessageResponse
)

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/register",
             response_model=MessageResponse)
def register(
        user: UserCreate,
        db: Session = Depends(get_db)
):
    existing_username = db.query(User).filter(
        User.username == user.username
    ).first()

    if existing_username:
        raise HTTPException(
            status_code=409,
            detail="Username already exists"
        )

    existing_email = db.query(User).filter(
        User.email == user.email
    ).first()

    if existing_email:
        raise HTTPException(
            status_code=409,
            detail="Email already exists"
        )
    hashed_password = hash_password(
        user.password
    )

    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully"
    }

@router.post("/login",response_model=Token)
def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db)
):

    db_user = db.query(User).filter(
        User.username == form_data.username
    ).first()

    if not db_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    if not verify_password(
            form_data.password,
            db_user.hashed_password
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password"
        )

    access_token = create_access_token(
        data={
            "sub": db_user.username,
            "role": db_user.role
        }
    )
    refresh_token = create_refresh_token(
        data={
            "sub": db_user.username,
            "role": db_user.role,
        }
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }
@router.post("/refresh",
             response_model=AccessTokenResponse)
def refresh_token(
        request: RefreshTokenRequest
):
    user = verify_refresh_token(
        request.refresh_token
    )
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token"
        )
    access_token = create_access_token(
        data={
            "sub": user["username"],
            "role": user["role"]
        }
    )
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }