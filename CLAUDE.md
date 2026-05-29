# 🔭 Netscope-AI — 프로젝트 컨텍스트 (CLAUDE.md)

```
╔══════════════════════════════════════════════════════════════════════════════╗
║   NETSCOPE-AI                                                                ║
║   Explainable Network/Application Log Diagnostics                            ║
║                                                                              ║
║   Stage  : MVP+  (Auth · DB · Multi-tenant · Weekly Report 까지 가동)         ║
║   Stack  : FastAPI · SQLAlchemy · Postgres · Next.js 16 · Tailwind 4         ║
║   Theme  : "왜 그렇게 판단했는가" 를 룰 ID + 근거 + 점수로 노출                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

> **한 줄 요약**: 로그 묶음을 **Rule Engine (R001~R018) + 선택적 GPT 보강** 으로 분석해,
> 매칭된 룰 ID·근거·신뢰도·심각도까지 함께 응답하는 **설명 가능한** 진단 시스템.
> 현재는 **인증·DB·멀티테넌시·주간 리포트** 까지 실제 동작. 다음 단계는 **인시던트 대시보드 UI · 룰 학습 파이프라인**.

> 📎 PM 고도화 기획안 → [`docs/PM_ENHANCEMENT_PLAN.md`](./docs/PM_ENHANCEMENT_PLAN.md)
> 📎 룰 학습 정본 → [`docs/RULE_LEARNING.md`](./docs/RULE_LEARNING.md)
> 📎 디자인 시스템 → [`docs/DESIGN_SYSTEM.md`](./docs/DESIGN_SYSTEM.md)

---

## 🗺️ 0. 상태 한눈에 보기

```
영역                상태      비고
──────────────────────────────────────────────────────────────────────
🟢 Rule Engine      DONE      R001~R018, 상호작용 보너스, 검증셋 50개
🟢 Auth             DONE      httpOnly 쿠키 + Refresh Rotation + Reuse 탐지
🟢 DB 영속화        DONE      Postgres + SQLAlchemy + create_all 초기화
🟢 Multi-tenancy    DONE      JWT(sub, tenant_id) → 모든 라우터에서 tenant 강제
🟢 Projects         DONE      tenant 단위 CRUD, 프로젝트 단위 라우팅
🟢 Analysis API     DONE      /projects/{id}/analysis + signals + matched_rules
🟢 Reports API      DONE      list/trend/weekly + GPT 주간 요약 + 리스크 예측
🟢 Ingest Pipeline  DONE      raw 로그 → 룰 → aggregator → analysis_results
🟢 Docker Compose   DONE      postgres + backend + frontend (hot reload)
🟢 Seed Script      DONE      3 tenants × 2 projects × 18 logs, demo 시연용
🟡 Frontend Routes  PARTIAL   /auth, /projects, reports 동작 — 대시보드 미완성
🟡 Severity Mapping PARTIAL   백엔드 CRITICAL 정의됐으나 매핑 미사용 (LOW/MED/HIGH만)
🟡 Strategy         PARTIAL   rule / gpt 만 동작 — ai / hybrid 미구현
🚧 /projects/overview  STUB   프론트가 호출하지만 백엔드 라우트 없음 (404)
🚧 GPT 모델명       LEGACY    `gpt-4.1-mini` — 의도가 `gpt-4o-mini`라면 정정 필요
🚧 netscope-agent   BROKEN    `POST /logs` 호출 → 현재 라우트는 /projects/{id}/logs (auth 필요)
❌ /health 엔드포인트  NONE   main.py 등록 없음, health.py 비어있음
❌ 테스트            NONE     test_health.py 본문 비어 있음, 회귀 방어 부재
❌ Alembic 마이그레이션 NONE   create_all 만 사용 — 스키마 변경 시 drop+recreate 필요
❌ 룰 학습 (L0~L4)  미착수   기획서만 존재
```

> **범례** — 🟢 동작 · 🟡 일부 동작 · 🚧 부분 구현 / 깨짐 · ❌ 미구현

---

## 🏛️ 1. 시스템 아키텍처

### 1-1. 전체 토폴로지

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  📡  Application / OS Logs  (stdout, stderr, syslog, *.log)                       │
└──────────────────────────────┬──────────────────────────────────────────────────┘
                               │  tail -f (1s polling)
                               ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  🤖  NETSCOPE AGENT   (backend/netscope-agent/netscope-agent.py)                 │
│    · BOM/제어문자 정리 · level 자동 감지 (ERROR/WARN/INFO/DEBUG)                  │
│    · Agent-side filter v0: ERROR / WARN / TIMEOUT / 5xx 만 통과                  │
│    · X-Tenant-ID / X-Project-ID 헤더 부착                                        │
│    ⚠ 현재 POST URL이 `/logs` (legacy) — 백엔드는 `/projects/{id}/logs` 로 이전됨  │
└──────────────────────────────┬──────────────────────────────────────────────────┘
                               │ HTTP JSON  (+headers)
                               ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  🛡️  BACKEND  (FastAPI · backend/src · port 8000)                                │
│                                                                                 │
│   ┌──────────────────┐  cookie:access_token  ┌─────────────────────────────┐    │
│   │ Auth Layer       │ ────────────────────▶ │ get_current_context (dep.py) │    │
│   │ /auth/{register, │                       │ → {user_id, tenant_id}       │    │
│   │  login, refresh, │                       └────────┬────────────────────┘    │
│   │  logout}         │                                │ 모든 라우터에 주입         │
│   └──────────────────┘                                ▼                          │
│                                                                                 │
│   ┌────────────────────────────────────────────────────────────────────────┐    │
│   │  /projects/{project_id}/...   (tenant 자동 필터링)                      │    │
│   │                                                                        │    │
│   │  • POST   /logs              ← 수동 단건 입력 (LogDomainService)        │    │
│   │  • GET    /logs              ← 최근 200건 (tenant+project filter)       │    │
│   │  • POST   /analysis          ← log_ids → AnalysisEngine.analyze()      │    │
│   │  • GET    /reports           ← AnalysisResult 목록 (날짜 필터)           │    │
│   │  • GET    /reports/weekly    ← 7일 GPT 요약 + 다음주 리스크 예측         │    │
│   │  • GET    /reports/trend/confidence  ← 일자별 confidence 추이            │    │
│   └────────────────────────────────────────────────────────────────────────┘    │
│                                                                                 │
│   ┌──────────────────────────────────┐  ┌─────────────────────────────────┐     │
│   │  POST /ingest                    │  │  POST /analysis/test            │     │
│   │  (Agent / fluent-bit / 외부)      │  │  (DB 없이 룰만 돌리는 검증용)     │     │
│   │  X-Tenant-ID / X-Project-ID      │  └─────────────────────────────────┘     │
│   │  → RuleEngine.run_raw            │                                          │
│   │  → SignalAggregator              │                                          │
│   │  → persist_analysis (raw 보관 X) │                                          │
│   └──────────────────────────────────┘                                          │
│                                                                                 │
│                                                                                 │
│   ┌─── AnalysisEngine.analyze() ────────────────────────────────────────┐       │
│   │  ① RuleEngine (R001~R018)                                          │       │
│   │  ② (옵션) GPTAnalyzer  ← strategy=gpt 이고 OPENAI_API_KEY 있을 때    │       │
│   │  ③ severity = HIGH(≥0.75) | MEDIUM(≥0.45) | LOW(<0.45)              │       │
│   │  ④ 안정성 보호: causes/actions 비면 fallback 문구                     │       │
│   │  ⑤ AnalysisResult DB 저장 (tenant+project 강제)                      │       │
│   │  ⑥ 주간 리포트 자동 트리거: 최근 7일 ≥5건 + 미존재 → 생성              │       │
│   └────────────────────────────────────────────────────────────────────┘       │
└───────────────────────────────┬─────────────────────────────────────────────────┘
                                │  SQLAlchemy ORM
                                ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  🐘  POSTGRES 16   (docker-compose · postgres_data volume)                       │
│      tenants · users · refresh_tokens · projects                                │
│      logs · analysis_results · weekly_reports                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                ▲
                                │  axios (withCredentials, silent refresh)
                                │
┌─────────────────────────────────────────────────────────────────────────────────┐
│  🖼️  FRONTEND   (Next.js 16 · React 19 · Tailwind 4 · zustand · port 3000)       │
│                                                                                 │
│   /auth/{login, register}  →  서버 set-cookie (httpOnly, sameSite=lax)           │
│   /projects                →  tenant 별 프로젝트 카드                            │
│   /projects/[id]           →  프로젝트 상세 + NewLogModal + WeeklyReportCard      │
│   /projects/[id]/reports   →  분석 리포트 목록                                   │
│                                                                                 │
│   lib/api/client.ts  ← axios interceptor: 401 시 /auth/refresh 자동 재시도        │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 1-2. Auth 흐름 (시퀀스)

```
Client                  Frontend (axios)             Backend                 Postgres
  │                          │                          │                       │
  │  email/password          │                          │                       │
  ├─────────────────────────▶│                          │                       │
  │                          │  POST /auth/login        │                       │
  │                          ├─────────────────────────▶│                       │
  │                          │                          │  verify_password      │
  │                          │                          ├──────────────────────▶│
  │                          │                          │◀──────────────────────┤
  │                          │                          │  create_access_token  │
  │                          │                          │  create_refresh_token │
  │                          │                          │  INSERT refresh_token │
  │                          │                          ├──────────────────────▶│
  │                          │  Set-Cookie:             │                       │
  │                          │    access_token (httpOnly)                       │
  │                          │    refresh_token (httpOnly, path=/auth)          │
  │                          │◀─────────────────────────┤                       │
  │  302 → /projects         │                          │                       │
  │◀─────────────────────────┤                          │                       │
  │                          │                          │                       │
  │  GET /projects/{id}/...  │                          │                       │
  ├─────────────────────────▶│                          │                       │
  │                          │  Cookie: access_token    │                       │
  │                          ├─────────────────────────▶│                       │
  │                          │                          │ get_current_context   │
  │                          │                          │  {user_id, tenant_id} │
  │                          │  401 (expired)           │                       │
  │                          │◀─────────────────────────┤                       │
  │                          │  POST /auth/refresh ─────┼─▶  rotation logic     │
  │                          │  Set-Cookie: 새 토큰 2종   │   + reuse 탐지        │
  │                          │◀─────────────────────────┤                       │
  │                          │  원 요청 재시도            │                       │
  │                          ├─────────────────────────▶│                       │
  │                          │◀─────────────────────────┤                       │
