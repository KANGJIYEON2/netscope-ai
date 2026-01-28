from src.db.base import Base
from src.db.session import engine

# 모델 import  (이거 안 하면 테이블 안 생김)
from src.model.log import Log
from src.model.analysis_result import AnalysisResult
from src.model.Project import Project
from src.model.Tenant import Tenant
from src.model.User import User
from src.model.weekly_report import WeeklyReport
from src.model.refresh_token import RefreshToken


def init_db():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()