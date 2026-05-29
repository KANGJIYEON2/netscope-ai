# 🔭 Netscope-AI — 에이전트 작업 가이드 (CLAUDE.md)

> **이 파일은 Claude/기여자가 코드를 만질 때 보는 작업용 요약본**입니다.
> 아키텍처 다이어그램·API 페이로드·룰 카탈로그·데이터 모델 등 **상세 레퍼런스는 → [`README.md`](./README.md)** 와 `docs/` 를 보세요.

```
NETSCOPE-AI · Explainable Log Diagnostics
Stage : MVP++  (Auth · DB · Multi-tenant · Weekly Report · Rule Learning L0~L4 가동)
Stack : FastAPI · SQLAlchemy · Postgres 16 · Next.js 16 · React 19 · Tailwind 4 · zustand
Theme : "왜 그렇게 판단했는가" 를 룰 ID + 학습 패턴 + 근거 + 점수로 노출
```

---

## 🗺️ 1. 지금 무엇이 되고 무엇이 안 되나 (작업 전 필독)

```
🟢 DONE      Rule Engine v3.0 (R001~R024) · Auth(쿠키+rotation+reuse탐지) · Postgres 영속화
             Multi-tenancy · Projects CRUD · Analysis API · Reports(list/trend/weekly)
             Ingest 파이프라인 · Docker Compose · Seed 스크립트
             /health 엔드포인트 · /projects/overview API
             Agent↔/ingest 정합 (배치 전송) · Agent Resume (오프셋 영속화)
             GPT 모델명 수정 (gpt-4o-mini) · 7일 리텐션 job
             구조화 파서 (JSON/KV/syslog/plain) · Alembic 초기 설정
             Frontend Severity CRITICAL + Strategy ai/hybrid 타입 동기화
             severity.ts 컬러 매핑 정본 · CORS 다환경 (콤마 구분)
             Rule Learning L0~L4 (Drain 마이닝 · 카탈로그 · 패턴 매칭 · 피드백 · 가중치 학습)
             테스트 43개 (health/overview/rule engine/parser/learning)
🟡 PARTIAL   Frontend(대시보드 미완) · 패턴 관리 UI(/patterns 페이지 미구현)
❌ 없음       프론트엔드 패턴 알림 카드 · 임베딩 기반 의미 유사도(L5)
```

> ⚠️ **코드를 고치기 전에**: 위에서 건드리는 영역이 🟡/❌ 면, "원래 동작했는데 내가 깼다" 가 아니라 "원래 미완" 일 가능성이 높다. README 의 상태표를 함께 확인.

---

## 📁 2. 어디에 무엇이 있나 (디렉터리 맵)

