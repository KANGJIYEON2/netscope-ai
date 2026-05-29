# 🔭 Netscope-AI — Explainable Log Diagnostics

```
╔══════════════════════════════════════════════════════════════════════════════╗
║   NETSCOPE-AI                                                                ║
║   Explainable Network/Application Log Diagnostics                            ║
║                                                                              ║
║   Stage  : MVP++  (Auth · DB · Multi-tenant · Rule Learning L0~L4 가동)       ║
║   Stack  : FastAPI · SQLAlchemy · Postgres · Next.js 16 · Tailwind 4         ║
║   Theme  : "왜 그렇게 판단했는가" 를 룰 ID + 학습 패턴 + 근거 + 점수로 노출       ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

> **한 줄 요약**: 로그 묶음을 **Rule Engine v3.0 (R001~R024) + Pattern Learning (L0~L4) + 선택적 GPT 보강** 으로 분석해,
> 매칭된 룰 ID·학습 패턴·근거·신뢰도·심각도까지 함께 응답하는 **설명 가능한** 진단 시스템.
> 현재는 **인증·DB·멀티테넌시·주간 리포트·룰 학습·패턴 매칭** 까지 실제 동작.

> 📎 에이전트/기여자 작업 가이드 → [`CLAUDE.md`](./CLAUDE.md)
> 📎 PM 고도화 기획안 → [`docs/PM_ENHANCEMENT_PLAN.md`](./docs/PM_ENHANCEMENT_PLAN.md)
> 📎 룰 학습 정본 → [`docs/RULE_LEARNING.md`](./docs/RULE_LEARNING.md)
> 📎 디자인 시스템 → [`docs/DESIGN_SYSTEM.md`](./docs/DESIGN_SYSTEM.md)

---

## 🗺️ 상태 한눈에 보기

```
영역                        상태      비고
──────────────────────────────────────────────────────────────────────
🟢 Rule Engine v3.0         DONE      R001~R024, 시간/통계/상관관계 룰, 13개 interaction bonus
🟢 Auth                     DONE      httpOnly 쿠키 + Refresh Rotation + Reuse 탐지
🟢 DB 영속화                DONE      Postgres + SQLAlchemy + Alembic 설정 완료
🟢 Multi-tenancy            DONE      JWT(sub, tenant_id) → 모든 라우터에서 tenant 강제
🟢 Projects                 DONE      tenant 단위 CRUD + /projects/overview (대시보드)
🟢 Analysis API             DONE      /projects/{id}/analysis + signals + matched_rules + matched_patterns
🟢 Reports API              DONE      list/trend/weekly + GPT 주간 요약 + 리스크 예측
🟢 Ingest Pipeline          DONE      raw 로그 → 구조화 파서 → 룰 → 패턴 마이닝 → 영속화
🟢 Docker Compose           DONE      postgres + backend + frontend (hot reload)
🟢 Seed Script              DONE      3 tenants × 2 projects × 18 logs
🟢 /health                  DONE      DB ping + liveness check
🟢 Agent ↔ /ingest          DONE      POST /ingest 배치 전송 + 오프셋 영속화 + 로그 회전 감지
🟢 GPT 모델명               DONE      gpt-4o-mini (4곳 수정 완료)
🟢 CORS 다환경              DONE      콤마 구분 복수 origin 지원
🟢 Severity/Strategy 동기화  DONE      CRITICAL + ai/hybrid 프론트엔드 타입 추가
🟢 severity.ts 컬러 매핑     DONE      cyan/amber/red/fuchsia 정본 (다크테마)
🟢 구조화 파서               DONE      JSON/key=value/syslog/plain text 자동감지
🟢 7일 리텐션                DONE      scripts/retention.py (--days N --dry-run)
🟢 Alembic                  DONE      초기 설정 + 모델 import 완료
🟢 테스트                    DONE      43개 (health/overview/rule engine/parser/learning)
🟢 Rule Learning L0          DONE      Drain 패턴 마이닝 + 변수 마스킹 + 카탈로그 DB
🟢 Rule Learning L1          DONE      패턴 관리 API (list/detail/label/dismiss)
🟢 Rule Learning L2          DONE      분석 시 PatternMatcher 통합, matched_patterns 노출
🟢 Rule Learning L3          DONE      피드백 API + 자동 승격/강등
🟢 Rule Learning L4          DONE      온라인 score_adjust + 안전 가드
🟡 Frontend Routes          PARTIAL   /auth, /projects, reports 동작 — 대시보드 미완성
🟡 패턴 관리 UI             PARTIAL   백엔드 API 완료 — 프론트엔드 /patterns 페이지 미구현
❌ L5 임베딩 유사도          미착수   sentence-transformer + HDBSCAN (장기)
```

> **범례** — 🟢 동작 · 🟡 일부 동작 · ❌ 미구현

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
│    · POST /ingest 배치 전송 · 오프셋 영속화 (~/.netscope-agent/)                  │
│    · 로그 회전(truncation) 자동 감지                                              │
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
│   │  • POST/GET /logs · POST /analysis · GET /reports/*                   │    │
│   └────────────────────────────────────────────────────────────────────────┘    │
│   ┌──────────────────────────────────┐  ┌─────────────────────────────────┐     │
│   │  POST /ingest  (Agent hot path)  │  │  /patterns (L1~L3 패턴 관리)    │     │
│   │  → 구조화 파서 → RuleEngine      │  │  list/label/dismiss/feedback     │     │
│   │  → PatternMiner (L0)             │  └─────────────────────────────────┘     │
│   │  → SignalAggregator → persist    │                                          │
│   └──────────────────────────────────┘  ┌─────────────────────────────────┐     │
│   ┌──────────────────────────────────┐  │  GET /health (DB ping)          │     │
│   │  GET /projects/overview          │  │  GET /projects/overview          │     │
│   │  (24h 로그수/에러율/최근분석)       │  └─────────────────────────────────┘     │
│   └──────────────────────────────────┘                                          │
│                                                                                 │
│   ┌─── AnalysisEngine.analyze() ────────────────────────────────────────┐       │
│   │  ① RuleEngine v3.0 (R001~R024)                                     │       │
│   │  ② PatternMatcher (L2 — 학습 패턴 매칭)                             │       │
│   │  ③ (옵션) GPTAnalyzer  ← strategy=gpt 이고 OPENAI_API_KEY 있을 때    │       │
│   │  ④ severity 자동 매핑 (CRITICAL/HIGH/MEDIUM/LOW)                     │       │
│   │  ⑤ AnalysisResult DB 저장 + matched_patterns 포함                    │       │
│   │  ⑥ 주간 리포트 자동 트리거: 최근 7일 ≥5건 + 미존재 → 생성              │       │
│   └────────────────────────────────────────────────────────────────────┘       │
└───────────────────────────────┬─────────────────────────────────────────────────┘
                                │  SQLAlchemy ORM
                                ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  🐘  POSTGRES 16   (docker-compose · postgres_data volume)                       │
│      tenants · users · refresh_tokens · projects                                │
│      logs · analysis_results · weekly_reports                                   │
│      patterns · pattern_feedback  ← L0~L4                                       │
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
```

