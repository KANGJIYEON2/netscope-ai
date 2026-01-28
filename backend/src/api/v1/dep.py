from fastapi import Depends, HTTPException, Request, status
from jose import jwt, JWTError

from src.core.config import settings

ALGORITHM = "HS256"


def _get_bearer_from_header(request: Request) -> str | None:
    auth = request.headers.get("Authorization")
    if not auth:
        return None
    if not auth.startswith("Bearer "):
        return None
    return auth.split(" ", 1)[1].strip()


def get_current_context(request: Request) -> dict:
    """
    ✅ 쿠키 기반 JWT 검증 후 user / tenant context 반환
    - 1순위: 쿠키 access_token
    - 2순위(옵션): Authorization: Bearer <token> fallback
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
    )

    # ✅ 1) 쿠키에서 access_token 읽기
    token = request.cookies.get("access_token")

    # ✅ 2) 헤더 fallback (원하면 유지, 싫으면 이 블록 삭제)
    if not token:
        token = _get_bearer_from_header(request)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="NO_ACCESS_TOKEN",
        )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
        )
    except JWTError:
        raise credentials_exception

    # ✅ access 토큰 타입 체크(중요)
    if payload.get("type") != "access":
        raise credentials_exception

    user_id: str | None = payload.get("sub")
    tenant_id: str | None = payload.get("tenant_id")

    if not user_id or not tenant_id:
        raise credentials_exception

    return {"user_id": user_id, "tenant_id": tenant_id}