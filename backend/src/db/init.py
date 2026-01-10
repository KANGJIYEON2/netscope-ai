from db.base import Base
from db.session import engine

# 모델 import  (이거 안 하면 테이블 안 생김)
from model.log import Log
from model.analysis_result import AnalysisResult
from model.Project import Project
from model.Tenant import Tenant
from model.User import User
from model.weekly_report import WeeklyReport

def init_db():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()