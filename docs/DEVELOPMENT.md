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
| **Docker + Compose** | 최신 | **권장 실행 경로** (postgres + backend + frontend 한 번에) |
| Python | ≥ 3.10 | 백엔드, 에이전트 (수동 실행 시) |
| Node.js | ≥ 20 LTS | 프론트엔드 (Next 16) (수동 실행 시) |
| npm | ≥ 10 | 프론트 패키지 |
| Git | ≥ 2.40 | — |
| **PostgreSQL** | ≥ 14 (compose는 16) | **필수** — DB 영속화 활성. 수동 실행 시 별도 기동 필요 |
| (옵션) OpenAI API Key | — | `strategy=gpt` 분석·주간 리포트 GPT 요약 사용 시 |

플랫폼: macOS / Linux / **Windows 11** (PowerShell 사용 시 BOM·CRLF 주의 — 에이전트가 자동 처리하지만 코드 편집 시 LF 권장)

---

## 2. 셋업

### 2-A. Docker Compose (권장)

```bash
git clone <repo> && cd netscope-ai

# backend/.env.docker 에 SECRET_KEY(필수) · OPENAI_API_KEY(선택) · INGEST_API_KEY(선택) 채움
#   (compose backend 가 env_file: ./backend/.env.docker 로 주입.
#    DATABASE_URL/APP_ENV 는 docker-compose.yml 이 직접 설정. .env.docker 는 git 미추적)
#   ※ OPENAI_API_KEY 를 채우거나 바꾼 뒤에는 env_file 재주입 위해 backend 재생성:
#     docker compose up -d --force-recreate backend

docker compose up -d --build
# Postgres   → localhost:5432  (volume: postgres_data)
# Backend    → http://localhost:8000  (Swagger: /docs)
# Frontend   → http://localhost:3000  (로그인 후 → /dashboard Fleet 커맨드)

# 데모 데이터 시드 (alice/bob/carol@demo.io · PW Demo1234!)
docker compose exec backend python -m scripts.seed --reset
# 대량 데모(트렌드/이슈/라이브피드 채우기, 14일 backdate)
docker compose exec backend python -m scripts.seed_big
```

> **실시간 데모**: `/dashboard` 를 열어둔 채 `POST /ingest`(X-Tenant-ID/X-Project-ID 헤더)로 에러 로그를 쏘면, 새 분석이 SSE로 즉시 화면에 뜬다(토스트 + Issues Board + Live Activity).

종료/초기화: `docker compose down` (데이터 유지) · `docker compose down -v` (DB wipe).

### 2-B. 로컬 (수동)

> ⚠️ `SECRET_KEY` 는 **필수** (`core/config.py` 에 기본값 없음 — 미설정 시 부팅 실패). `DATABASE_URL` 도 설정해야 보호 라우트가 동작한다. Postgres 가 먼저 떠 있어야 함.

```powershell
# Backend
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

$env:SECRET_KEY = "dev-secret"
$env:DATABASE_URL = "postgresql+psycopg://netscope:netscope_dev_pw@localhost:5432/netscope"
$env:OPENAI_API_KEY = "sk-..."        # 선택

uvicorn src.main:app --reload --port 8000
```
→ http://localhost:8000/docs (FastAPI 자동 스웨거)

```powershell
# Frontend (새 터미널)
cd frontend
npm install
$env:NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000"
npm run dev
```
→ http://localhost:3000

### 2-C. 분석 흐름 한 번 돌려보기 (인증 필요)

> 모든 `/projects/...` 라우트는 쿠키 인증이 필요하다. curl 로는 쿠키 jar(`-c`/`-b`)를 써야 하므로, **Swagger UI(`/docs`) 또는 프론트**로 확인하는 게 가장 쉽다.