### 분석 파이프라인 (이벤트 흐름)

```
   logs[]                       AnalysisEngine
     │                                │
     ▼                                ▼
 ┌────────────┐  matches   ┌─────────────────┐
 │ RuleEngine │ ─────────▶ │   aggregate()    │
 │ R001..R024 │            │  base + bonus   │
 └────────────┘            └────────┬────────┘
                                    │
                ┌───────────────────┼───────────────────┐
                │                   │                   │
                ▼                   ▼                   ▼
        ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐
        │ PatternMatcher│  │ severity     │  │ matched_rules[] │
        │ (L2 카탈로그) │  │ CRIT/HI/M/L │  │ matched_patterns│
        └──────┬───────┘  └──────┬───────┘  └────────┬────────┘
               │                 │                   │
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

## 🧠 Rule Engine v3.0 (R001~R024)

> 룰셋 버전 `v3.0`. 상세 정본은 [`docs/RULE_ENGINE.md`](./docs/RULE_ENGINE.md).

### 룰 카탈로그

| 룰 ID | 점수 | 제목 | 트리거 키워드/조건 | 유형 |
| :---: | :---: | --- | --- | --- |
| **R001** | 0.35 | Timeout 발생 | `timeout`, `timed out`, `ETIMEDOUT` | 키워드 |
| **R002** | 0.35 | Connection 실패 | `connection refused`, `ECONNREFUSED`, `reset by peer` | 키워드 |
| **R003** | 0.25 | DNS / Name Resolution | `ENOTFOUND`, `NXDOMAIN`, `DNS` | 키워드 |
| **R004** | 0.25 | 5xx 응답 | `5\d\d`, `502`, `503`, `504` | 키워드 |
| **R005** | 0.20 | ERROR 레벨 존재 | `level == ERROR` | 레벨 |
| **R006** | 0.20 | 동일 source ≥ 5회 | `_count_by_source ≥ 5` | 통계 |
| **R007** | 0.40 | Out of Memory | `OOM`, `OutOfMemoryError`, `MemoryError` | 키워드 |
| **R008** | 0.30 | DB 관련 오류 | `database`/`SQL`/`pool`/`deadlock` + ERROR/WARN | 키워드 |
| **R009** | 0.35 | 디스크 용량 부족 | `disk full`, `ENOSPC`, `no space left` | 키워드 |
| **R010** | 0.25 | CPU 과부하 | `CPU`, `high load`, `throttl` | 키워드 |
| **R011** | 0.25 | 인증/인가 실패 | auth 키워드 + 4xx 동시 | 복합 |
| **R012** | 0.20 | Rate Limit 초과 | `rate limit`, `too many requests`, `quota` | 키워드 |
| **R013** | 0.45 | 애플리케이션 크래시 | `crash`, `panic`, `segfault`, `fatal` | 키워드 |
| **R014** | 0.30 | 서비스 재시작 | `restart`, `reboot`, `killed`, `terminated` | 키워드 |
| **R015** | 0.30 | SSL/TLS 인증서 문제 | `SSL`/`TLS`/`certificate` + ERROR/WARN | 복합 |
| **R016** | 0.25 | 권한 거부 | `permission denied`, `EACCES` | 키워드 |
| **R017** | 0.15 | 4xx 반복 | `4\d\d` 가 ≥ 3회 | 통계 |
| **R018** | 0.15 | WARN ≥ 3회 | `level == WARN` 가 ≥ 3건 | 레벨 |
| **R019** | 0.40 | 에러 버스트 | 1분 내 ERROR 5건+ | 시간윈도우 |
| **R020** | 0.45 | 타임아웃→크래시 연쇄 | timeout 후 5분 내 crash/panic | 순서패턴 |
| **R021** | 0.35 | 높은 에러율 | ERROR/전체 ≥ 50% (5건+) | 통계 |
| **R022** | 0.35 | 다중 source 동시 에러 | 3개+ source에서 ERROR | 상관관계 |
| **R023** | 0.25 | 로그 급증 스파이크 | 최근 1분 발생률이 평균 3배+ | 시간윈도우 |
| **R024** | 0.40 | 연결실패→재시작 연쇄 | conn refused 후 5분 내 restart/killed | 순서패턴 |

### Confidence 산출식

```
┌──────────────────────────────────────────────────────────────────────┐
│   base       =  Σ rule.score                                        │
│                                                                      │
│   evidence   =  count ≥ 5 → +0.20  ·  count == 4 → +0.15           │
│                 count == 3 → +0.10  ·  count == 2 → +0.05           │
│                                                                      │
│   interaction (13개 조합)                                             │
│     R001+R004 → +0.15   (timeout × 5xx)                             │
│     R001+R005 → +0.10   (timeout × ERROR)                           │
│     R002+R003 → +0.10   (connection × DNS)                          │
│     R007+R013 → +0.15   (OOM × crash)                               │
│     R008+R001 → +0.12   (DB × timeout)                              │
│     R009+R013 → +0.12   (disk × crash)                              │
│     R010+R001 → +0.10   (CPU × timeout)                             │
│     R019+R022 → +0.15   (에러 버스트 × 다중 source)                  │
│     R019+R021 → +0.12   (에러 버스트 × 높은 에러율)                   │
│     R020+R007 → +0.15   (타임아웃→크래시 × OOM)                      │
│     R024+R022 → +0.15   (연결→재시작 × 다중 source)                  │
│     R021+R008 → +0.12   (높은 에러율 × DB)                           │
│     R023+R019 → +0.10   (급증 × 버스트)                              │
│                                                                      │
│   pattern    = Σ matched_pattern.score  (L2 학습 패턴 점수)           │
│                                                                      │
│   confidence = min(base + evidence + interaction + pattern, 1.0)    │
│                                                                      │
│   severity =  CRITICAL (치명적 조합 or ≥0.85 & 5개+ 룰)              │
│               HIGH     (≥ 0.75 or 크래시/OOM 단독)                    │
│               MEDIUM   (≥ 0.45)                                      │
│               LOW      (< 0.45)                                      │
└──────────────────────────────────────────────────────────────────────┘
```

**검증 자산** — `backend/src/analysis/validation/test_cases.py`(60개 시나리오) · `distribution.py`(분포 리포트) · `tests/test_rule_engine.py`(20개 테스트).

---

## 🔬 Rule Learning (L0~L4)

> 상세 기획 → [`docs/RULE_LEARNING.md`](./docs/RULE_LEARNING.md)

### 파이프라인 요약

```
Raw Log  →  Variable Masking  →  Drain Tree  →  Catalog Upsert (DB)
            (UUID/IP/TS/PATH)     (prefix tree,   (tenant별, 10K 한도)
                                   sim≥0.4)

