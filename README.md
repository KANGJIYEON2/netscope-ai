# 🔭 Netscope-AI — Explainable Log Diagnostics

```
╔══════════════════════════════════════════════════════════════════════════════╗
║   NETSCOPE-AI                                                                ║
║   Explainable Network/Application Log Diagnostics                            ║
║                                                                              ║
║   Stage  : MVP++  (Auth · DB · Multi-tenant · L0~L4 · 실시간 SSE · Fleet UI)   ║
║   Stack  : FastAPI · SQLAlchemy · Postgres · Next.js 16 · ECharts · Tailwind 4 ║
║   Theme  : "왜 그렇게 판단했는가" 를 룰 ID + 학습 패턴 + 근거 + 점수로 노출       ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

> **한 줄 요약**: 로그 묶음을 **Rule Engine v3.0 (R001~R024) + Pattern Learning (L0~L4) + 선택적 GPT 보강** 으로 분석해,
> 매칭된 룰 ID·학습 패턴·근거·신뢰도·심각도까지 함께 응답하는 **설명 가능한** 진단 시스템.
> 에이전트가 보낸 로그는 **실시간(SSE)** 으로 **Fleet 대시보드**에 즉시 반영되고,
> GPT 보강 시 **보고서급 구조화 출력**, 사람이 남긴 **조사/해결 기록**은 유사 사례 학습으로 이어진다.

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
🟢 GPT 보고서 (구조화)       DONE      JSON 모드 — 간결 summary + report_sections[{title,body}] 상세 본문
🟢 조사/해결 (Investigation) DONE      상태·실제원인·메모 타임라인 + 룰 교집합 유사 해결사례 학습 추천
🟢 실시간 SSE 푸시           DONE      /events/stream — ingest→완전 분석 저장→브라우저 즉시 반영
🟢 Frontend Fleet 대시보드   DONE      ECharts — 이슈 보드·라이브 피드·재발 이슈·프로젝트 헬스
🟢 프로젝트 상세 탭          DONE      Overview/Logs/Analyses/Patterns + 공유 AppShell
🟢 패턴 관리 UI             DONE      /projects/{id}/patterns 탭 — label/dismiss/feedback
🟢 Agent 신뢰성/배포        DONE      env화 + X-API-Key + 전송 성공 시에만 offset 전진 + systemd
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
│  🤖  NETSCOPE AGENT   (backend/netscope-agent/netscope-agent.py · systemd 유닛)  │
│    · BOM/제어문자 정리 · level 자동 감지 (ERROR/WARN/INFO/DEBUG)                  │
│    · Agent-side filter v0: ERROR / WARN / TIMEOUT / 5xx 만 통과                  │
│    · X-Tenant-ID / X-Project-ID / X-API-Key 헤더 부착                            │
│    · 환경변수화: NETSCOPE_API_URL / API_KEY / OFFSET_DIR (CLI 오버라이드)         │
│    · POST /ingest 배치 전송 · ★전송 성공 시에만 offset 전진(실패 시 재시도)        │
│    · 오프셋 영속화 · 로그 회전(truncation) 자동 감지                              │
└──────────────────────────────┬──────────────────────────────────────────────────┘
                               │ HTTP JSON  (+headers, X-API-Key 옵션)
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
│   │  → 구조화 파서 → PatternMiner(L0)│  │  list/label/dismiss/feedback     │     │
│   │  → RuleEngine 분석 → ★완전한      │  └─────────────────────────────────┘     │
│   │    AnalysisResult 저장(strategy= │  ┌─────────────────────────────────┐     │
│   │    agent) → broker.publish       │  │  GET /events/stream  (SSE)      │     │
│   │  (X-API-Key 옵션 인증)            │  │  ★cookie 인증 · tenant별 라이브  │     │
│   └──────────────────────────────────┘  │  푸시 → 브라우저 즉시 갱신        │     │
│   ┌──────────────────────────────────┐  └─────────────────────────────────┘     │
│   │  GET /projects/overview          │  ┌─────────────────────────────────┐     │
│   │  (24h 로그수/에러율/최근분석)       │  │  GET /health (DB ping)          │     │
│   └──────────────────────────────────┘  └─────────────────────────────────┘     │
│   ┌──────────────────────────────────────────────────────────────────────┐      │
│   │  조사/해결: PATCH .../investigation · POST .../notes · GET .../similar │      │
│   │  (상태·실제원인·메모 타임라인 + 룰 교집합 유사 해결사례 학습)             │      │
│   └──────────────────────────────────────────────────────────────────────┘      │
│                                                                                 │
│   ┌─── AnalysisEngine.analyze() ────────────────────────────────────────┐       │
│   │  ① RuleEngine v3.0 (R001~R024)                                     │       │
│   │  ② PatternMatcher (L2 — 학습 패턴 매칭)                             │       │
│   │  ③ (옵션) GPTAnalyzer  ← strategy=gpt 이고 OPENAI_API_KEY 있을 때    │       │
│   │     JSON 구조화: 간결 summary + report_sections[{title,body}] 상세    │       │
│   │  ④ severity 자동 매핑 (CRITICAL/HIGH/MEDIUM/LOW)                     │       │
│   │  ⑤ AnalysisResult DB 저장 + matched_patterns + report_sections       │       │
│   │  ⑥ 주간 리포트 자동 트리거: 최근 7일 ≥5건 + 미존재 → 생성              │       │
│   └────────────────────────────────────────────────────────────────────┘       │
└───────────────────────────────┬─────────────────────────────────────────────────┘
                                │  SQLAlchemy ORM
                                ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  🐘  POSTGRES 16   (docker-compose · postgres_data volume)                       │
│      tenants · users · refresh_tokens · projects                                │
│      logs · analysis_results (+report_sections·investigation_status·            │
│            resolution·notes) · weekly_reports                                   │
│      patterns · pattern_feedback  ← L0~L4                                       │
└─────────────────────────────────────────────────────────────────────────────────┘

  🛰️  실시간(SSE): ingest → broker.publish → GET /events/stream → 브라우저 EventSource
  🖥️  FRONTEND(Next.js 16 · ECharts): /dashboard(Fleet 커맨드) + /projects/{id}/{Overview,
      Logs,Analyses,Patterns} — 공유 AppShell, 전 화면 SSE 라이브 갱신
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

## 📝 GPT 구조화 보고서 · 🔎 조사/해결 학습 · 🛰️ 실시간

### GPT 구조화 보고서 (`strategy=gpt` + `OPENAI_API_KEY`)
`gpt_analyzer.py`가 **JSON 모드**로 응답 → 룰 결과를 baseline으로 유지하며 보고서급 출력 생성.
```
summary          : 2~3문장 간결 머리말
report_sections  : [{title, body}] — 현상요약 / 근본원인 / 영향범위 / 진단근거 / 다음단계
                   (한국어, 섹션당 2~5문장 · 마크다운/불릿 금지)
