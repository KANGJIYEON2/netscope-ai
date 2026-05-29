# 🔭 Netscope-AI — Explainable Log Diagnostics

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

> 📎 에이전트/기여자 작업 가이드 → [`CLAUDE.md`](./CLAUDE.md)
> 📎 PM 고도화 기획안 → [`docs/PM_ENHANCEMENT_PLAN.md`](./docs/PM_ENHANCEMENT_PLAN.md)
> 📎 룰 학습 정본 → [`docs/RULE_LEARNING.md`](./docs/RULE_LEARNING.md)
> 📎 디자인 시스템 → [`docs/DESIGN_SYSTEM.md`](./docs/DESIGN_SYSTEM.md)

---

## 🗺️ 상태 한눈에 보기

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

## 🏛️ 시스템 아키텍처

### 전체 토폴로지

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

### Auth 흐름 (시퀀스)

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

### 분석 파이프라인 (이벤트 흐름)

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

## 🧠 Rule Engine (R001~R018, v2.0)

> 룰셋 버전 `v2.0`. 상세 정본은 [`docs/RULE_ENGINE.md`](./docs/RULE_ENGINE.md).

### 룰 카탈로그

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

### Confidence 산출식

```
┌──────────────────────────────────────────────────────────────────────┐
│   base       =  Σ rule.score                                        │
│                                                                      │
│   evidence   =  count ≥ 5 → +0.20   ·  count == 4 → +0.15           │
│                 count == 3 → +0.10  ·  count == 2 → +0.05           │
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
│   severity =  HIGH   (≥ 0.75)   ████████████░  ▶ 적색               │
│               MEDIUM (≥ 0.45)   ███████░░░░░░  ▶ 황색               │
│               LOW    (< 0.45)   ████░░░░░░░░░  ▶ 청색               │
└──────────────────────────────────────────────────────────────────────┘
```

### 설명 가능성 (Explainability)

응답의 `matched_rules` 필드는 **사람이 읽을 수 있는 근거 문자열** 로 직렬화:

```
[
  "R001 Timeout 발생 (+0.35) - 로그 메시지에 timeout / timed out / ETIMEDOUT 키워드가 포함됨",
  "R004 5xx 응답 감지 (+0.25) - 로그 메시지에 5xx(502/503/504) 상태 코드 패턴이 포함됨",
  "R005 ERROR 레벨 로그 존재 (+0.20) - level=ERROR 로 기록된 로그가 하나 이상 존재함"
]
```

GPT 보강 시에도 룰 결과가 **baseline** — `gpt_analyzer.py` 의 system prompt 가
`"The rule-engine analysis is the baseline. Do NOT contradict rules without clear justification."` 로 고정.

**검증 자산** — `backend/src/analysis/validation/test_cases.py`(50개 시나리오) · `distribution.py`(분포/미스매치 리포트).

---

## 🌐 API 레퍼런스

> 상세 정본은 [`docs/API_REFERENCE.md`](./docs/API_REFERENCE.md). 모든 보호 라우트는 쿠키의 `access_token` 으로 인증, tenant/project 경계는 서버에서 강제.

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
    ├── /analysis
    │   └── POST   .               { log_ids[], strategy } → AnalysisResultDTO + DB 저장
    └── /reports
        ├── GET    .               목록 (start_date/end_date/limit)
        ├── GET    /{analysis_id}  단건
        ├── GET    /weekly         최근 7일 GPT 요약 + 다음주 리스크 (캐시됨)
        └── GET    /trend/confidence  일자별 평균 confidence + report_count

🚧 STUB / MISSING
├── GET    /projects/overview      ← 프론트 lib/api/overview.ts 호출 — 백엔드 없음 (404)
└── GET    /health                 ← health.py 비어있음, main.py 미등록
```

### 대표 페이로드

**`POST /projects/{id}/analysis`**
```json
// Request
{ "log_ids": ["uuid-1", "uuid-2"], "strategy": "rule" }   // rule | gpt (ai/hybrid 미구현)

// Response (저장된 AnalysisResult)
{
  "summary": "룰 기반 분석 결과, 다음과 같은 이상 징후가 감지되었습니다: Timeout 발생, 5xx 응답 감지.",
  "severity": "HIGH",
  "confidence": 0.85,
  "suspected_causes": ["Upstream 응답 지연", "프록시/게이트웨이 오류"],
  "recommended_actions": ["timeout 설정값 확인", "Upstream 헬스 점검"],
  "matched_rules": ["R001 Timeout 발생 (+0.35) - ...", "R004 5xx ... "],
  "strategy_used": "rule",
  "received_at": "2026-05-29T10:11:12Z"
}
```

**`POST /ingest`** (Agent 라인 단위 hot path — raw 로그 비저장)
```http
POST /ingest
X-Tenant-ID: <uuid>
X-Project-ID: <uuid>
Content-Type: application/json