```

### 1-3. 분석 파이프라인 (이벤트 흐름)

```
   logs[]                       AnalysisEngine
     │                                │
     ▼                                ▼
 ┌────────────┐  matches   ┌─────────────────┐
 │ RuleEngine │ ─────────▶ │   aggregate()    │
 │ R001..R018 │            │  base + bonus   │
 └────────────┘            └────────┬────────┘
                                    │
                ┌───────────────────┼───────────────────┐
                │                   │                   │
                ▼                   ▼                   ▼
        ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐
        │ strategy=gpt?│  │ severity     │  │ matched_rules[] │
        │  → GPTAnalyzer│  │ HIGH/MED/LOW │  │ signals[]       │
        └──────┬───────┘  └──────┬───────┘  └────────┬────────┘
               └─────────────────┴───────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │  AnalysisResultDTO     │
                    │  + DB INSERT           │
                    └──────────┬─────────────┘
                               │
                  ┌────────────┴────────────┐
                  │  ≥5 results in 7d &     │
                  │   no weekly report?     │
                  └────────────┬────────────┘
                               │ yes
                               ▼
                    ┌────────────────────────┐
                    │  GPT weekly summary    │
                    │  + risk_outlook        │
                    │  → weekly_reports INS  │
                    └────────────────────────┘