```
실패/파싱 오류 시 **룰 결과로 안전 폴백**. 프론트는 `AnalysisResult.tsx`에서 요약→번호 섹션→
원인/조치 카드→룰 칩 순의 "진짜 보고서" 레이아웃으로 렌더.

### 조사 & 해결 (Investigation) — 사후 기록 + 학습
분석 보고서별로 사람이 조사 현황/실제 원인을 남기고, 그게 쌓여 유사 사례 추천으로 이어진다.
```
status      : open → investigating → resolved (또는 false_positive)
resolution  : 실제 규명된 원인  예) "프론트엔드 nginx rewrite 경로 설정 오류"
notes       : 메모 타임라인 [{at, text}]  예) "10:30 재현 · 11:00 수정"
학습 추천   : 같은 matched_rules 교집합으로 'resolved' 된 과거 분석의 resolution을
              GET /analysis/{id}/similar 로 추천 (룰 교집합 큰 순)
```
프론트: 분석 행 펼치면 InvestigationPanel(상태칩·실제원인·메모·📌유사 사례) — Overview/Analyses 탭.

### 실시간 (SSE 서버 푸시)
```
에이전트/ingest ─▶ 완전한 AnalysisResult 저장 ─▶ broker.publish(tenant별 이벤트)
브라우저 ◀─ EventSource GET /events/stream ─ 이벤트 즉시 수신 ─▶ 화면 자동 갱신 + 토스트
```
- Fleet 대시보드 + 프로젝트 전 탭이 자기 tenant/project 이벤트에 반응해 **새로고침 없이** 갱신.
- broker는 **in-memory(단일 프로세스)** — 멀티워커 배포 시 Redis pub/sub 또는 Postgres LISTEN/NOTIFY로 교체.
- ⚠️ 과거 `aggregator/persist`가 summary 없이 행을 insert해 `/ingest`가 항상 500이던 버그를 이 과정에서 수정.

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
├── POST   /ingest                 X-Tenant-ID/Project-ID 필수, (옵션)X-API-Key
│                                  → 완전한 분석 저장 + SSE 이벤트 publish
├── POST   /analysis/test          DB 없이 룰(+GPT) 실행 (개발/검증용)
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
│   │   ├── POST   .                       { log_ids[], strategy } → AnalysisResultDTO
│   │   │                                  (+matched_patterns +report_sections)
│   │   ├── PATCH  /{id}/investigation      { status?, resolution? } 조사 상태/실제 원인
│   │   ├── POST   /{id}/notes              { text } 메모 타임라인 append
│   │   └── GET    /{id}/similar            룰 교집합 기반 과거 '해결됨' 사례 추천(학습)
│   └── /reports
│       ├── GET    .               목록 (start_date/end_date/limit)
│       ├── GET    /{analysis_id}  단건
│       ├── GET    /weekly         최근 7일 GPT 요약 + 다음주 리스크
│       └── GET    /trend/confidence  일자별 평균 confidence + report_count
│
├── /patterns  (L1~L3 패턴 관리)
│   ├── GET    .                   패턴 목록 (status 필터, 페이지네이션)
│   ├── GET    /{pattern_id}       패턴 상세
│   ├── PATCH  /{pattern_id}/label   라벨링
│   ├── PATCH  /{pattern_id}/dismiss 무시
│   └── POST   /{pattern_id}/feedback  피드백 (confirm/dismiss/wrong)
│
└── GET    /events/stream          ★SSE 라이브 스트림 (cookie 인증, tenant별 푸시)
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
  "report_sections": [          // strategy=gpt 일 때 GPT가 채우는 상세 보고서 본문
    { "title": "현상 요약",   "body": "..." },
    { "title": "근본 원인 분석", "body": "..." }
  ],
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
  "investigation_status": "open",   // open | investigating | resolved | false_positive
  "resolution": null,               // 사람이 기록한 실제 원인
  "notes": [],                      // 메모 타임라인 [{at, text}]
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
└──────────────┘   │ report_sections JSONB│            │
                   │ strategy_used       │             │
                   │ investigation_status│  ← 조사/해결 │
                   │ resolution (text)   │             │
                   │ notes JSONB         │             │
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
# 환경변수 (CLI 플래그로 오버라이드 가능)
export NETSCOPE_API_URL=https://netscope.example.com/ingest
export NETSCOPE_API_KEY=<백엔드 INGEST_API_KEY와 동일한 공유 비밀>   # 옵션
python netscope-agent.py --path /var/log/app.log \
                         --source gateway \
                         --tenant <tenant_uuid> \
                         --project <project_uuid>

# 리눅스 상시 구동: systemd 유닛 동봉 (netscope-agent.service)
#   /etc/netscope/agent.env 에 위 변수 + LOG_PATH/SOURCE/TENANT/PROJECT 채움
#   sudo systemctl enable --now netscope-agent
```

