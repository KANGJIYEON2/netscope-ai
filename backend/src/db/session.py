import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. "
        "Please export it as an OS environment variable."
    )

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # 끊어진 커넥션 자동 감지
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)