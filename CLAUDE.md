# 🔭 Netscope-AI — 에이전트 작업 가이드 (CLAUDE.md)

> **이 파일은 Claude/기여자가 코드를 만질 때 보는 작업용 요약본**입니다.
> 아키텍처 다이어그램·API 페이로드·룰 카탈로그·데이터 모델 등 **상세 레퍼런스는 → [`README.md`](./README.md)** 와 `docs/` 를 보세요.

```
NETSCOPE-AI · Explainable Log Diagnostics
Stage : MVP+  (Auth · DB · Multi-tenant · Weekly Report 가동)
Stack : FastAPI · SQLAlchemy · Postgres 16 · Next.js 16 · React 19 · Tailwind 4 · zustand
Theme : "왜 그렇게 판단했는가" 를 룰 ID + 근거 + 점수로 노출
```

---

## 🗺️ 1. 지금 무엇이 되고 무엇이 안 되나 (작업 전 필독)

```
🟢 DONE      Rule Engine(R001~R018) · Auth(쿠키+rotation+reuse탐지) · Postgres 영속화
             Multi-tenancy · Projects CRUD · Analysis API · Reports(list/trend/weekly)
             Ingest 파이프라인 · Docker Compose · Seed 스크립트
🟡 PARTIAL   Frontend(대시보드 미완) · Severity 매핑(CRITICAL 미사용) · Strategy(rule/gpt만)
🚧 깨짐/스텁  /projects/overview(프론트 호출 O, 백엔드 X→404) · netscope-agent(POST /logs legacy)
             GPT 모델명 `gpt-4.1-mini` (의도 확인 필요)
❌ 없음       /health · 테스트(회귀 방어 0) · Alembic · 룰 학습(L0~L4)
```

> ⚠️ **코드를 고치기 전에**: 위에서 건드리는 영역이 🚧/❌ 면, "원래 동작했는데 내가 깼다" 가 아니라 "원래 미완" 일 가능성이 높다. README 의 상태표를 함께 확인.

---

## 📁 2. 어디에 무엇이 있나 (디렉터리 맵)

```
backend/src/
├── main.py                 FastAPI 부트 · CORS(FRONTEND_ORIGIN) · 라우터 7개 등록
├── api/v1/
│   ├── dep.py              get_current_context — 쿠키 JWT → {user_id, tenant_id}  ★모든 보호 라우트가 의존
│   ├── auth.py             /auth/{register,login,refresh,logout}
│   ├── projects.py         /projects (list/create/delete)
│   ├── logs.py             /projects/{id}/logs
│   ├── analysis.py         /projects/{id}/analysis  (저장 + weekly 트리거)
│   ├── reports.py          /projects/{id}/reports/{,weekly,trend/confidence,{id}}
│   ├── ingest.py           /ingest  (헤더로 tenant/project, raw 비저장)
│   ├── test.py             /analysis/test  (DB 없이 룰만)
│   └── health.py           ❌ 비어있음 (미등록)
├── core/                   config.py · jwt.py · security.py(argon2) · logging.py(스텁)
├── db/                     base · session(get_db) · deps(중복 get_db — 정리후보) · init(create_all, Alembic X)
├── domain/                 auth · log · project  ← ★쓰기/도메인 로직은 여기로 위임 (모범 사례)
├── ingest/                 service → aggregator → signals → persist (hot path, raw 비보존)
├── analysis/
│   ├── engine.py           오케스트레이션 (Rule → GPT → severity → DTO). ★ORM 모름 (RuleLog dataclass만 받음)
│   ├── rule_engine.py      R001~R018 + interaction_bonus + aggregate()
│   ├── gpt_analyzer.py     단건 GPT 보강 (모델 gpt-4.1-mini ⚠️)
│   ├── gpt_weekly.py · weekly_service.py    주간 요약/리스크
│   └── validation/         test_cases.py(50) · distribution.py
├── model/                  User · Tenant · refresh_token · Project · log · analysis_result · weekly_report
├── schemas/                enums.py(LogLevel·SeverityLevel·AnalysisStrategy) · auth · project · log · analysis · ingest
└── scripts/seed.py         3 tenants × 2 projects × 18 logs (--reset 로 drop+recreate)

frontend/src/
├── app/                    page(redirect) · auth/{login,register} · projects/[id]/{,reports,components}
├── lib/api/client.ts       ★axios: withCredentials + 401 silent-refresh interceptor
├── lib/api/                auth · project · log · analysis · report · overview(🚧 백엔드 없음)
├── lib/store/authStore.ts  zustand: hydrated 플래그만 (쿠키는 JS 접근 불가)
├── types/{analysis,log}.ts ⚠️ Severity = LOW|MED|HIGH (CRITICAL 누락)
└── styles/severity.ts      ⚠️ 비어있음 → severity→color 정본으로 채울 자리
```

---

## 🧭 3. 작업 컨벤션 (지키지 않으면 머지 보류)