```

---

## 📁 2. 디렉터리 맵 (현재 코드 기준)

```
netscope-ai/
├── docker-compose.yml          🆕 postgres + backend + frontend
├── CLAUDE.md                   (이 파일)
│
├── backend/
│   ├── Dockerfile
│   ├── Dockerfile.local-backup ⚠️ 미추적 — 정리 필요 (.gitignore or 삭제)
│   ├── requirements.txt · pyproject.toml
│   │
│   ├── src/
│   │   ├── main.py             FastAPI 부트 · CORS(FRONTEND_ORIGIN) · 라우터 7개 등록
│   │   │
│   │   ├── api/v1/
│   │   │   ├── auth.py         🆕 /auth/{register,login,refresh,logout}
│   │   │   ├── projects.py     🆕 /projects (list/create/delete)
│   │   │   ├── logs.py         /projects/{id}/logs   (project-scoped)
│   │   │   ├── analysis.py     /projects/{id}/analysis (저장 + weekly trigger)
│   │   │   ├── reports.py      🆕 /projects/{id}/reports/{,weekly,trend/confidence,{id}}
│   │   │   ├── ingest.py       🆕 /ingest (헤더로 tenant/project, raw 보관 X)
│   │   │   ├── test.py         /analysis/test (DB 없이 룰만 검증)
│   │   │   ├── dep.py          🆕 get_current_context — 쿠키 JWT → {user, tenant}
│   │   │   └── health.py       ❌ 비어있음 (라우터 미등록)
│   │   │
│   │   ├── core/
│   │   │   ├── config.py       🆕 Settings(SECRET_KEY · COOKIE_* · FRONTEND_ORIGIN ·
│   │   │   │                       ACCESS/REFRESH 만료 · DATABASE_URL · OPENAI_API_KEY)
│   │   │   ├── jwt.py          🆕 create_access/refresh_token, decode_token
│   │   │   ├── security.py     🆕 argon2 hash + verify_password + refresh hash
│   │   │   └── logging.py      (스텁)
│   │   │
│   │   ├── db/                 🆕 Postgres 연동
│   │   │   ├── base.py         declarative_base
│   │   │   ├── session.py      engine + SessionLocal + get_db()
│   │   │   ├── deps.py         (중복 get_db — 정리 후보)
│   │   │   └── init.py         Base.metadata.create_all (Alembic 없음)
│   │   │
│   │   ├── domain/             🆕 도메인 서비스 계층
│   │   │   ├── auth.py         AuthDomainService — register/login/refresh/logout
│   │   │   │                   refresh rotation + reuse 탐지 + all-revoke
│   │   │   ├── log.py          LogDomainService.create_log
│   │   │   └── project.py      ProjectDomainService.list/create/delete
│   │   │
│   │   ├── ingest/             🆕 Ingest hot path (raw 로그 비보존)
│   │   │   ├── service.py      ingest_logs → run_raw → aggregator
│   │   │   ├── aggregator.py   SignalAggregator → extract_signals → persist
│   │   │   ├── signals.py      RuleMatch[] → signals (rule_id, score, count)
│   │   │   └── persist.py      analysis_results 직접 INSERT
│   │   │
│   │   ├── analysis/
│   │   │   ├── engine.py       오케스트레이션 (Rule → GPT → severity → DTO)
│   │   │   ├── rule_engine.py  R001~R018 + interaction bonus + aggregate()
│   │   │   ├── gpt_analyzer.py 단건 GPT 보강 (모델: gpt-4.1-mini ⚠️)
│   │   │   ├── gpt_weekly.py   🆕 주간 요약 + 다음주 리스크 예측
│   │   │   ├── weekly_service.py 🆕 should_generate / generate_and_save
│   │   │   ├── rule_summary.py · signal.py · signal_mapper.py
│   │   │   ├── result.py
│   │   │   └── validation/     test_cases.py(50개) · distribution.py
│   │   │
│   │   ├── model/              SQLAlchemy ORM  ✅ 모두 연결됨
│   │   │   ├── User.py         users (id, email, password_hash, tenant_id)
│   │   │   ├── Tenant.py       tenants (id, name)
│   │   │   ├── refresh_token.py 🆕 jti PK · token_hash · revoked · expires_at
│   │   │   ├── Project.py      projects (id, tenant_id, name)
│   │   │   ├── log.py          logs (+ tenant_id, project_id, source_type, host)
│   │   │   ├── analysis_result.py (+ tenant_id, project_id, signals JSONB)
│   │   │   └── weekly_report.py 🆕 weekly_reports (period, summary, risk_*)
│   │   │
│   │   ├── schemas/            Pydantic DTO + Enum
│   │   │   ├── enums.py        LogLevel · AnalysisStrategy · SeverityLevel(CRITICAL 포함)
│   │   │   ├── auth.py         🆕 RegisterRequest · LoginRequest
│   │   │   ├── project.py · log.py · analysis.py · analysis_test.py · ingest.py
│   │   │
│   │   ├── repositories/       project_repository · (analysis_repository — 부분 사용)
│   │   ├── infrastructure/     storage.py(InMemory — 현재는 미사용), database.py(스텁)
│   │   ├── log/                models.py(레거시 dataclass) · service.py · parser.py(스텁)
│   │   ├── utils/              hash.py · time.py
│   │   └── netscope/           main.py (보조 진입점)
│   │
│   ├── scripts/
│   │   └── seed.py             🆕 3 tenants × 2 projects × 18 logs + 사전 분석 결과
│   │
│   ├── netscope-agent/
│   │   └── netscope-agent.py   ⚠️ POST URL이 `/logs` → 백엔드 이전됨, 인증 누락
│   │
│   └── tests/
│       └── test_health.py      ❌ 본문 비어있음 (1 line)
│
└── frontend/
    ├── Dockerfile
    └── src/
        ├── app/
        │   ├── layout.tsx              dark theme (zinc-950)
        │   ├── page.tsx                쿠키 확인 후 /auth/login or /projects 로 redirect
        │   ├── auth/{login,register}/  🆕 폼 + axios + 서버 set-cookie
        │   ├── projects/               🆕 프로젝트 카드 + new
        │   │   ├── page.tsx
        │   │   ├── new/
        │   │   └── [projectId]/
        │   │       ├── page.tsx        프로젝트 상세
        │   │       ├── components/
        │   │       │   ├── NewLogModal.tsx
        │   │       │   └── WeeklyReportCard.tsx 🆕
        │   │       └── reports/        분석 리포트 페이지
        │   ├── components/
        │   │   ├── Layout/TopNav.tsx
        │   │   └── common/
        │   │       ├── LogoutButton.tsx
        │   │       └── SeverityBadge.tsx
        │   ├── analysis/ · logs/ · test-log/
        │   └── globals.css
        ├── lib/
        │   ├── api/
        │   │   ├── client.ts           🆕 withCredentials + 401 silent-refresh interceptor
        │   │   ├── auth.ts             login/register/refresh/logout
        │   │   ├── project.ts · log.ts · analysis.ts · report.ts
        │   │   └── overview.ts         🚧 /projects/overview 호출 — 백엔드 없음
        │   ├── store/authStore.ts      zustand: hydrated 플래그만 (쿠키는 JS 접근 불가)
        │   └── config.ts               API_BASE_URL (NEXT_PUBLIC_API_BASE_URL)
        ├── types/{analysis,log}.ts     ⚠️ Severity = LOW|MED|HIGH (CRITICAL 누락)
        └── styles/severity.ts          ⚠️ 비어있음 (색은 컴포넌트에 인라인)
