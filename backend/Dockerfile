# Python 런타임
FROM python:3.11-slim

# 시스템 패키지
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-kor \
    ghostscript \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# ✅ FastAPI 코드 기준 디렉토리
WORKDIR /src/backend

# requirements
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 소스 복사
COPY . .

# ✅ 핵심: src를 Python path로 인식
ENV PYTHONPATH=/src/backend

# ✅ 여기 중요
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