- **언어** — 코드 주석/식별자는 영어, 도메인 문서/기획서는 한국어 가능. 라우터의 한국어 주석은 유지.
- **레이어 경계**
  - 라우터에서 **읽기 query 직접 허용** (분석/리포트 라우터가 그렇게 함).
  - **쓰기/도메인 로직은 `domain/*DomainService` 로 위임** (auth/log/project 가 모범).
  - `analysis/engine.py` 는 **ORM 을 모른다** — `RuleLog`(frozen dataclass) 만 받는다. 여기에 ORM import 하지 말 것.
- **Tenant 강제** — 보호 라우트는 항상 `Depends(get_current_context)` → `ctx["tenant_id"]`(+`project_id`) 로 query 필터. cross-tenant 접근 차단이 보안의 핵심.
- **룰 추가 시** ①`rule_engine.py::default_rules()` 에 `Rule(...)` ②필요 시 `interaction_bonus()` 조합 ③`validation/test_cases.py` 양/음성 케이스 ④`distribution.py` 로 분포 회귀 확인.
- **DTO 변경 시** — `backend/src/schemas/*` 와 `frontend/src/types/*` **양쪽 동기화 필수** (특히 Severity / Strategy).
- **GPT enrichment** — system prompt 의 *"rule-engine analysis is the baseline. Do NOT contradict rules…"* 문구는 **유지**. 빼면 결정성/재현성 깨짐.
- **Agent** — stdlib + `requests` 만. 의존성 추가 신중.
- **DB 스키마 변경** — Alembic 도입 전에는 `seed.py --reset` 으로 drop+recreate. 운영 마이그는 직접 SQL.

---

## 🎨 4. UI / 보고서 시각화 원칙 ⭐ 필수 요구사항

> **사용자가 보는 모든 보고서 화면(분석 결과·주간 리포트·프로젝트 상세)은 시각적으로 강하게 표현**한다.
> 텍스트 나열만으로는 "보고서답지 않다". 새 보고서/대시보드 컴포넌트가 아래 체크리스트 절반 이상 ❌면 **머지 보류**.

| 카테고리 | 요구사항 |
| --- | --- |
| **Severity 색상** | LOW=blue/cyan · MEDIUM=amber/yellow · HIGH=red/rose · (CRITICAL=magenta) — 배지 + 카드 border + 좌측 컬러 바 동시 |
| **Confidence** | 숫자만 X — 게이지/도넛/그라데이션. `0.85` 보다 `█████████░ 85%` |
| **Matched Rules** | 리스트 X — 룰 ID 칩 + 점수 + 근거 expand, 카테고리별 색상 |
| **Trend** | `/reports/trend/confidence` → 라인/에어리어 차트 + 임계선(0.45 / 0.75) |
| **Weekly Report** | 헤더에 기간 + report_count + risk_outlook 색상 그라데이션 배경 |
| **Causes / Actions** | 불릿 X — 아이콘(🩺 원인 / 🛠 조치) + 카드 grid, 길면 collapse |
| **Empty / Loading** | 평문 X — 일러스트/아이콘 + CTA 버튼 |
| **다크 테마** | `zinc-950` 배경 위에서 색이 살아야 함 — Tailwind `*-400`/`*-500` 톤 |

```
❌ 안티패턴: "severity: HIGH, confidence: 0.82" key:value 평문 · matched_rules 를 <ul><li> 텍스트로만
            · 회색조만 사용 · 차트 없는 trend · 한 컬럼에 모든 정보 세로 쌓기
```

권장: 차트 `recharts`/`tremor` · 아이콘 `lucide-react` · 모션 `framer-motion` · **컬러 매핑은 `frontend/src/styles/severity.ts` 에 정본 통일** (컴포넌트 하드코딩 금지). 상세 → [`docs/DESIGN_SYSTEM.md`](./docs/DESIGN_SYSTEM.md).

---

## 🚀 5. 자주 쓰는 명령어

```bash
# 전체 스택 (postgres + backend + frontend, hot reload)
docker compose up -d --build

# 데모 데이터 시드  (alice/bob/carol @demo.io · PW Demo1234!)
docker compose exec backend python -m scripts.seed --reset

# 룰 분포 회귀 확인 (룰 변경 후 필수)
docker compose exec backend python -m src.analysis.validation.distribution
```

로컬 수동 실행·Postgres 접속·데모 계정 상세 → [`README.md`](./README.md) 의 "실행 / 배포".

---

## 🚨 6. 손대기 전 알아둘 갭 (우선순위)

```
P0  Agent↔/ingest 정합 (URL+인증) · /projects/overview 404 · /health 없음 · 테스트 0 · GPT 모델명 확인
P1  Alembic 도입 · Frontend Severity 타입 CRITICAL 누락 · Strategy ai/hybrid · CORS 다환경
P2  Agent Resume(오프셋) · 7일 리텐션 job · 구조화 파서
P3  룰 학습 L0~L4 (docs/RULE_LEARNING.md 기획만 존재)
```

상세 영향/액션 표와 로드맵 → [`README.md`](./README.md) 의 "알려진 갭 / 로드맵".

---

```
─── netscope-ai · CLAUDE.md (agent guide) · last sync 2026-05-29 ───
상세 정본은 README.md + docs/ 를 신뢰. 이 파일은 빠른 작업 컨텍스트용.
```
