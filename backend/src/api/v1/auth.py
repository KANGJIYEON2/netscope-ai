from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.session import get_db
from domain.auth import AuthDomainService
from schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
)

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post("/register", response_model=TokenResponse)
def register(
    req: RegisterRequest,
    db: Session = Depends(get_db),
):
    service = AuthDomainService(db)
    token = service.register(
        email=req.email,
        password=req.password,
    )
    return {"access_token": token}


@router.post("/login", response_model=TokenResponse)
def login(
    req: LoginRequest,
    db: Session = Depends(get_db),
):
    service = AuthDomainService(db)
    token = service.login(
        email=req.email,
        password=req.password,
    )

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return {"access_token": token}
