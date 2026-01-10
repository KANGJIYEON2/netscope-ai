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

# 작업 디렉토리
WORKDIR /src

# requirements 먼저
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 소스 복사
COPY . .

# ✅ 핵심 수정 포인트
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