```
backend/src/
├── main.py                 FastAPI 부트 · CORS(cors_origins) · 라우터 10개 등록
├── api/v1/
│   ├── dep.py              get_current_context — 쿠키 JWT → {user_id, tenant_id}  ★모든 보호 라우트가 의존
│   ├── auth.py             /auth/{register,login,refresh,logout}
│   ├── projects.py         /projects (list/create/overview/delete)
│   ├── logs.py             /projects/{id}/logs
│   ├── analysis.py         /projects/{id}/analysis  (저장 + weekly 트리거 + 패턴 매칭)
│   ├── reports.py          /projects/{id}/reports/{,weekly,trend/confidence,{id}}
│   ├── ingest.py           /ingest  (헤더로 tenant/project, raw 비저장, 패턴 마이닝 연동)
│   ├── patterns.py         /patterns (list/detail/label/dismiss/feedback) ← L1~L3
│   ├── test.py             /analysis/test  (DB 없이 룰만)
│   └── health.py           /health (DB ping + liveness)
├── core/                   config.py(cors_origins 프로퍼티) · jwt.py · security.py(argon2) · logging.py
├── db/                     base · session(get_db) · deps · init(create_all)
├── domain/                 auth · log · project  ← ★쓰기/도메인 로직은 여기로 위임 (모범 사례)
├── ingest/
│   ├── service.py          ingest_logs (룰 + 패턴 마이닝 연동)
│   ├── parser.py           구조화 파서 (JSON/KV/syslog/plain 자동감지)
│   ├── aggregator.py       SignalAggregator
│   ├── signals.py          extract_signals
│   └── persist.py          persist_analysis
├── analysis/
│   ├── engine.py           오케스트레이션 (Rule → GPT → severity 자동 매핑 → DTO). ★ORM 모름
│   ├── rule_engine.py      R001~R024 v3.0 + interaction_bonus(13개) + 시간/통계 헬퍼
│   ├── gpt_analyzer.py     단건 GPT 보강 (모델 gpt-4o-mini)
│   ├── gpt_weekly.py · weekly_service.py    주간 요약/리스크
│   └── validation/         test_cases.py(60) · distribution.py
├── learning/               ★ Rule Learning L0~L4
│   ├── masking.py          변수 마스킹 (UUID/IP/TS/PATH/B64/NUM 등)
│   ├── drain.py            Drain 트리 (온라인 로그 템플릿 추출)
│   ├── catalog.py          카탈로그 upsert (DB 영속화)
│   ├── matcher.py          패턴 매칭 (분석 시 카탈로그 조회)
│   ├── promotion.py        자동 승격/강등 (confirm/dismiss 비율)
│   └── weight_learner.py   온라인 score_adjust (안전 가드 포함)
├── model/                  User · Tenant · refresh_token · Project · log · analysis_result
│                           · weekly_report · pattern · pattern_feedback
├── schemas/                enums.py(LogLevel·SeverityLevel·AnalysisStrategy) · auth · project
│                           · log · analysis(matched_patterns 포함) · ingest
├── scripts/
│   ├── seed.py             3 tenants × 2 projects × 18 logs (--reset)
│   └── retention.py        7일 리텐션 cleanup (--days N --dry-run)
└── alembic/                Alembic 초기 설정 (env.py에 전 모델 import)

frontend/src/
├── app/                    page(redirect) · auth/{login,register} · projects/[id]/{,reports,components}
├── lib/api/client.ts       ★axios: withCredentials + 401 silent-refresh interceptor
├── lib/api/                auth · project · log · analysis · report · overview
├── lib/store/authStore.ts  zustand: hydrated 플래그만 (쿠키는 JS 접근 불가)
├── types/{analysis,log}.ts Severity = LOW|MED|HIGH|CRITICAL · Strategy = rule|gpt|ai|hybrid
└── styles/severity.ts      ★severity→color 정본 (cyan/amber/red/fuchsia, 다크테마)

backend/netscope-agent/
└── netscope-agent.py       POST /ingest 배치 전송 · 오프셋 영속화 · 로그 회전 감지
```

---

## 🧭 3. 작업 컨벤션 (지키지 않으면 머지 보류)

- **언어** — 코드 주석/식별자는 영어, 도메인 문서/기획서는 한국어 가능. 라우터의 한국어 주석은 유지.
- **레이어 경계**
  - 라우터에서 **읽기 query 직접 허용** (분석/리포트 라우터가 그렇게 함).
  - **쓰기/도메인 로직은 `domain/*DomainService` 로 위임** (auth/log/project 가 모범).
  - `analysis/engine.py` 는 **ORM 을 모른다** — `RuleLog`(frozen dataclass) 만 받는다. 여기에 ORM import 하지 말 것.
  - 패턴 매칭(L2)은 **라우터(analysis.py)에서** DB 조회 후 결과를 합침 — engine.py 에 ORM 넣지 않기 위함.
- **Tenant 강제** — 보호 라우트는 항상 `Depends(get_current_context)` → `ctx["tenant_id"]`(+`project_id`) 로 query 필터. cross-tenant 접근 차단이 보안의 핵심.
- **룰 추가 시** ①`rule_engine.py::default_rules()` 에 `Rule(...)` ②필요 시 `interaction_bonus()` 조합 ③`validation/test_cases.py` 양/음성 케이스 ④`tests/test_rule_engine.py` 에 테스트 추가 ⑤`distribution.py` 로 분포 회귀 확인.
- **DTO 변경 시** — `backend/src/schemas/*` 와 `frontend/src/types/*` **양쪽 동기화 필수** (특히 Severity / Strategy).
- **GPT enrichment** — system prompt 의 *"rule-engine analysis is the baseline. Do NOT contradict rules…"* 문구는 **유지**. 빼면 결정성/재현성 깨짐.
- **Agent** — stdlib + `requests` 만. 의존성 추가 신중.
- **DB 스키마 변경** — Alembic 설정 완료. `alembic revision --autogenerate -m "description"` → `alembic upgrade head`.
- **패턴 학습 안전 가드** — score_seed 상한 0.30, score_adjust |절대값| ≤ 0.10, 테넌트별 분리 필수.

---

## 🎨 4. UI / 보고서 시각화 원칙 ⭐ 필수 요구사항

> **사용자가 보는 모든 보고서 화면(분석 결과·주간 리포트·프로젝트 상세)은 시각적으로 강하게 표현**한다.
> 텍스트 나열만으로는 "보고서답지 않다". 새 보고서/대시보드 컴포넌트가 아래 체크리스트 절반 이상 ❌면 **머지 보류**.

