from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

from src.core.config import settings

# auth/login 엔드포인트 경로
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

ALGORITHM = "HS256"


def get_current_context(token: str = Depends(oauth2_scheme)) -> dict:
    """
    JWT 검증 후 user / tenant context 반환
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
        )
    except JWTError:
        raise credentials_exception

    user_id: str | None = payload.get("sub")
    tenant_id: str | None = payload.get("tenant_id")

    if not user_id or not tenant_id:
        raise credentials_exception

    return {
        "user_id": user_id,
        "tenant_id": tenant_id,
    }