```

> 🆕 = 이전 CLAUDE.md 이후 새로 등장 · ⚠️ = 주의 필요 · ❌ = 미완 / 비어있음

---

## 🧠 3. 핵심 가치 — Rule Engine (R001~R018, v2.0)

> 룰셋 버전 `v2.0`. 이전 문서의 R001~R006 에서 **+12 룰 확장**.

### 3-1. 룰 카탈로그

| 룰 ID | 점수 | 제목 | 트리거 키워드/조건 |
| :---: | :---: | --- | --- |
| **R001** | 0.35 | Timeout 발생 | `timeout`, `timed out`, `ETIMEDOUT` |
| **R002** | 0.35 | Connection 실패 | `connection refused`, `ECONNREFUSED`, `reset by peer` |
| **R003** | 0.25 | DNS / Name Resolution | `ENOTFOUND`, `NXDOMAIN`, `DNS`, `name resolution` |
| **R004** | 0.25 | 5xx 응답 | `5\d\d`, `502`, `503`, `504` |
| **R005** | 0.20 | ERROR 레벨 존재 | `level == ERROR` |
| **R006** | 0.20 | 동일 source ≥ 5회 | `_count_by_source ≥ 5` |
| **R007** | 0.40 | Out of Memory | `OOM`, `OutOfMemoryError`, `MemoryError` |
| **R008** | 0.30 | DB 관련 오류 | `database`/`SQL`/`pool`/`deadlock` + ERROR/WARN |
| **R009** | 0.35 | 디스크 용량 부족 | `disk full`, `ENOSPC`, `no space left` |
| **R010** | 0.25 | CPU 과부하 | `CPU`, `high load`, `throttl` |
| **R011** | 0.25 | 인증/인가 실패 | auth 키워드 + 4xx 동시 |
| **R012** | 0.20 | Rate Limit 초과 | `rate limit`, `too many requests`, `quota` |
| **R013** | 0.45 | 애플리케이션 크래시 | `crash`, `panic`, `segfault`, `fatal` |
| **R014** | 0.30 | 서비스 재시작 | `restart`, `reboot`, `killed`, `terminated` |
| **R015** | 0.30 | SSL/TLS 인증서 문제 | `SSL`/`TLS`/`certificate` + ERROR/WARN |
| **R016** | 0.25 | 권한 거부 | `permission denied`, `EACCES`, `access denied` |
| **R017** | 0.15 | 4xx 반복 | `4\d\d` 가 ≥ 3회 |
| **R018** | 0.15 | WARN ≥ 3회 | `level == WARN` 가 ≥ 3건 |

### 3-2. Confidence 산출식

```
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│   base       =  Σ rule.score                                        │
│                                                                      │
│   evidence   =  count ≥ 5 → +0.20                                   │
│                 count == 4 → +0.15                                  │
│                 count == 3 → +0.10                                  │
│                 count == 2 → +0.05                                  │
│                                                                      │
│   interaction = R001+R004 → +0.15   (timeout × 5xx)                 │
│                 R001+R005 → +0.10   (timeout × ERROR)               │
│                 R002+R003 → +0.10   (connection × DNS)              │
│                 R007+R013 → +0.15   (OOM × crash)                   │
│                 R008+R001 → +0.12   (DB × timeout)                  │
│                 R009+R013 → +0.12   (disk × crash)                  │
│                 R010+R001 → +0.10   (CPU × timeout)                 │
│                                                                      │
│   confidence = min(base + evidence + interaction, 1.0)              │
│                                                                      │
│   ┌──────────────────────────────────────────────────────────────┐  │
│   │  severity =  HIGH   (≥ 0.75)   ████████████░  ▶ 적색         │  │
│   │              MEDIUM (≥ 0.45)   ███████░░░░░░  ▶ 황색         │  │
│   │              LOW    (< 0.45)   ████░░░░░░░░░  ▶ 청색         │  │
│   └──────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

### 3-3. 설명 가능성 (Explainability)

