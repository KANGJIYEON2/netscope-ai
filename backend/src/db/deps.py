from db.session import SessionLocal

#FAST API 용 DB 주입
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()