```bash
# 1) 로그인 → 쿠키 저장
curl -c cookies.txt -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@demo.io","password":"Demo1234!"}'

# 2) 내 프로젝트 목록 (project_id 확보)
curl -b cookies.txt http://localhost:8000/projects

# 3) 로그 등록 (201, id 확보)
curl -b cookies.txt -X POST http://localhost:8000/projects/<PID>/logs \
  -H "Content-Type: application/json" \
  -d '{"source":"gateway","message":"Request timed out after 30s","level":"ERROR"}'

# 4) 분석 실행
curl -b cookies.txt -X POST http://localhost:8000/projects/<PID>/analysis \
  -H "Content-Type: application/json" \
  -d '{"log_ids":["<LOG_UUID>"],"strategy":"rule"}'
```

> 인증 없이 룰만 빠르게 확인하려면 `POST /analysis/test` (`{"messages":[...], "strategy":"rule"}`) 사용.

### 2-D. 에이전트 (옵션)
```powershell
cd backend\netscope-agent
python netscope-agent.py --path ..\..\test-log\shell.log --source demo --tenant <uuid> --project <uuid>
```
> ⚠️ 현재 에이전트의 `API_URL` 이 legacy `/logs` 라 그대로는 동작하지 않음 — `/ingest` 로 전환 + 인증/헤더 정합 필요 (P0).

---

## 3. 실행 시나리오

| 목적 | 띄울 것 | 메모 |
| --- | --- | --- |
| **프론트만 작업** | 백엔드 + 프론트 | 에이전트 없이 LogForm으로 수동 입력 |
| **룰 엔진 튜닝** | 백엔드 + `validation/distribution.py` | UI 없이 60개 시나리오로 회귀 |
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
├── docker-compose.yml                 ← postgres + backend + frontend
├── backend/
│   ├── src/
│   │   ├── main.py                    ← FastAPI 부트 (라우터 7개 등록)
│   │   ├── api/v1/                    ← 라우터 (auth/projects/logs/analysis/reports/ingest/test/dep)
│   │   ├── core/                      ← config(Settings) · jwt · security(argon2) · logging(스텁)
│   │   ├── db/                        ← session/get_db · init(create_all) · base
│   │   ├── domain/                    ← ⭐ 쓰기/도메인 로직 (auth/log/project)
│   │   ├── ingest/                    ← ingest hot path (service→aggregator→signals→persist)
│   │   ├── analysis/                  ← ⭐ 룰 엔진 + GPT + weekly + validation
│   │   ├── schemas/                   ← Pydantic DTO + Enum
│   │   ├── model/                     ← SQLAlchemy ORM (✅ 전부 연결됨)
│   │   └── repositories/              ← project_repository 등
│   ├── scripts/seed.py                ← 데모 시드 (--reset)
│   ├── netscope-agent/                ← 단일 스크립트 collector
│   ├── tests/                         ← pytest (현재 비어있음)
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
- `backend/tests/test_health.py` 본문 비어있음. 회귀 방어 사실상 0.
- `analysis/validation/` 60개 시나리오 — pytest 미통합 (standalone 실행만).

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

실제 정의는 `backend/src/core/config.py` 의 `Settings`.

| 변수 | 사용처 | 기본 | 설명 |
| --- | --- | --- | --- |
| `SECRET_KEY` | backend | **(필수, 기본 없음)** | JWT 서명 키. 미설정 시 부팅 실패 |
| `DATABASE_URL` | backend | `None` | `postgresql+psycopg://...` — 없으면 DB 라우트 동작 안 함 |
| `OPENAI_API_KEY` | backend | `None` | 채우면 `strategy=gpt` 활성(구조화 보고서 `report_sections`). 비우면 룰만 폴백 |
| `INGEST_API_KEY` | backend | `None` | 채우면 `/ingest`가 `X-API-Key` 헤더 요구(에이전트 인증). 비우면 미적용 |
| `APP_ENV` | backend | `local` | `local \| prod` (`is_prod` 분기) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | backend | `60` | access 토큰/쿠키 TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | backend | `14` | refresh 토큰/쿠키 TTL |
| `FRONTEND_ORIGIN` | backend | `http://localhost:3000` | **CORS 오리진(콤마 구분 복수 가능)** → `settings.cors_origins` |
| `COOKIE_SECURE` | backend | `False` | 운영 HTTPS 에서 `True` 로 |
| `COOKIE_SAMESITE` | backend | `lax` | 쿠키 SameSite |
| `NEXT_PUBLIC_API_BASE_URL` | frontend | `http://localhost:8000` | API 위치 (SSE EventSource도 이 베이스 사용) |
| `NETSCOPE_API_URL` / `_API_KEY` / `_OFFSET_DIR` | agent | — | 에이전트 ingest URL · X-API-Key · 오프셋 디렉터리 |