응답의 `matched_rules` 필드는 **사람이 읽을 수 있는 근거 문자열** 로 직렬화:

```
[
  "R001 Timeout 발생 (+0.35) - 로그 메시지에 timeout / timed out / ETIMEDOUT 키워드가 포함됨",
  "R004 5xx 응답 감지 (+0.25) - 로그 메시지에 5xx(502/503/504) 상태 코드 패턴이 포함됨",
  "R005 ERROR 레벨 로그 존재 (+0.20) - level=ERROR 로 기록된 로그가 하나 이상 존재함"
]
```

GPT 보강 시에도 룰 결과가 **baseline** — `gpt_analyzer.py` 의 system prompt 가
`"The rule-engine analysis is the baseline. Do NOT contradict rules without clear justification."` 로 고정되어 있음.

### 3-4. 검증 자산

- `backend/src/analysis/validation/test_cases.py` — 50개 시나리오 (silence / single rule / multi rule / edge)
- `backend/src/analysis/validation/distribution.py` — 분포 분석 + 미스매치 리포트

---

## 🌐 4. API 레퍼런스 (현재 동작 기준)

> **모든 보호 라우트는 쿠키의 `access_token` 으로 인증**. tenant/project 경계는 서버에서 강제.

### 4-1. API 트리

```
🔓 PUBLIC
├── POST   /auth/register          email/password → tenant 자동 생성 + 토큰 쿠키
├── POST   /auth/login             자격 확인 → 새 refresh 발급(rotation 시작점)
├── POST   /auth/refresh           refresh 쿠키만으로 access 갱신 + rotation
└── POST   /auth/logout            현 refresh revoke + 쿠키 제거

🔓 SEMI-PUBLIC  (헤더 기반 — 에이전트/외부)
├── POST   /ingest                 X-Tenant-ID, X-Project-ID 필수, raw 보관 X
└── POST   /analysis/test          DB 없이 룰만 실행 (개발/검증용)

🔐 PROTECTED  (cookie:access_token 필요, tenant 자동 적용)
├── /projects
│   ├── GET    .                   내 tenant 의 프로젝트 목록
│   ├── POST   .                   { name } → ProjectResponse
│   └── DELETE /{project_id}
│
└── /projects/{project_id}
    ├── /logs
    │   ├── POST   .               { source, message, level, timestamp? }
    │   ├── GET    .               최근 200건 (timestamp desc)
    │   └── DELETE /{log_id}
    │
    ├── /analysis
    │   └── POST   .               { log_ids[], strategy } → AnalysisResultDTO + DB 저장
    │
    └── /reports
        ├── GET    .               목록 (start_date/end_date/limit)
        ├── GET    /{analysis_id}  단건
        ├── GET    /weekly         최근 7일 GPT 요약 + 다음주 리스크 (캐시됨)
        └── GET    /trend/confidence  일자별 평균 confidence + report_count

🚧 STUB / MISSING
├── GET    /projects/overview      ← 프론트 lib/api/overview.ts 호출 — 백엔드 없음 (404)
└── GET    /health                 ← health.py 비어있음, main.py 미등록
```

### 4-2. 대표 페이로드

**`POST /projects/{id}/analysis`**
```json
// Request
{
  "log_ids": ["uuid-1", "uuid-2"],
  "strategy": "rule"            // rule | gpt  (ai/hybrid 미구현)
}

// Response (저장된 AnalysisResult)
{
  "summary": "룰 기반 분석 결과, 다음과 같은 이상 징후가 감지되었습니다: Timeout 발생, 5xx 응답 감지.",
  "severity": "HIGH",
  "confidence": 0.85,
  "suspected_causes": ["Upstream 응답 지연", "프록시/게이트웨이 오류", ...],
  "recommended_actions": ["timeout 설정값 확인", "Upstream 헬스 점검", ...],
  "matched_rules": ["R001 Timeout 발생 (+0.35) - ...", "R004 5xx ... "],
  "strategy_used": "rule",
  "received_at": "2026-05-29T10:11:12Z"
}
```

**`GET /projects/{id}/reports/weekly`**
```json
{
  "period": "last_7_days",
  "from": "2026-05-22",
  "to": "2026-05-29",
  "report_count": 17,
  "summary": "지난 주는 게이트웨이 5xx 가 우세했고, ...",
  "risk_outlook": { "level": "보통", "reason": "..." }
}
```

**`POST /ingest`** (Agent 라인 단위 hot path — raw 로그 비저장)
```http
POST /ingest
X-Tenant-ID: <uuid>
X-Project-ID: <uuid>
X-Agent-ID: agent-001        (선택)
Content-Type: application/json

{ "logs": ["[ERROR] timeout", "[ERROR] 502 Bad Gateway", ...] }
```

### 4-3. 에러 컨벤션

| 상태 | 케이스 |
| :---: | --- |
| 400 | `analysis.log_ids` 일부가 tenant 또는 project 경계 밖 |
| 401 | `NO_ACCESS_TOKEN`, `Invalid or expired token`, refresh 재사용 탐지 등 |
| 404 | project / log / report 단건 미존재 |
| 409 | `EMAIL_ALREADY_EXISTS` |

---

## 🗄️ 5. 데이터 모델 (Postgres / SQLAlchemy)

### 5-1. ER 개요