분석 시:  PatternMatcher  →  카탈로그 조회  →  matched_patterns 응답 포함
피드백:   confirm/dismiss/wrong  →  score_adjust 보정  →  자동 승격/강등
```

### 패턴 상태 머신

```
candidate  ──(label)──▶  labeled  ──(5+ confirm, <20% dismiss)──▶  promoted
    │                       │                                          │
    └──(dismiss)──▶  dismissed  ◀──(dismiss 비율 초과)─────────────────┘
```

### API

```
GET    /patterns              패턴 목록 (status 필터, 페이지네이션)
GET    /patterns/{id}         패턴 상세
PATCH  /patterns/{id}/label   라벨링 (label, causes, actions, score_seed ≤ 0.30)
PATCH  /patterns/{id}/dismiss 무시
POST   /patterns/{id}/feedback  피드백 (confirm/dismiss/wrong → L3 승격 + L4 가중치)
```

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
├── POST   /ingest                 X-Tenant-ID, X-Project-ID 필수, 구조화 파서 + 패턴 마이닝
├── POST   /analysis/test          DB 없이 룰만 실행 (개발/검증용)
└── GET    /health                 DB ping + liveness check

🔐 PROTECTED  (cookie:access_token 필요, tenant 자동 적용)
├── /projects
│   ├── GET    .                   내 tenant 의 프로젝트 목록
│   ├── POST   .                   { name } → ProjectResponse
│   ├── GET    /overview           24h 로그 수 + 에러율 + 최근 분석
│   └── DELETE /{project_id}
│
├── /projects/{project_id}
│   ├── /logs
│   │   ├── POST   .               { source, message, level, timestamp? }
│   │   ├── GET    .               최근 200건 (timestamp desc)
│   │   └── DELETE /{log_id}
│   ├── /analysis
│   │   └── POST   .               { log_ids[], strategy } → AnalysisResultDTO + matched_patterns
│   └── /reports
│       ├── GET    .               목록 (start_date/end_date/limit)
│       ├── GET    /{analysis_id}  단건
│       ├── GET    /weekly         최근 7일 GPT 요약 + 다음주 리스크
│       └── GET    /trend/confidence  일자별 평균 confidence + report_count
│
└── /patterns  (L1~L3 패턴 관리)
    ├── GET    .                   패턴 목록 (status 필터, 페이지네이션)
    ├── GET    /{pattern_id}       패턴 상세
    ├── PATCH  /{pattern_id}/label   라벨링
    ├── PATCH  /{pattern_id}/dismiss 무시
    └── POST   /{pattern_id}/feedback  피드백 (confirm/dismiss/wrong)
```