| 항목 | 값 |
| --- | --- |
| 의존성 | stdlib + `requests` |
| API | `POST /ingest` (배치 전송, `{logs: [...]}`) |
| 설정 | `NETSCOPE_API_URL` / `NETSCOPE_API_KEY` / `NETSCOPE_OFFSET_DIR` (env, CLI 우선) |
| Tail 주기 | 1s 폴링 (`os.path.getsize` 기반) |
| 정규화 | BOM, 제어문자 제거 |
| Level 추론 | 본문에서 `ERROR\|WARN\|INFO` 첫 매치 → 없으면 `DEBUG` |
| Agent-side 필터 | level∈{ERROR,WARN} OR `TIMEOUT`/`TIMED OUT` OR HTTP 5xx |
| 헤더 | `X-Tenant-ID`, `X-Project-ID`, `X-Agent-ID`, (옵션)`X-API-Key` |
| ★신뢰성 | **전송 성공(2xx) 시에만 offset 전진** → 백엔드 장애 시 무손실 재시도 |
| Resume | `~/.netscope-agent/` 바이트 오프셋 영속화 (재시작 시 이어읽기) |
| 로그 회전 | 파일 truncation 자동 감지 → 오프셋 리셋 |
| 배포 | `netscope-agent.service` (systemd) 동봉 |