```
              ┌──────────────┐
              │   tenants    │
              │──────────────│
              │ id (PK)      │
              │ name         │
              └──────┬───────┘
                     │ 1:N
       ┌─────────────┴────────────────┬────────────────┐
       │                              │                │
       ▼                              ▼                ▼
┌──────────────┐              ┌──────────────┐  ┌──────────────┐
│   users      │ 1:N           │  projects    │  │ refresh_     │
│──────────────│ ─────────┐    │──────────────│  │ tokens       │
│ id (PK)      │          │    │ id (PK)      │  │──────────────│
│ email (uniq) │          │    │ tenant_id    │  │ id=jti (PK)  │
│ password_hash│          │    │ name         │  │ user_id (FK) │
│ tenant_id    │          │    │ created_at   │  │ tenant_id    │
│ created_at   │          │    └──────┬───────┘  │ token_hash   │
└──────────────┘          │           │ 1:N      │ expires_at   │
                          └─────────────────────▶│ revoked      │
                                      │          │ revoked_at   │
        ┌─────────────────────────────┤          └──────────────┘
        │                             │
        ▼                             ▼
┌──────────────┐               ┌─────────────────────┐
│    logs      │               │  analysis_results   │
│──────────────│               │─────────────────────│
│ id (PK)      │               │ id (PK)             │
│ tenant_id    │               │ tenant_id           │
│ project_id   │               │ project_id          │
│ source       │               │ summary (text)      │
│ source_type  │ "manual|agent"│ severity (enum)     │
│ message      │               │ confidence (float)  │
│ level (enum) │               │ suspected_causes(JSONB)│
│ timestamp    │               │ recommended_actions(JSONB)│
│ received_at  │               │ matched_rules(JSONB)│
│ host         │               │ signals(JSONB)      │
└──────────────┘               │ strategy_used       │
                               │ received_at         │
                               └──────────┬──────────┘
                                          │ 7-day 집계
                                          ▼
                               ┌─────────────────────┐
                               │  weekly_reports     │
                               │─────────────────────│
                               │ id (PK)             │
                               │ tenant_id, project_id│
                               │ period_start/end    │
                               │ report_count        │
                               │ summary (GPT)       │
                               │ risk_level          │
                               │ risk_reason         │
                               │ created_at          │
                               └─────────────────────┘
```

### 5-2. Enum 정합성

| Enum | Backend | Frontend | Drift |
| --- | --- | --- | --- |
| `LogLevel` | DEBUG / INFO / WARN / ERROR | 동일 | ✅ |
| `SeverityLevel` | LOW / MEDIUM / HIGH / **CRITICAL** | LOW / MEDIUM / HIGH | ⚠️ CRITICAL 누락 (엔진 미사용이라 당장은 무해) |
| `AnalysisStrategy` | rule / ai / hybrid / gpt | rule / gpt | ⚠️ ai/hybrid 백엔드도 미구현 |

### 5-3. 스키마 변경 / 마이그레이션

> ❌ **Alembic 미사용**. `backend/src/db/init.py` 의 `Base.metadata.create_all()` 만 사용.
> Seed 스크립트는 `--reset` 옵션으로 `drop_all + create_all` 로 해결. **운영 마이그레이션 전략 부재**.

---

## 🛡️ 6. 인증 / 세션

| 항목 | 값 |
| --- | --- |
| 알고리즘 | HS256 (`SECRET_KEY` env) |
| Access TTL | 60 min (`ACCESS_TOKEN_EXPIRE_MINUTES`) |
| Refresh TTL | 14 days (`REFRESH_TOKEN_EXPIRE_DAYS`) |
| Access 쿠키 | `access_token` · httpOnly · path=`/` · max-age=60min |
| Refresh 쿠키 | `refresh_token` · httpOnly · **path=`/auth`** · max-age=14d |
| Secure / SameSite | `COOKIE_SECURE`, `COOKIE_SAMESITE` (기본 false / lax — 운영 시 변경 필요) |
| Password Hash | **argon2** (`passlib`) |
| Refresh 저장 | `refresh_tokens` 테이블 (id=jti, token_hash, expires_at, revoked) |
| Rotation | refresh 사용 시 즉시 revoke + 새 토큰 발급 |
| **Reuse Detection** | revoked 된 refresh 재사용 시 → 해당 user 전체 세션 강제 revoke |
| 토큰 위/변조 | refresh 의 token_hash 불일치 시 → 전체 세션 강제 revoke |
| 프론트 보관 | **없음** — 쿠키만 사용 (zustand 는 hydrated 플래그만) |
| 401 처리 | axios interceptor 가 `/auth/refresh` 자동 호출 → 원 요청 재시도, 실패 시 `/auth/login` 으로 이동 |

---

## 🖼️ 7. Frontend (현재 라우트 & 상태)

```
/  (page.tsx — 서버 컴포넌트)
   └─ cookie:access_token 있으면 → /projects
      없으면 → /auth/login

/auth/login            로그인 폼 → POST /auth/login → 서버가 쿠키 set
/auth/register         가입 폼   → POST /auth/register

/projects              내 tenant 프로젝트 카드 그리드
/projects/new          새 프로젝트 생성
/projects/[id]         프로젝트 상세
   ├─ NewLogModal      수동 로그 입력 (POST /projects/{id}/logs)
   └─ WeeklyReportCard GET /projects/{id}/reports/weekly

/projects/[id]/reports 분석 리포트 목록

/components/common/
   ├─ LogoutButton     POST /auth/logout
   └─ SeverityBadge    severity 색상 매핑

/components/Layout/TopNav
```

> 🎨 다크 테마 고정 (`zinc-950` / `zinc-100`). Tailwind 4. 디자인 시스템 상세는 `docs/DESIGN_SYSTEM.md`.

---

## 🤖 8. Netscope Agent (현재 상태)

```bash
python netscope-agent.py --path /var/log/app.log \
                         --source gateway \
                         --tenant <tenant_uuid> \
                         --project <project_uuid>
```

