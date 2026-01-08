from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from api.v1.logs import router as logs_router
from api.v1.analysis import router as analysis_router
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