{ "logs": ["[ERROR] timeout", "[ERROR] 502 Bad Gateway"] }
```

### 에러 컨벤션

| 상태 | 케이스 |
| :---: | --- |
| 400 | `analysis.log_ids` 일부가 tenant 또는 project 경계 밖 |
| 401 | `NO_ACCESS_TOKEN`, `Invalid or expired token`, refresh 재사용 탐지 등 |
| 404 | project / log / report 단건 미존재 |
| 409 | `EMAIL_ALREADY_EXISTS` |

---

## 🗄️ 데이터 모델 (Postgres / SQLAlchemy)

```
              ┌──────────────┐
              │   tenants    │
              │ id (PK)      │
              │ name         │
              └──────┬───────┘
                     │ 1:N
       ┌─────────────┼────────────────┬────────────────┐
       ▼             ▼                ▼                │
┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│   users      │  │  projects    │  │ refresh_     │   │
│ id (PK)      │  │ id (PK)      │  │ tokens       │   │
│ email (uniq) │  │ tenant_id    │  │ id=jti (PK)  │   │
│ password_hash│  │ name         │  │ user_id (FK) │   │
│ tenant_id    │  │ created_at   │  │ token_hash   │   │
└──────────────┘  └──────┬───────┘  │ expires_at   │   │
                         │ 1:N      │ revoked      │   │
        ┌────────────────┤          └──────────────┘   │
        ▼                ▼                              │
┌──────────────┐   ┌─────────────────────┐             │
│    logs      │   │  analysis_results   │             │
│ id (PK)      │   │ id (PK)             │             │
│ tenant_id    │   │ tenant_id           │             │
│ project_id   │   │ project_id          │             │
│ source       │   │ summary (text)      │             │
│ source_type  │   │ severity (enum)     │             │
│ message      │   │ confidence (float)  │             │
│ level (enum) │   │ suspected_causes JSONB│           │
│ timestamp    │   │ recommended_actions JSONB│         │
│ received_at  │   │ matched_rules JSONB │             │
│ host         │   │ signals JSONB       │             │
└──────────────┘   │ strategy_used       │             │
                   │ received_at         │             │
                   └──────────┬──────────┘             │
                              │ 7-day 집계              │
                              ▼                         │
                   ┌─────────────────────┐             │
                   │  weekly_reports     │◀────────────┘
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

### Enum 정합성

| Enum | Backend | Frontend | Drift |
| --- | --- | --- | --- |
| `LogLevel` | DEBUG / INFO / WARN / ERROR | 동일 | ✅ |
| `SeverityLevel` | LOW / MEDIUM / HIGH / **CRITICAL** | LOW / MEDIUM / HIGH | ⚠️ CRITICAL 누락 (엔진 미사용이라 당장은 무해) |
| `AnalysisStrategy` | rule / ai / hybrid / gpt | rule / gpt | ⚠️ ai/hybrid 백엔드도 미구현 |

> ❌ **Alembic 미사용**. `backend/src/db/init.py` 의 `Base.metadata.create_all()` 만 사용.
> Seed 스크립트의 `--reset` 옵션이 `drop_all + create_all` 로 해결. 운영 마이그레이션 전략 부재.

---

## 🛡️ 인증 / 세션

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
| 401 처리 | axios interceptor 가 `/auth/refresh` 자동 호출 → 원 요청 재시도, 실패 시 `/auth/login` 이동 |

---

## 🖼️ Frontend (라우트 & 상태)

```
/                      cookie:access_token 있으면 → /projects, 없으면 → /auth/login
/auth/login            로그인 폼 → POST /auth/login → 서버가 쿠키 set
/auth/register         가입 폼   → POST /auth/register
/projects              내 tenant 프로젝트 카드 그리드
/projects/new          새 프로젝트 생성
/projects/[id]         프로젝트 상세
   ├─ NewLogModal      수동 로그 입력 (POST /projects/{id}/logs)
   └─ WeeklyReportCard GET /projects/{id}/reports/weekly
/projects/[id]/reports 분석 리포트 목록
```

> 🎨 다크 테마 고정 (`zinc-950` / `zinc-100`). Tailwind 4. 디자인 시스템은 [`docs/DESIGN_SYSTEM.md`](./docs/DESIGN_SYSTEM.md).

---

## 🤖 Netscope Agent

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
| **⚠️ 알려진 깨짐** | `API_URL = http://127.0.0.1:8000/logs` — 백엔드는 `/projects/{id}/logs` 로 이전 + 인증 필요. **`/ingest` 전환 + 호스트 환경변수화 필요.** |
| Resume | 미저장 — EOF 부터 시작 (재시작 시 라인 누락 가능) |

---

## 🐳 실행 / 배포

### Docker Compose (권장)

```bash
docker compose up -d --build
# Postgres   → localhost:5432  (volume: postgres_data)
# Backend    → http://localhost:8000  (Swagger: /docs)
# Frontend   → http://localhost:3000  (자동으로 /auth/login 으로 리다이렉트)
```

종료/초기화

```bash
docker compose down       # 컨테이너만 종료 (데이터 유지)
docker compose down -v    # 볼륨까지 초기화 (DB 완전 wipe)
```

### 로컬 (수동)

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

### Postgres — dev credentials

| Field    | Value              |
| -------- | ------------------ |
| Host     | `localhost`        |
| Port     | `5432`             |
| Database | `netscope`         |
| User     | `netscope`         |
| Password | `netscope_dev_pw`  |