| 항목 | 값 |
| --- | --- |
| 의존성 | stdlib + `requests` (배포 친화 유지) |
| Tail 주기 | 1s 폴링 (`os.path.getsize` 기반) |
| 정규화 | BOM(`﻿`), `\r`, `\x00`, `[\x00-\x1F\x7F-\x9F]` 제거 |
| Level 추론 | 본문에서 `ERROR\|WARN\|INFO` 첫 매치 → 없으면 `DEBUG` |
| Agent-side 필터 | level∈{ERROR,WARN} OR `TIMEOUT`/`TIMED OUT` OR HTTP 5xx |
| 헤더 | `X-Tenant-ID`, `X-Project-ID` 부착 |
| **⚠️ 알려진 깨짐** | `API_URL = http://127.0.0.1:8000/logs` — 백엔드 라우트는 `/projects/{id}/logs` 로 이전. 또한 인증 없이는 401. **`/ingest` 로 전환 + 호스트 환경변수화 필요.** |
| Resume | 미저장 — EOF 부터 시작 (재시작 시 라인 누락 가능) |
| 실패 처리 | stdout 로그 후 다음 라인으로 계속 (루프 유지) |

---

## 🐳 9. 실행 / 배포

### 9-1. Docker Compose (권장)

```bash
# 사전 준비
cp backend/.env.example backend/.env.docker  # SECRET_KEY, OPENAI_API_KEY 등 채움

docker compose up -d --build
# postgres   : localhost:5432  (volume: postgres_data)
# backend    : localhost:8000  (uvicorn, FastAPI)
# frontend   : localhost:3000  (Next.js dev — bind mount + hot reload)

# 데모 데이터 시드
docker compose exec backend python -m scripts.seed --reset
# alice@demo.io / bob@demo.io / carol@demo.io  (PW: Demo1234!)
```

### 9-2. 로컬 (수동)

```powershell
# Backend
cd backend
pip install -r requirements.txt
$env:DATABASE_URL = "postgresql+psycopg://netscope:netscope_dev_pw@localhost:5432/netscope"
$env:SECRET_KEY = "dev-secret"
$env:OPENAI_API_KEY = "sk-..."   # 선택
uvicorn src.main:app --reload --port 8000

# Frontend
cd frontend
npm install
$env:NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000"
npm run dev
```

### 9-3. Agent

```bash
cd backend/netscope-agent
python netscope-agent.py --path ../../test-log/shell.log \
                         --source demo --tenant <uuid> --project <uuid>
# ⚠️ 현재 API_URL 이 /logs (legacy) — 동작시키려면 코드 수정 필요
```

---

## 🚨 10. 알려진 갭 / 주의 사항

```
우선  영역                  상태   영향                                       해결 액션
────  ────────────────────  ────   ────────────────────────────────────────  ────────────────────────────
P0    Agent ↔ /ingest 정합  🚧    실제 운영 시 로그 한 줄도 못 받음            URL→/ingest, 인증 정책 결정
P0    /projects/overview     🚧    프론트 콜은 있는데 백엔드 없음 → 404         라우터 추가 or 프론트 제거
P0    /health                ❌    외부 모니터링 / k8s probe 불가              health.py 본문 + 라우터 등록
P0    테스트                  ❌    auth/DB/ingest 전부 회귀 방어 없음          최소 auth+analysis 통합 테스트
P0    GPT 모델명               🚧    `gpt-4.1-mini` 표기 — 의도와 일치?         확인 후 정정
P1    Alembic                ❌    스키마 변경 마다 drop_all 필요               Alembic 도입 + initial revision
P1    Frontend Severity 타입  ⚠️   CRITICAL 누락                              types/analysis.ts 갱신
P1    Strategy 타입          ⚠️   ai/hybrid 정의만 존재                        engine 분기 추가 or enum 정리
P1    CORS                   ⚠️   FRONTEND_ORIGIN 단일 — 다환경 미고려           ALLOWED_ORIGINS 목록화
P1    Dockerfile.local-backup ⚠️   미추적 — 노이즈                              `.gitignore` 또는 삭제
P1    db/deps.py 중복         ⚠️   session.py 와 동일 함수 중복 정의            하나로 통합
P2    Agent Resume            ⚠️   재시작 사이 라인 누락 가능                   파일 오프셋 저장
P2    7일 윈도우 리텐션         ❌    README 언급뿐, 코드 없음                    cron / cleanup job
P2    구조화 파서              ❌    log/parser.py 비어있음                     JSON/syslog 파서
P2    Inmemory storage 잔재   ⚠️   infrastructure/storage.py 사용처 없음        제거 후보
P3    룰 학습 L0~L4          ❌    docs/RULE_LEARNING.md 만 존재                백그라운드 패턴 마이닝부터
```

---

## 🎨 10-1. UI / 보고서 시각화 원칙  ⭐ 필수 요구사항

> **원칙**: 분석 결과·주간 리포트·프로젝트 상세 등 **사용자가 보는 모든 보고서 화면은 시각적으로 강하게 표현**한다.
> 텍스트 나열만으로는 부족 — 정보가 충분해도 "보고서답지 않다"는 인상을 줌.

### 적용 대상

```
✅ /projects/[id]                  프로젝트 상세 (대시보드)
✅ /projects/[id]/reports          분석 리포트 목록
✅ /projects/[id]/reports/[id]     단건 리포트 (추후)
✅ WeeklyReportCard                주간 리포트 카드
✅ SeverityBadge                   심각도 배지
✅ 향후 추가될 인시던트 보고서 (P1 Flagship UI)
```

### 시각 요소 체크리스트

| 카테고리 | 요구사항 |
| --- | --- |
| **Severity 색상** | LOW=blue/cyan · MEDIUM=amber/yellow · HIGH=red/rose · (CRITICAL=magenta) — 배지 + 카드 border + 좌측 컬러 바 동시 사용 |
| **Confidence** | 숫자만 X — 게이지 바 / 도넛 / 그라데이션으로 시각화. `0.85` 보다 `█████████░ 85%` 가 우선 |
| **Matched Rules** | 단순 리스트 X — 룰 ID 칩(chip) + 점수 + 근거 expand. 룰 카테고리별 색상 코드 |
| **Trend (confidence)** | `/reports/trend/confidence` 데이터를 라인/에어리어 차트로. 점선 임계값(0.45 / 0.75) 표시 |
| **Weekly Report** | 카드 헤더에 기간 + report_count + risk_outlook 색상 그라데이션 배경 |
| **Causes / Actions** | 불릿 X — 아이콘(🩺 원인 / 🛠 조치) + 카드 grid. 길어지면 collapse |
| **Empty / Loading** | "분석된 로그가 없습니다" 같은 평문 X — 일러스트/아이콘 + CTA 버튼 |
| **타이포그래피** | summary 는 큰 폰트(text-xl+) · 메타데이터는 mono + muted color 로 대비 |
| **다크 테마** | `zinc-950` 배경 위에서 색이 살아야 함 — Tailwind `*-400`/`*-500` 톤 권장 |

