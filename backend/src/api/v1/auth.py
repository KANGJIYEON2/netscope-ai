from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.orm import Session

from src.core.config import settings
from src.db.session import get_db
from src.domain.auth import AuthDomainService
from src.schemas.auth import RegisterRequest, LoginRequest

router = APIRouter(prefix="/auth", tags=["Auth"])

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"


def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    access_max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    refresh_max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

    response.set_cookie(
        key=ACCESS_COOKIE,
        value=access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=access_max_age,
        path="/",
    )

    # ✅ 보안상 refresh는 auth 경로로 제한 (유지)
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=refresh_max_age,
        path="/auth",  # or "/auth/refresh" 로 더 좁혀도 됨
    )


def clear_auth_cookies(response: Response):
    response.delete_cookie(key=ACCESS_COOKIE, path="/")
    response.delete_cookie(key=REFRESH_COOKIE, path="/auth")


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
