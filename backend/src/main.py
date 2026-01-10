from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from src.api.v1.logs import router as logs_router
from src.api.v1.analysis import router as analysis_router
from src.api.v1.ingest import router as ingest_router
from src.api.v1.reports import router as report_router
from src.api.v1.projects import router as projects_router
from src.api.v1.auth import router as auth_router
from src.api.v1.test import router as test_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="NETSCOPE AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발용 (나중에 도메인 제한)
    allow_credentials=True,
    allow_methods=["*"],  # OPTIONS 포함
    allow_headers=["*"],
)

app.include_router(logs_router)
app.include_router(analysis_router)
app.include_router(ingest_router)
app.include_router(report_router)
app.include_router(projects_router)
app.include_router(auth_router)
app.include_router(test_router)