| 카테고리 | 요구사항 |
| --- | --- |
| **Severity 색상** | LOW=cyan · MEDIUM=amber · HIGH=red · CRITICAL=fuchsia — 배지 + 카드 border + 좌측 컬러 바 동시 |
| **Confidence** | 숫자만 X — 게이지/도넛/그라데이션. `0.85` 보다 `█████████░ 85%` |
| **Matched Rules** | 리스트 X — 룰 ID 칩 + 점수 + 근거 expand, 카테고리별 색상 |
| **Matched Patterns** | `🆕 learned` 배지 + 패턴 이력(빈도·평균 severity) 표시 |
| **Trend** | `/reports/trend/confidence` → 라인/에어리어 차트 + 임계선(0.45 / 0.75) |
| **Weekly Report** | 헤더에 기간 + report_count + risk_outlook 색상 그라데이션 배경 |
| **Causes / Actions** | 불릿 X — 아이콘 + 카드 grid, 길면 collapse |
| **Empty / Loading** | 평문 X — 일러스트/아이콘 + CTA 버튼 |
| **다크 테마** | `zinc-950` 배경 위에서 색이 살아야 함 — Tailwind `*-400`/`*-500` 톤 |

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

# 테스트 실행 (43개)
cd backend && .venv/Scripts/python -m pytest tests/ -v

# 7일 리텐션 cleanup (dry-run 먼저)
docker compose exec backend python -m scripts.retention --dry-run
docker compose exec backend python -m scripts.retention

# Alembic 마이그레이션
cd backend && alembic revision --autogenerate -m "description"
cd backend && alembic upgrade head
```

로컬 수동 실행·Postgres 접속·데모 계정 상세 → [`README.md`](./README.md) 의 "실행 / 배포".

---

## 🧠 6. Rule Engine v3.0 요약

```
R001~R018  키워드 매칭 기반 (v2.0 계승)
R019       에러 버스트 (1분 내 ERROR 5건+)
R020       타임아웃 → 크래시 연쇄 (시간 순서 패턴)
R021       높은 에러율 (ERROR/전체 ≥ 50%, 5건+)
R022       다중 source 동시 에러 (3개+ source)
R023       로그 급증 스파이크 (평균 대비 3배+)
R024       연결실패 → 서비스 재시작 연쇄

interaction_bonus: 13개 조합 (기존 7 + 신규 6)

Severity 자동 매핑:
  CRITICAL = 치명적 룰 조합 (R020+R007, R019+R022, R024+R022) 또는 0.85+ & 5개+ 룰
  HIGH     = confidence ≥ 0.75 또는 크래시/OOM/연쇄크래시 단독
  MEDIUM   = confidence ≥ 0.45
  LOW      = confidence < 0.45
```

---

## 🔬 7. Rule Learning (L0~L4) 요약

```
L0  Drain 패턴 마이닝 — ingest 시 백그라운드로 변수 마스킹 → Drain 트리 → 카탈로그 DB 적재
L1  패턴 관리 API — GET /patterns · PATCH label/dismiss
L2  분석 통합 — PatternMatcher가 분석 시 카탈로그 조회, matched_patterns를 결과에 포함
L3  자동 승격 — confirm 5회+ & dismiss < 20% → promoted, 역전 시 강등
L4  가중치 학습 — confirm +0.01, dismiss -0.01, wrong -0.02, |adjust| ≤ 0.10, same-user 감쇠

패턴 상태: candidate → labeled → promoted (→ dismissed)
룰 ID: 시스템 R001~, 학습 L001~ (향후)
안전 가드: score_seed ≤ 0.30, score_adjust ≤ |0.10|, 테넌트 격리
```

상세 기획 → [`docs/RULE_LEARNING.md`](./docs/RULE_LEARNING.md)

---

## 🚧 8. 남은 작업 (우선순위)

```
🟡  프론트엔드 대시보드 완성 (분석 결과 시각화, 패턴 알림 카드, /patterns 페이지)
🟡  Agent 환경변수화 (API_URL, OFFSET_DIR)
🟡  임베딩 기반 의미 유사도 (L5 — sentence-transformer + HDBSCAN)
🟡  Alembic initial revision (DB 연결 필요)
🟡  통합 테스트 (auth + analysis e2e)
```

---

```
─── netscope-ai · CLAUDE.md (agent guide) · last sync 2026-05-30 ───
상세 정본은 README.md + docs/ 를 신뢰. 이 파일은 빠른 작업 컨텍스트용.
```
