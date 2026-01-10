import uuid
from sqlalchemy.orm import Session

from src.model.User import User
from src.model.Tenant import Tenant
from src.core.security import hash_password, verify_password
from src.core.jwt import create_access_token


class AuthDomainService:
    def __init__(self, db: Session):
        self.db = db

    def register(self, email: str, password: str) -> str:
        # 1. Tenant 생성
        tenant_id = str(uuid.uuid4())
        tenant = Tenant(
            id=tenant_id,
            name=email.split("@")[0],
        )
        self.db.add(tenant)

        # 2. User 생성
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            email=email,
            password_hash=hash_password(password),
            tenant_id=tenant_id,
        )
        self.db.add(user)

        self.db.commit()

        # 3. JWT 발급
        return create_access_token(
            user_id=user_id,
            tenant_id=tenant_id,
        )

    def login(self, email: str, password: str) -> str | None:
        user = (
            self.db.query(User)
            .filter(User.email == email)
            .first()
        )

        if not user:
            return None

        if not verify_password(password, user.password_hash):
            return None

        return create_access_token(
            user_id=user.id,
            tenant_id=user.tenant_id,
        )