### 안티 패턴 (피할 것)

```
❌ "severity: HIGH, confidence: 0.82" 같은 key:value 평문 나열
❌ matched_rules 를 `<ul><li>` 텍스트로만 표시
❌ 회색조만 사용 — severity 가 글로 적힌 단어로만 구분되는 화면
❌ 차트 없는 trend 데이터
❌ 한 컬럼에 모든 정보를 세로로 쌓기 (요약/근거/액션은 carded grid 로)
```

### 권장 라이브러리 / 패턴

- **차트** — `recharts` 또는 `tremor` (Tailwind 친화)
- **아이콘** — `lucide-react`
- **모션** — `framer-motion` (카드 hover / 등장 애니메이션)
- **컬러 매핑** — `frontend/src/styles/severity.ts` 가 현재 비어있음 → **여기에 severity→color 매핑 표를 정본으로 통일**, 컴포넌트별 하드코딩 금지

### 작업 시 체크 룰

> 새 보고서/대시보드 컴포넌트를 만들 때 위 체크리스트 절반 이상이 ❌면 머지 보류.
> "기능은 되는데 보고서답지 않다"는 피드백을 받으면 이 섹션을 다시 본다.

---

## 🧭 11. 작업 컨벤션 / 에이전트 가이드

- **언어** — 코드 주석/식별자는 영어, 도메인 문서/기획서는 한국어 가능. 라우터의 한국어 주석은 유지.
- **레이어 경계**
  - 라우터는 ORM 직접 접근 금지가 아니라 **읽기만 직접 허용** (분석/리포트 라우터에서는 직접 query 사용 중).
  - 쓰기/도메인 로직은 `domain/*DomainService` 로 위임 (auth, log, project 가 모범 사례).
  - 분석 엔진(`analysis/engine.py`)은 **ORM 모름** — `RuleLog` (frozen dataclass) 만 받음.
- **Tenant 강제** — 보호 라우트는 항상 `Depends(get_current_context)` → `ctx["tenant_id"]` 로 query 필터. `project_id` 도 함께 필터링해 cross-tenant 접근 차단.
- **룰 추가 시**
  1. `rule_engine.py::default_rules()` 에 `Rule(...)` 추가
  2. 필요 시 `interaction_bonus()` 에 조합 추가
  3. `validation/test_cases.py` 양/음성 케이스 추가
  4. `validation/distribution.py` 실행해 분포 회귀 확인
- **DTO 변경 시** — `backend/src/schemas/*` 와 `frontend/src/types/*` **양쪽 동기화 필수** (특히 Severity / Strategy).
- **GPT enrichment 변경** — system prompt 의 *"rule-engine analysis is the baseline"* 문구는 유지. 그렇지 않으면 결정성/재현성 깨짐.
- **Agent** — stdlib + `requests` 만 사용. 의존성 추가 신중.
- **DB 스키마 변경** — Alembic 도입 전에는 `seed.py --reset` 으로 drop+recreate. 운영 마이그 책임은 직접 SQL.

---

## 🛣️ 12. 다음 단계 트리아지

```
                     ┌────────────────────────────────────────────────────┐
   P0 (이번 주)       │  · /ingest 로 Agent 정합 (URL + 인증)               │
   "운영 가능성"       │  · /health 본문 + 라우터 등록                       │
                     │  · /projects/overview 라우터 추가 (또는 프론트 제거) │
                     │  · 최소 회귀 테스트 (auth + analysis 통합)            │
                     │  · GPT 모델명 정정 / 확정                            │
                     └────────────────────────────────────────────────────┘
                     ┌────────────────────────────────────────────────────┐
   P1 (다음 2~4주)    │  · 🔥 인시던트 보고서 대시보드 (Flagship UI)          │
   "차별점 확보"       │  · Alembic 도입 + initial revision                  │
                     │  · 룰 관리 API + 룰 토글                             │
                     │  · 패턴 마이닝 백그라운드 수집 (룰 학습 L0)            │
                     │  · Severity/Strategy 타입 동기화                     │
                     │  · CORS 다환경, Webhook 알림                         │
                     └────────────────────────────────────────────────────┘
                     ┌────────────────────────────────────────────────────┐
   P2 (1~2개월)       │  · 7일 리텐션 정책 + 구조화 파서                     │
                     │  · Redis 캐시 (weekly report TTL)                  │
                     │  · 에이전트 Resume (오프셋 영속화)                    │
                     │  · PDF Export, 패턴 라벨링 UX (룰 학습 L1·L2)         │
                     └────────────────────────────────────────────────────┘
                     ┌────────────────────────────────────────────────────┐
   P3 (분기 이후)      │  · 룰 A/B 테스트, 비용/토큰 트래킹                    │
                     │  · 룰 자동 승격 + 피드백 가중치 (룰 학습 L3·L4)        │
                     │  · 양방향 Slack 통합                                │
                     └────────────────────────────────────────────────────┘
```

> 룰 학습 전체 설계는 [`docs/RULE_LEARNING.md`](./docs/RULE_LEARNING.md) — Netscope-AI 의 핵심 차별점.

---

```
                        ─── netscope-ai · CLAUDE.md ───
                       last sync : 2026-05-29 (post auth/db merge)
```