```bash
docker exec -it netscope-postgres psql -U netscope -d netscope
```

> ⚠️ Dev only. `docker-compose.yml` 에 평문 정의 — 운영 환경에서는 절대 그대로 쓰지 말 것.

### 데모 계정 (시드 후 사용 가능)

각 계정은 **자기 tenant 의 프로젝트/로그/분석 결과만** 볼 수 있습니다 (멀티테넌시 격리).

| Email             | Password    | Tenant          | Projects                          | 시나리오                          |
| ----------------- | ----------- | --------------- | --------------------------------- | --------------------------------- |
| `alice@demo.io`   | `Demo1234!` | Alice Co.       | `gateway-prod`, `auth-service`    | gateway timeout + auth JWT 에러   |
| `bob@demo.io`     | `Demo1234!` | Bob Industries  | `billing-api`, `worker-queue`     | DB connection 거부 + 워커 혼합 오류 |
| `carol@demo.io`   | `Demo1234!` | Carol Labs      | `edge-cdn`, `checkout-flow`       | DNS 실패 + checkout 5xx           |

각 계정은 **프로젝트 2개씩, 프로젝트당 18개의 로그, 1~2개의 사전 분석 결과** 를 가집니다.

```bash
# 첫 실행 또는 데이터 wipe 후 재시드 (drop_all + create_all)
docker exec netscope-backend python -m scripts.seed --reset

# 이미 테이블이 맞으면 기존 데모 계정은 건너뜀 (idempotent)
docker exec netscope-backend python -m scripts.seed
```

---

## 🧭 제품 설계 노트 (MVP)

운영 로그를 **프로젝트 단위로 수집·분석**하고, Rule 기반 + GPT 보강으로 **운영 리스크를 빠르게 파악**한다.

```
인증 흐름        첫 화면 = 로그인/회원가입 → Tenant ID 기준 진입 → 모든 데이터 Tenant 단위 분리
좌측 Nav         Test Log · Project Log 두 메뉴만 (MVP 단계 메뉴 확장 지양)
Project          실제 운영 로그 저장 단위 = 분석 결과 + 주간 리포트 기준 단위
Test Log         로그 직접 입력 → 즉시 분석 · DB 저장 X · 프로젝트 무관 (룰/GPT 품질 검증용)
Project Log      수동 입력(New Log) + (향후) Agent/API 자동 수집
```

### 로그 저장 정책 — "의미 있는 로그만 남긴다"

```
✅ 저장      Rule 매칭 로그 · GPT 분석 대상 로그
❌ 미저장    단순 원본 로그 전체 · 의미 없는 반복 로그
```

### 분석 결과 (Report) 구성

`Summary` · `Severity(LOW/MEDIUM/HIGH)` · `Confidence` · `Cause` · `Action` · `Evidence(Matched Rules)`
— 각 결과는 리포트 단위로 저장·조회 가능.

### 주간 운영 리포트

최근 7일 분석 결과 집계 → Rule + GPT 자동 요약. 포함: 분석 리포트 수 · 주간 장애 패턴 요약 · 다음 주 리스크 예측(낮음/보통/높음 + 근거). 분석 실행 시 조건부 자동 생성, 동일 기간 중복 생성 방지.

### 향후 확장

로그 자동 수집 Agent · 알림(Slack/Webhook) · 리스크 트렌드 시각화 · 프로젝트별 권한 관리 · 분석 Rule UI 관리.

> **"로그를 쌓는 서비스가 아니라, 운영 판단에 필요한 '의미 있는 로그'만 남기는 분석 서비스"**

---

## 🚨 알려진 갭 / 로드맵

```
우선  영역                  상태   해결 액션
────  ────────────────────  ────   ────────────────────────────
P0    Agent ↔ /ingest 정합  🚧    URL→/ingest, 인증 정책 결정
P0    /projects/overview     🚧    라우터 추가 or 프론트 제거
P0    /health                ❌    health.py 본문 + 라우터 등록
P0    테스트                  ❌    최소 auth+analysis 통합 테스트
P0    GPT 모델명               🚧    `gpt-4.1-mini` 확인 후 정정
P1    Alembic                ❌    도입 + initial revision
P1    Frontend Severity 타입  ⚠️   CRITICAL 누락 → types/analysis.ts 갱신
P1    Strategy 타입          ⚠️   ai/hybrid engine 분기 or enum 정리
P1    CORS                   ⚠️   ALLOWED_ORIGINS 목록화
P2    Agent Resume            ⚠️   파일 오프셋 저장
P2    7일 윈도우 리텐션         ❌    cron / cleanup job
P2    구조화 파서              ❌    JSON/syslog 파서
P3    룰 학습 L0~L4          ❌    백그라운드 패턴 마이닝부터
```

전체 룰 학습 설계는 [`docs/RULE_LEARNING.md`](./docs/RULE_LEARNING.md) — Netscope-AI 의 핵심 차별점.

---

```
                        ─── netscope-ai · README.md ───
                       last sync : 2026-05-29 (post auth/db merge)
```
