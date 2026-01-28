import uuid
from datetime import datetime, UTC

from sqlalchemy.orm import Session

from src.model.User import User
from src.model.Tenant import Tenant
from src.model.refresh_token import RefreshToken  # 경로 맞춰서
from src.core.security import hash_password, verify_password, hash_refresh_token
from src.core.jwt import create_access_token, create_refresh_token,decode_token
from src.core.security import verify_refresh_token

class AuthDomainService:
    def __init__(self, db: Session):
        self.db = db

    def register(self, email: str, password: str) -> dict:
        # 이메일 중복 방지(권장)
        exists = self.db.query(User).filter(User.email == email).first()
        if exists:
            # FastAPI에서 409로 처리하고 싶으면 예외 커스텀해서 올려도 됨
            raise ValueError("EMAIL_ALREADY_EXISTS")

        tenant_id = str(uuid.uuid4())
        tenant = Tenant(id=tenant_id, name=email.split("@")[0])
        self.db.add(tenant)

        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            email=email,
            password_hash=hash_password(password),
            tenant_id=tenant_id,
        )
        self.db.add(user)

        # 토큰 발급
        access_token = create_access_token(user_id=user_id, tenant_id=tenant_id)
        refresh_token = create_refresh_token(user_id=user_id, tenant_id=tenant_id)

        # refresh 저장
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("INVALID_REFRESH_TOKEN_TYPE")

        jti = payload["jti"]
        exp = payload["exp"]  # 보통 timestamp(int)
        expires_at = datetime.fromtimestamp(exp, tz=UTC)

        rt = RefreshToken(
            id=jti,  # ✅ PK를 jti로 통일
            user_id=user_id,
            tenant_id=tenant_id,
            token_hash=hash_refresh_token(refresh_token),
            jti=jti,
            expires_at=expires_at,
            revoked=False,
        )
        self.db.add(rt)
        self.db.commit()

        return {"access_token": access_token, "refresh_token": refresh_token}

    def login(self, email: str, password: str) -> dict | None:
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None

        access_token = create_access_token(user_id=user.id, tenant_id=user.tenant_id)
        refresh_token = create_refresh_token(user_id=user.id, tenant_id=user.tenant_id)

        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("INVALID_REFRESH_TOKEN_TYPE")

        jti = payload["jti"]
        exp = payload["exp"]
        expires_at = datetime.fromtimestamp(exp, tz=UTC)

        rt = RefreshToken(
            id=jti,
            user_id=user.id,
            tenant_id=user.tenant_id,
            token_hash=hash_refresh_token(refresh_token),
            jti=jti,
            expires_at=expires_at,
            revoked=False,
        )
        self.db.add(rt)
        self.db.commit()

        return {"access_token": access_token, "refresh_token": refresh_token}

    def refresh(self, refresh_token: str) -> dict:
        payload = decode_token(refresh_token)

        if payload.get("type") != "refresh":
            raise ValueError("INVALID_TOKEN_TYPE")

        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")
        jti = payload.get("jti")
        exp = payload.get("exp")

        if not user_id or not tenant_id or not jti or not exp:
            raise ValueError("INVALID_REFRESH_PAYLOAD")

        now = datetime.now(UTC)

        # ✅ DB row: 멀티테넌시/유저 교차검증
        rt = (
            self.db.query(RefreshToken)
            .filter(
                RefreshToken.jti == jti,
                RefreshToken.user_id == user_id,
                RefreshToken.tenant_id == tenant_id,
            )
            .first()
        )

        if not rt:
            raise ValueError("REFRESH_NOT_FOUND")

        # ✅ 해시 검증 (토큰 위조/변조 방지)
        if not verify_refresh_token(refresh_token, rt.token_hash):
            # 위조 의심: 바로 전체 세션 revoke까지는 선택인데,
            # 난 운영에서는 '전체 revoke' 권장. (원하면 여기서는 401만)
            self._revoke_all_user_sessions(user_id=user_id, tenant_id=tenant_id)
            raise ValueError("REFRESH_HASH_MISMATCH_ALL_REVOKED")

        # ✅ 만료 체크(서버 기준)
        if rt.expires_at < now:
            # 만료면 revoke 표시하고 끝
            if not rt.revoked:
                rt.revoked = True
                rt.revoked_at = now
                self.db.add(rt)
                self.db.commit()
            raise ValueError("REFRESH_EXPIRED")

        # ✅ 재사용 탐지: 이미 revoked된 refresh로 요청 => 탈취 의심
        if rt.revoked:
            self._revoke_all_user_sessions(user_id=user_id, tenant_id=tenant_id)
            raise ValueError("REFRESH_REUSE_DETECTED_ALL_REVOKED")

        # ✅ Rotation: 기존 refresh 폐기
        rt.revoked = True
        rt.revoked_at = now
        self.db.add(rt)

        # ✅ 새 토큰 발급
        new_access = create_access_token(user_id=user_id, tenant_id=tenant_id)
        new_refresh = create_refresh_token(user_id=user_id, tenant_id=tenant_id)

        new_payload = decode_token(new_refresh)
        new_jti = new_payload.get("jti")
        new_exp = new_payload.get("exp")
        if not new_jti or not new_exp:
            raise ValueError("INVALID_NEW_REFRESH_PAYLOAD")

        new_expires_at = datetime.fromtimestamp(new_exp, tz=UTC)

        new_rt = RefreshToken(
            id=new_jti,  # PK를 jti로 쓰는 전략
            user_id=user_id,
            tenant_id=tenant_id,
            token_hash=hash_refresh_token(new_refresh),
            jti=new_jti,
            expires_at=new_expires_at,
            revoked=False,
        )
        self.db.add(new_rt)
        self.db.commit()

        return {"access_token": new_access, "refresh_token": new_refresh}

    def logout(self, refresh_token: str) -> None:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("INVALID_TOKEN_TYPE")

        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")
        jti = payload.get("jti")
        if not user_id or not tenant_id or not jti:
            raise ValueError("INVALID_REFRESH_PAYLOAD")

        rt = (
            self.db.query(RefreshToken)
            .filter(
                RefreshToken.jti == jti,
                RefreshToken.user_id == user_id,
                RefreshToken.tenant_id == tenant_id,
            )
            .first()
        )
        if not rt:
            return

        now = datetime.now(UTC)
        if not rt.revoked:
            rt.revoked = True
            rt.revoked_at = now
            self.db.add(rt)
            self.db.commit()

    def logout_all(self, user_id: str, tenant_id: str) -> None:
        self._revoke_all_user_sessions(user_id=user_id, tenant_id=tenant_id)

    def _revoke_all_user_sessions(self, user_id: str, tenant_id: str) -> None:
        now = datetime.now(UTC)
        (
            self.db.query(RefreshToken)
            .filter(
                RefreshToken.user_id == user_id,
                RefreshToken.tenant_id == tenant_id,
                RefreshToken.revoked == False,  # noqa
            )
            .update({"revoked": True, "revoked_at": now})
        )
        self.db.commit()