---

## 🐳 실행 / 배포

### Docker Compose (권장)

```bash
docker compose up -d --build
# Postgres   → localhost:5432
# Backend    → http://localhost:8000  (Swagger: /docs)
# Frontend   → http://localhost:3000  (→ /dashboard 리다이렉트)
```

### 환경변수 (`backend/.env.docker` — git 미추적)

| 변수 | 용도 |
| --- | --- |
| `OPENAI_API_KEY` | 채우면 `strategy=gpt` 활성화(구조화 보고서). 비우면 룰만 |
| `INGEST_API_KEY` | 채우면 `/ingest`가 `X-API-Key` 헤더 요구(에이전트 인증). 비우면 미적용 |
| `SECRET_KEY` · `FRONTEND_ORIGIN` | JWT 서명 · CORS 화이트리스트(콤마 구분) |

### 유틸리티 명령어

```bash
# 데모 시드 (3 tenants × 2 projects × 18 logs)
docker compose exec backend python -m scripts.seed --reset

# 대량 데모 데이터 (트렌드/이슈/피드용 — 14일 backdate, 프로젝트당 28분석·70로그)
docker compose exec backend python -m scripts.seed_big           # 증강(원본 보존)
docker compose exec backend python -m scripts.seed_big --purge   # 벌크만 제거(strategy='bulk')

# 7일 리텐션 (dry-run → 실행)
docker compose exec backend python -m scripts.retention --dry-run
docker compose exec backend python -m scripts.retention

# 테스트 (43개)
docker compose exec backend python -m pytest tests/ -v

# 룰 분포 확인 (룰 변경 후 필수)
docker compose exec backend python -m src.analysis.validation.distribution
```

### 실시간(SSE) 데모

```bash
# /dashboard 를 열어둔 채, 에이전트가 보낸 것처럼 한 방 쏘면 새로고침 없이 반영됨
curl -X POST http://localhost:8000/ingest \
  -H "X-Tenant-ID: <tenant>" -H "X-Project-ID: <project>" \
  -H "Content-Type: application/json" \
  -d '{"logs":["ERROR gw timeout 30000ms","ERROR app OutOfMemoryError"]}'
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
🟢    프론트엔드 Fleet 대시보드        완료   ECharts 이슈보드/라이브피드/헬스그리드
🟢    /patterns UI                   완료   프로젝트 Patterns 탭 (label/dismiss/feedback)
🟢    Agent 환경변수화/신뢰성         완료   env + X-API-Key + offset-on-success + systemd
🟢    실시간 SSE 푸시                 완료   /events/stream — 전 화면 라이브 갱신
🟢    GPT 구조화 보고서               완료   간결 summary + report_sections 상세
🟢    조사/해결(Investigation) 학습   완료   상태·실제원인·메모 + 유사 사례 추천
🟡    SSE 멀티워커 확장              미착수  현재 in-memory broker(단일 프로세스) → Redis/LISTEN
🟡    Alembic initial revision       미착수  현재 신규 컬럼은 수동 ALTER로 반영
🟡    통합 테스트 (auth+analysis e2e) 미착수  엔드투엔드
🟡    Agent 단일 바이너리            미착수  PyInstaller 패키징
❌    L5 임베딩 기반 의미 유사도       장기   sentence-transformer + HDBSCAN
```

---

```
                        ─── netscope-ai · README.md ───
                       last sync : 2026-05-30
```