---

## 9. 자주 막히는 곳

### 9-1. "분석 결과가 항상 LOW로 나옴"
- 입력 로그가 `INFO` 만 있거나 룰 매칭 안 됨. `RULE_ENGINE.md` §11 시뮬레이션 표 확인.
- `level=ERROR` 와 메시지에 `timeout` 포함된 로그 2개 이상 넣어 보기.

### 9-2. "GPT 선택했는데 결과가 룰만 나옴"
- `OPENAI_API_KEY` 미설정/빈값 → 조용한 폴백. 응답 `strategy_used` 가 `gpt` 인지 확인.
- ⚠️ env_file은 컨테이너 **생성 시점**에 읽힘 — `.env.docker`에 키를 채웠으면 `docker compose up -d --force-recreate backend` 로 재주입(단순 restart는 안 됨).
- 정상 동작 시 응답에 `report_sections`(상세 보고서 본문)가 채워짐. 모델: `gpt-4o-mini`.

### 9-2b. "실시간(SSE)이 안 들어옴"
- 백엔드 로그에 `GET /events/stream 200` 이 있는지 확인 — 없으면 브라우저가 **옛 JS**(하드 리프레시 Ctrl+Shift+R 필요) 또는 미로그인.
- 이벤트는 **연결 이후** 발생분만 푸시(historical X). `/ingest`가 200인데 `matched_rules`가 비면 분석 저장 안 됨 → `analysis` 이벤트 없음.
- 보고 있는 화면이 **이벤트의 project_id와 같은 프로젝트**인지(프로젝트 페이지는 자기 프로젝트만 반응).

### 9-3. "프론트가 API에 못 붙음"
- 백엔드 CORS 는 `FRONTEND_ORIGIN` **단일 오리진**만 허용(+`allow_credentials`). 프론트 주소가 기본 `http://localhost:3000` 가 아니면 `FRONTEND_ORIGIN` 을 맞춰야 함.
- 그래도 안 되면: `NEXT_PUBLIC_API_BASE_URL` 정확한지 / 백엔드 `--port 8000` 인지 / 네트워크 탭에서 실제 요청 URL·쿠키 전송(`withCredentials`) 확인.
- 401 무한루프면 쿠키 미발급(로그인 안 됨) 또는 `samesite`/`secure` 설정 의심.

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

### 10-2. 룰 엔진만 단독 실행
- 가장 쉬운 길: `POST /analysis/test` 에 `{"messages": ["[ERROR] Request timed out", "502 Bad Gateway"], "strategy": "rule"}` 전송 → DB·인증 없이 룰 결과만 반환.
- 코드 레벨: `AnalysisEngine().analyze_test(messages=[...], strategy="rule")`. 룰 엔진은 ORM `Log` 가 아니라 `RuleLog`(frozen dataclass) 를 받는다 — `engine.py` 가 변환을 담당.

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
# 백엔드 hot reload (필수 env)
$env:SECRET_KEY="dev-secret"; $env:DATABASE_URL="postgresql+psycopg://netscope:netscope_dev_pw@localhost:5432/netscope"; uvicorn src.main:app --reload --port 8000

# 룰 회귀 (60개 시나리오)
python -m src.analysis.validation.distribution

# 데모 시드 재실행
python -m scripts.seed --reset

# 프론트 빌드 검증 (배포 전)
npm run build && npm run start

# 의존성 업데이트 점검
pip list --outdated
npm outdated
```
