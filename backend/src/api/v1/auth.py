from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.domain.auth import AuthDomainService
from src.schemas.auth import RegisterRequest, LoginRequest

router = APIRouter(prefix="/auth", tags=["Auth"])

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"

COOKIE_SECURE = False  # ✅ prod에서 True(HTTPS)
COOKIE_SAMESITE = "lax"

def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    response.set_cookie(
        ACCESS_COOKIE,
        access_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=60 * 60,  # access ttl과 맞추기(예: 60분)
        path="/",
    )
    response.set_cookie(
        REFRESH_COOKIE,
        refresh_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=60 * 60 * 24 * 14,  # refresh ttl과 맞추기(예: 14일)
        path="/auth",
    )

def clear_auth_cookies(response: Response):
    response.delete_cookie(ACCESS_COOKIE, path="/")
    response.delete_cookie(REFRESH_COOKIE, path="/auth")


@router.post("/register")
def register(req: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    service = AuthDomainService(db)
    try:
        tokens = service.register(email=req.email, password=req.password)
    except ValueError as e:
        if str(e) == "EMAIL_ALREADY_EXISTS":
            raise HTTPException(status_code=409, detail="Email already exists")
        raise HTTPException(status_code=400, detail=str(e))

    set_auth_cookies(response, tokens["access_token"], tokens["refresh_token"])
    return {"ok": True}


@router.post("/login")
def login(req: LoginRequest, response: Response, db: Session = Depends(get_db)):
    service = AuthDomainService(db)
    tokens = service.login(email=req.email, password=req.password)

    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    set_auth_cookies(response, tokens["access_token"], tokens["refresh_token"])
    return {"ok": True}


@router.post("/refresh")
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get(REFRESH_COOKIE)
    if not refresh_token:
        clear_auth_cookies(response)
        raise HTTPException(status_code=401, detail="NO_REFRESH_TOKEN")

    service = AuthDomainService(db)
    try:
        tokens = service.refresh(refresh_token)
    except ValueError as e:
        clear_auth_cookies(response)
        raise HTTPException(status_code=401, detail=str(e))

    set_auth_cookies(response, tokens["access_token"], tokens["refresh_token"])
    return {"ok": True}


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get(REFRESH_COOKIE)

    service = AuthDomainService(db)
    if refresh_token:
        try:
            service.logout(refresh_token)
        except ValueError:
            pass

    clear_auth_cookies(response)
    return {"ok": True}