### 대표 페이로드

**`POST /projects/{id}/analysis`**
```json
// Request
{ "log_ids": ["uuid-1", "uuid-2"], "strategy": "rule" }

// Response
{
  "summary": "룰 기반 분석 결과, 다음과 같은 이상 징후가 감지되었습니다: ...",
  "severity": "HIGH",
  "confidence": 0.85,
  "suspected_causes": ["Upstream 응답 지연", "프록시/게이트웨이 오류"],
  "recommended_actions": ["timeout 설정값 확인", "Upstream 헬스 점검"],
  "matched_rules": ["R001 Timeout 발생 (+0.35) - ...", "R004 5xx ..."],
  "matched_patterns": [
    {
      "pattern_id": "a1b2c3d4e5f6",
      "label": "auth-token-expiry",
      "template": "Auth token expired (<UUID>)",
      "score": 0.25,
      "status": "promoted",
      "history": { "total_count": 47, "avg_severity": "HIGH", "confirm_count": 8 }
    }
  ],
  "strategy_used": "rule",
  "received_at": "2026-05-30T10:11:12Z"
}
```

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
                   │ risk_level/reason   │
                   │ created_at          │
                   └─────────────────────┘

  ┌──────────────────────────┐    ┌──────────────────────────┐
  │  patterns (L0~L4)        │    │  pattern_feedback (L3~L4) │
  │ id (PK, sha1 12자)       │    │ id (PK, auto)             │
  │ tenant_id                │    │ tenant_id                 │
  │ template, sample         │    │ pattern_id (FK)           │
  │ total_count              │    │ analysis_id               │
  │ first_seen, last_seen    │    │ action (confirm/dismiss)  │
  │ sources JSONB            │    │ user_id                   │
  │ level_dist JSONB         │    │ severity_shown            │
  │ hourly_dist INT[]        │    │ created_at                │
  │ status, label, display   │    └──────────────────────────┘
  │ causes TEXT[], actions   │
  │ score_seed, score_adjust │
  │ confirm/dismiss_count    │
  │ created_at, updated_at   │
  └──────────────────────────┘
