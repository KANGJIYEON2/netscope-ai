# Development Guide

> 신규 합류자/외부 베타 도입자를 위한 로컬 개발·테스트·기여 가이드.

## 목차
- [1. 사전 요구](#1-사전-요구)
- [2. 5분 셋업](#2-5분-셋업)
- [3. 실행 시나리오](#3-실행-시나리오)
- [4. 디렉터리 빠른 참조](#4-디렉터리-빠른-참조)
- [5. 코드 컨벤션](#5-코드-컨벤션)
- [6. 테스트 정책](#6-테스트-정책)
- [7. Git / PR 정책](#7-git--pr-정책)
- [8. 환경변수 카탈로그](#8-환경변수-카탈로그)
- [9. 자주 막히는 곳](#9-자주-막히는-곳)
- [10. 디버깅 팁](#10-디버깅-팁)

---

## 1. 사전 요구

| 도구 | 버전 | 용도 |
| --- | --- | --- |
| Python | ≥ 3.10 | 백엔드, 에이전트 |
| Node.js | ≥ 20 LTS | 프론트엔드 (Next 16) |
| npm | ≥ 10 | 프론트 패키지 |
| Git | ≥ 2.40 | — |
| (옵션) PostgreSQL | ≥ 14 | P0-1 이후 영속화 활성화 시 |
| (옵션) OpenAI API Key | — | `strategy=gpt` 분석 사용 시 |

플랫폼: macOS / Linux / **Windows 11** (PowerShell 사용 시 BOM·CRLF 주의 — 에이전트가 자동 처리하지만 코드 편집 시 LF 권장)

---

## 2. 5분 셋업

### 2-1. 클론 & 디렉터리
```bash
git clone <repo>
cd netscope-ai
```

### 2-2. 백엔드
```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# (옵션) GPT 사용
$env:OPENAI_API_KEY = "sk-..."

uvicorn src.main:app --reload --port 8000
```
→ http://localhost:8000/docs (FastAPI 자동 스웨거)

### 2-3. 프론트엔드
새 터미널:
```powershell
cd frontend
npm install

# (옵션) API 위치 변경
$env:NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000"

npm run dev
```
→ http://localhost:3000

### 2-4. 에이전트 (옵션)
```powershell
cd backend\netscope-agent
python netscope-agent.py --path ..\..\test-log\shell.log --source demo
```
- `test-log/shell.log` 에 라인을 추가(`Add-Content`)하면 실시간으로 백엔드에 전송됨.
- 프론트의 "Incoming Logs" 패널에 3초 이내 표시되면 정상.

### 2-5. 분석 1회 돌려보기 (curl)
```bash
curl -X POST http://localhost:8000/logs \
  -H "Content-Type: application/json" \
  -d '{"source":"gateway","message":"Request timed out after 30s","level":"ERROR"}'

# id 받아서
curl -X POST http://localhost:8000/analysis \
  -H "Content-Type: application/json" \
  -d '{"log_ids":["<UUID>"],"strategy":"rule"}'
```

---

## 3. 실행 시나리오

| 목적 | 띄울 것 | 메모 |
| --- | --- | --- |
| **프론트만 작업** | 백엔드 + 프론트 | 에이전트 없이 LogForm으로 수동 입력 |
| **룰 엔진 튜닝** | 백엔드 + `validation/distribution.py` | UI 없이 50개 시나리오로 회귀 |
| **에이전트 검증** | 백엔드 + 에이전트 + 임의 로그 파일 | `Add-Content` 또는 `echo >>` 로 라인 주입 |
| **풀스택 데모** | 4개 모두 | 발표/회의 시나리오 |
| **GPT 동작 확인** | 백엔드 (OPENAI_API_KEY 세팅) + 프론트 | StrategySelect → GPT |

---

## 4. 디렉터리 빠른 참조

```
netscope-ai/
├── CLAUDE.md                          ← 프로젝트 컨텍스트 (먼저 읽기)
├── docs/
│   ├── README.md                      ← 문서 인덱스 (본 파일들의 색인)
│   ├── PM_ENHANCEMENT_PLAN.md         ← 로드맵
│   ├── API_REFERENCE.md               ← 엔드포인트 스펙
│   ├── RULE_ENGINE.md                 ← 룰 엔진 정본
│   ├── DEVELOPMENT.md                 ← (현재 문서)
│   └── DESIGN_SYSTEM.md               ← FE 토큰/컴포넌트 룰
├── backend/
│   ├── src/
│   │   ├── main.py                    ← FastAPI 부트
│   │   ├── api/v1/                    ← 라우터
│   │   ├── log/                       ← 로그 도메인
│   │   ├── analysis/                  ← ⭐ 룰 엔진 + GPT
│   │   ├── schemas/                   ← Pydantic DTO
│   │   ├── model/                     ← SQLAlchemy ORM (미연결)
│   │   ├── repositories/              ← (미연결)
│   │   ├── infrastructure/            ← storage, db, redis
│   │   └── core/                      ← config, security, logging (스텁)
│   ├── netscope-agent/                ← 단일 스크립트 collector
│   ├── tests/                         ← pytest
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── app/                       ← Next.js app router
│       ├── lib/                       ← API 클라이언트
│       ├── types/                     ← TS 타입
│       └── styles/
└── test-log/shell.log                 ← 데모용 샘플
```

`CLAUDE.md` 의 §2(디렉터리 매핑)도 함께 참고.

---

## 5. 코드 컨벤션

### 5-1. 공통
- **언어**: 식별자/주석 영어. 도메인 문서·기획서는 한국어 OK.
- **줄바꿈**: LF (Windows 편집기 주의). `.gitattributes`로 강제 권장.
- **인코딩**: UTF-8 (BOM 없이). 에이전트는 BOM/제어문자를 클린업하지만 소스 파일은 깨끗하게.

### 5-2. Python (backend)
- **포매터**: `ruff format` (제안 — 도입 시 PR 1건으로). `black` 도 호환.
- **린터**: `ruff check`.
- **타입 힌트**: 모든 public 함수 시그니처에 type hint. `from __future__ import annotations` 권장.
- **임포트 순서**: stdlib → 3rd party → local. ruff가 정렬.
- **로깅**: `print` 금지 (에이전트 제외). `logging.getLogger(__name__)` 사용. `core/logging.py` 채워지면 구조화 로그로 표준화 예정.
- **레이어 경계**:
  - 라우터(`api/v1`)는 storage/ORM을 **직접 부르지 않는다**. 항상 service 경유.
  - 분석 엔진(`analysis/`)은 ORM/DB 모름. `Log` 인스턴스만 받음.
  - 사이드이펙트(DB 저장, 외부 API)는 service / repository 레이어로.

### 5-3. TypeScript (frontend)
- **포매터/린터**: ESLint (이미 `eslint.config.mjs` 존재). Prettier 도입 가능.
- **컴포넌트**: 함수형, "use client" 는 필요한 곳만. 디폴트 export 회피, named export 선호.
- **타입**: `any` 금지. 백엔드 DTO 변경 시 `frontend/src/types/`도 같은 PR로 동기화.
- **API 호출**: 항상 `lib/api/*.ts` 래퍼 경유. 컴포넌트에서 `axios` 직접 호출 금지.
- **스타일**: Tailwind 우선, 컴포넌트 내부에 임시 hex 컬러 금지 — `DESIGN_SYSTEM.md`의 토큰만 사용.

### 5-4. 명명
| 종류 | 규칙 | 예 |
| --- | --- | --- |
| Python 함수/변수 | `snake_case` | `aggregate_evidence` |
| Python 클래스 | `PascalCase` | `RuleEngine` |
| TS 컴포넌트 | `PascalCase` | `AnalysisResult` |
| TS 훅 | `useFoo` | `useLogs` |
| 룰 ID | `R001`, 사용자 정의는 `Cxxx` | `R001` |

---

## 6. 테스트 정책

### 6-1. 현재 상태
- `backend/tests/test_health.py` 1개. 회귀 방어 사실상 0.
- `analysis/validation/` 50개 시나리오 — pytest 미통합.

### 6-2. 목표 (P0-7)
| 레벨 | 도구 | 예 |
| --- | --- | --- |
| Unit | pytest | `RuleEngine.aggregate(logs)` 단독 검증 |
| Integration | pytest + httpx `TestClient` | `POST /logs → POST /analysis → GET /analysis/{id}` e2e |
| 회귀 | `validation/distribution.py` → pytest 변환 | 룰 분포 회귀 |
| (P1+) E2E | Playwright | 대시보드 렌더링 / Print 미디어 |

### 6-3. 새 PR이 만족해야 할 최소
- 변경된 함수에 대한 unit test 1개 이상
- 룰 추가 시 `validation/test_cases.py` 양성/음성 케이스 1쌍
- DTO 변경 시 양쪽(BE/FE) 동기화 + 기존 통합 테스트 통과

### 6-4. 실행
```bash
# 백엔드 단위 테스트
cd backend
pytest

# 룰 분포 검증
python -m src.analysis.validation.distribution

# 프론트 빌드 체크
cd ../frontend
npm run build
```

---

## 7. Git / PR 정책

### 7-1. 브랜치
- `main` — 배포 가능 상태 가정. 직접 푸시 금지 (베타 도입 후엔 보호 룰).
- 작업: `feat/<scope>-<short>`, `fix/<scope>-<short>`, `chore/<scope>-<short>`
  - 예: `feat/api-analysis-id`, `fix/agent-resume`, `chore/docs-rule-engine`

### 7-2. 커밋 메시지
```
<type>(<scope>): <subject>

<body — 왜 변경했는지>

<footer — 이슈 참조, breaking change>
```
- `type`: `feat` / `fix` / `chore` / `docs` / `refactor` / `test`
- 한 줄 제목 ≤ 72자, 본문은 *왜*에 집중 (코드 디프는 *무엇*을 보여줌)

### 7-3. PR 체크리스트 (제안 템플릿)
- [ ] 변경 의도 1~2 문단 설명
- [ ] 스크린샷 (UI 변경 시)
- [ ] 회귀 테스트 결과 (룰/분포 변경 시 `distribution.py` 출력 첨부)
- [ ] BE/FE DTO 동기화 확인 (해당 시)
- [ ] `CLAUDE.md` 또는 docs 업데이트 (사용자 영향 변경 시)

### 7-4. 작은 PR 우선
- 한 PR = 한 가지 변경. 룰 추가 + 디자인 토큰 변경은 분리.
- diff 500 라인 넘으면 쪼갤 것 (테스트 제외).

---

## 8. 환경변수 카탈로그

| 변수 | 사용처 | 기본 | 설명 |
| --- | --- | --- | --- |
| `OPENAI_API_KEY` | backend | (none) | 미설정 시 GPT 분석 비활성. `strategy=gpt`도 룰만 실행 |
| `NEXT_PUBLIC_API_BASE_URL` | frontend | `http://localhost:8000` | API 위치 |
| (P0 추가 예정) `DATABASE_URL` | backend | — | `postgresql+psycopg://...` |
| (P0 추가 예정) `ALLOWED_ORIGINS` | backend | `*` | CORS 화이트리스트 (콤마 구분) |
| (P0 추가 예정) `LOG_LEVEL` | backend | `INFO` | 백엔드 로깅 레벨 |
| (P1 추가 예정) `REDIS_URL` | backend | — | 결과 캐시 |

> `.env.example` 추가 PR 권장 (현재 없음).

---

## 9. 자주 막히는 곳

### 9-1. "분석 결과가 항상 LOW로 나옴"
- 입력 로그가 `INFO` 만 있거나 룰 매칭 안 됨. `RULE_ENGINE.md` §11 시뮬레이션 표 확인.
- `level=ERROR` 와 메시지에 `timeout` 포함된 로그 2개 이상 넣어 보기.

### 9-2. "GPT 선택했는데 결과가 룰만 나옴"
- `OPENAI_API_KEY` 미설정 → 조용한 폴백. 백엔드 로그 또는 응답의 `strategy_used` 확인.
- 모델명 이슈 — 코드는 `gpt-4.1-mini`. 의도가 `gpt-4o-mini`라면 `gpt_analyzer.py` 수정 (P0 항목).

### 9-3. "프론트가 API에 못 붙음"
- 백엔드 CORS 가 현재 `*` 라 거의 항상 통과. 그래도 안 되면:
  - `NEXT_PUBLIC_API_BASE_URL` 정확한지
  - 백엔드 `--port 8000` 인지
  - 브라우저 콘솔 네트워크 탭에서 실제 요청 URL 확인

### 9-4. "에이전트가 로그를 안 보냄"
- 1차 필터를 통과해야 함 (ERROR/WARN/TIMEOUT/5xx 중 하나). `INFO` 만 있는 라인은 의도적으로 무시.
- 시작 시점 EOF부터 — 이미 있는 라인은 안 보냄. 새로 라인을 *추가*해야 함.

### 9-5. "프론트 폴링이 누적되어 느려짐"
- `setInterval` cleanup 누락 의심. `useEffect` return에서 `clearInterval` 확인.

### 9-6. Windows 인코딩
- 에이전트가 BOM/CR/제어문자 클린업하므로 PowerShell `Add-Content`로 라인 주입해도 안전.
- 단, 소스 파일을 직접 편집할 땐 BOM 없는 UTF-8 사용 (Python 3.10+ 는 BOM도 읽지만 파일 일관성 위해).

---

## 10. 디버깅 팁

### 10-1. FastAPI Swagger
- http://localhost:8000/docs — DTO 스키마 + 시도 가능한 폼.
- 큰 페이로드 디버깅에 유용.

### 10-2. 룰 엔진만 단독 실행 (REPL)
```python
from src.log.models import Log
from src.analysis.rule_engine import RuleEngine
from datetime import datetime, timezone

logs = [
    Log(source="gateway", message="Request timed out after 30s",
        level="ERROR", timestamp=datetime.now(timezone.utc),
        received_at=datetime.now(timezone.utc)),
    # ...
]
res = RuleEngine().aggregate(logs)
print(res.matched_rules, res.base_score)
```

### 10-3. 에이전트가 어떤 라인을 보냈는지
- 에이전트는 stdout에 보낸 라인을 출력함. tail -f 로 확인.
- 백엔드는 현재 access log만. P0의 구조화 로깅 도입 후엔 request id로 추적.

### 10-4. 분석 결과 일관성 확인
- 같은 `log_ids` 로 두 번 호출해서 `confidence` 가 동일한지. 다르면 룰 엔진에 무작위성이 들어간 것 — 즉시 회귀.

### 10-5. 프론트 상태 디버깅
- React DevTools 로 `page.tsx` 의 logs/analysisResult/strategy 상태 관찰.
- 폴링 주기 임시 변경(3000 → 30000) 후 네트워크 탭 정리하면 보기 쉬움.

---

## 부록 — 참고 명령어 모음

```powershell
# 백엔드 hot reload + 로그 레벨 디버그
$env:LOG_LEVEL="DEBUG"; uvicorn src.main:app --reload --port 8000

# 룰 회귀
python -m src.analysis.validation.distribution

# 에이전트
python netscope-agent.py --path C:\logs\app.log --source api

# 프론트 빌드 검증 (배포 전)
npm run build && npm run start

# 의존성 업데이트 점검
pip list --outdated
npm outdated
```