```

### Enum 정합성

| Enum | Backend | Frontend | Drift |
| --- | --- | --- | --- |
| `LogLevel` | DEBUG / INFO / WARN / ERROR | 동일 | ✅ |
| `SeverityLevel` | LOW / MEDIUM / HIGH / CRITICAL | LOW / MEDIUM / HIGH / CRITICAL | ✅ |
| `AnalysisStrategy` | rule / ai / hybrid / gpt | rule / gpt / ai / hybrid | ✅ |

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
| 의존성 | stdlib + `requests` |
| API | `POST /ingest` (배치 전송, `{logs: [...]}`) |
| Tail 주기 | 1s 폴링 (`os.path.getsize` 기반) |
| 정규화 | BOM, 제어문자 제거 |
| Level 추론 | 본문에서 `ERROR\|WARN\|INFO` 첫 매치 → 없으면 `DEBUG` |
| Agent-side 필터 | level∈{ERROR,WARN} OR `TIMEOUT`/`TIMED OUT` OR HTTP 5xx |
| 헤더 | `X-Tenant-ID`, `X-Project-ID` 부착 |
| Resume | `~/.netscope-agent/` 에 바이트 오프셋 영속화 (재시작 시 이어읽기) |
| 로그 회전 | 파일 truncation 자동 감지 → 오프셋 리셋 |

---

## 🐳 실행 / 배포

### Docker Compose (권장)

```bash
docker compose up -d --build
# Postgres   → localhost:5432
# Backend    → http://localhost:8000  (Swagger: /docs)
# Frontend   → http://localhost:3000
```

### 유틸리티 명령어

```bash
# 데모 시드
docker compose exec backend python -m scripts.seed --reset

# 7일 리텐션 (dry-run → 실행)
docker compose exec backend python -m scripts.retention --dry-run
docker compose exec backend python -m scripts.retention

# 테스트 (43개)
cd backend && .venv/Scripts/python -m pytest tests/ -v

# 룰 분포 확인
docker compose exec backend python -m src.analysis.validation.distribution
```

### 데모 계정 (시드 후 사용 가능)

| Email | Password | Tenant | Projects |
| --- | --- | --- | --- |
| `alice@demo.io` | `Demo1234!` | Alice Co. | `gateway-prod`, `auth-service` |
| `bob@demo.io` | `Demo1234!` | Bob Industries | `billing-api`, `worker-queue` |
| `carol@demo.io` | `Demo1234!` | Carol Labs | `edge-cdn`, `checkout-flow` |

---

## 🚨 알려진 갭 / 로드맵

```
우선  영역                          상태   비고
────  ────────────────────────────  ────   ────────────────────────
🟡    프론트엔드 대시보드 완성         미완   분석 결과 시각화, 패턴 카드 등
🟡    /patterns 프론트엔드 페이지     미착수  백엔드 API 완료, UI 미구현
🟡    Agent 환경변수화               미착수  API_URL, OFFSET_DIR 설정 가능하게
🟡    Alembic initial revision       미착수  DB 연결 후 autogenerate 필요
🟡    통합 테스트 (auth+analysis)     미착수  e2e 테스트
❌    L5 임베딩 기반 의미 유사도       장기   sentence-transformer + HDBSCAN
```

---

```
                        ─── netscope-ai · README.md ───
                       last sync : 2026-05-30
```
