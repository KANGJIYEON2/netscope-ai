# 🔭 Netscope-AI — 에이전트 작업 가이드 (CLAUDE.md)

> **이 파일은 Claude/기여자가 코드를 만질 때 보는 작업용 요약본**입니다.
> 아키텍처 다이어그램·API 페이로드·룰 카탈로그·데이터 모델 등 **상세 레퍼런스는 → [`README.md`](./README.md)** 와 `docs/` 를 보세요.

```
NETSCOPE-AI · Explainable Log Diagnostics
Stage : MVP++  (Auth · DB · Multi-tenant · L0~L4 · 실시간 SSE · Fleet UI · GPT 보고서 · 조사/학습)
Stack : FastAPI · SQLAlchemy · Postgres 16 · Next.js 16 · React 19 · ECharts · Tailwind 4 · zustand
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
             ── 이번 사이클 추가 ──
             Fleet 대시보드(ECharts: 이슈보드/라이브피드/재발이슈/헬스그리드) · 공유 AppShell
             프로젝트 상세 4탭(Overview/Logs/Analyses/Patterns) · /patterns UI
             GPT 구조화 보고서(JSON: summary + report_sections) · GPT 실제 활성화(.env.docker)
             조사/해결(Investigation): status·resolution·notes + 유사 사례 학습 추천
             실시간 SSE(/events/stream): ingest→완전 분석 저장→브라우저 즉시 갱신
             Agent 신뢰성/배포(env·X-API-Key·offset-on-success·systemd)
🟡 PARTIAL   SSE broker 멀티워커(현 in-memory 단일 프로세스) · Alembic revision(신규 컬럼은 수동 ALTER)
❌ 없음       L5 임베딩 의미 유사도 · Agent 단일 바이너리(PyInstaller) · auth+analysis e2e
```

> ⚠️ **코드를 고치기 전에**: 위에서 건드리는 영역이 🟡/❌ 면, "원래 동작했는데 내가 깼다" 가 아니라 "원래 미완" 일 가능성이 높다. README 의 상태표를 함께 확인.
> ⚠️ **DB 스키마**: `analysis_results`에 `report_sections·investigation_status·resolution·notes` 컬럼은 **수동 `ALTER TABLE`** 로 추가됨(create_all은 기존 테이블에 컬럼 추가 안 함). 새 환경은 `seed.py --reset` 시 모델 정의대로 생성됨.

---

## 📁 2. 어디에 무엇이 있나 (디렉터리 맵)

```
backend/src/
├── main.py                 FastAPI 부트 · CORS(cors_origins) · 라우터 11개 등록 (+events)
├── api/v1/
│   ├── dep.py              get_current_context — 쿠키 JWT → {user_id, tenant_id}  ★모든 보호 라우트가 의존
│   ├── auth.py             /auth/{register,login,refresh,logout}
│   ├── projects.py         /projects (list/create/overview/delete)
│   ├── logs.py             /projects/{id}/logs
│   ├── analysis.py         /projects/{id}/analysis (저장+weekly+패턴) ★+조사: /{id}/{investigation,notes,similar}
│   ├── reports.py          /projects/{id}/reports/{,weekly,trend/confidence,{id}}  (+id·investigation·report_sections 노출)
│   ├── ingest.py           /ingest  (헤더 tenant/project + 옵션 X-API-Key, raw 비저장)
│   ├── patterns.py         /patterns (list/detail/label/dismiss/feedback) ← L1~L3
│   ├── events.py           ★GET /events/stream  SSE 라이브 스트림 (cookie 인증, tenant별)
│   ├── test.py             /analysis/test  (DB 없이 룰+GPT)
│   └── health.py           /health (DB ping + liveness)
├── core/                   config.py(cors_origins·OPENAI_API_KEY·INGEST_API_KEY) · jwt · security(argon2) · logging
├── db/                     base · session(get_db) · deps · init(create_all)
├── domain/                 auth · log · project  ← ★쓰기/도메인 로직은 여기로 위임 (모범 사례)
├── realtime/               ★ broker.py — in-memory 이벤트 broker(단일 프로세스). publish/since/latest_id
├── ingest/
│   ├── service.py          ingest_logs: 패턴마이닝(L0) + engine으로 ★완전한 분석 저장(strategy=agent) + broker.publish
│   ├── parser.py           구조화 파서 (JSON/KV/syslog/plain 자동감지)
│   ├── aggregator.py·persist.py·signals.py   ⚠️ 더 이상 호출 안 함(persist가 summary 없이 insert→500 버그라 제거)
├── analysis/
│   ├── engine.py           오케스트레이션 (Rule → GPT → severity → DTO + report_sections). ★ORM 모름
│   ├── rule_engine.py      R001~R024 v3.0 + interaction_bonus(13개) + 시간/통계 헬퍼
│   ├── gpt_analyzer.py     ★JSON 모드 구조화 출력 (summary + report_sections[{title,body}]), 모델 gpt-4o-mini
│   ├── gpt_weekly.py · weekly_service.py    주간 요약/리스크
│   └── validation/         test_cases.py(60·결정적 타임스탬프) · distribution.py
├── learning/               ★ Rule Learning L0~L4
│   ├── masking.py          변수 마스킹 (UUID/IP/TS/PATH/B64/NUM 등)
│   ├── drain.py            Drain 트리 (온라인 로그 템플릿 추출)
│   ├── catalog.py          카탈로그 upsert (DB 영속화)
│   ├── matcher.py          패턴 매칭 (분석 시 카탈로그 조회)
│   ├── promotion.py        자동 승격/강등 (confirm/dismiss 비율)
│   └── weight_learner.py   온라인 score_adjust (안전 가드 포함)
├── model/                  User · Tenant · refresh_token · Project · log · weekly_report · pattern · pattern_feedback
│                           · analysis_result (+report_sections·investigation_status·resolution·notes)
├── schemas/                enums(LogLevel·SeverityLevel·AnalysisStrategy) · auth · project · log · ingest
│                           · analysis (+report_sections·investigation_status·resolution·notes·id, InvestigationUpdateDTO·NoteCreateDTO)
├── scripts/
│   ├── seed.py             3 tenants × 2 projects × 18 logs (--reset)
│   ├── seed_big.py         ★대량 backdate 시드 (--analyses/--logs/--days/--purge, strategy='bulk' 태그)
│   └── retention.py        7일 리텐션 cleanup (--days N --dry-run)
└── alembic/                Alembic 초기 설정 (신규 컬럼은 수동 ALTER로 반영)

frontend/src/
├── app/                    page(→/dashboard) · auth/{login,register}
│   ├── dashboard/          ★Fleet 커맨드 (page + components/: useFleetData·KpiCard·ProjectsHealthGrid·IssuesBoard·ActivityFeed·TopIssues·RecentAnalyses·WeeklyHero·AnimatedNumber)
│   ├── projects/[id]/      layout(탭바+LIVE) · page(Overview) · logs · analyses · patterns · components/LogActivity
│   ├── components/Layout/AppShell.tsx   ★공유 셸(사이드바+글로우, 전 페이지 공통)
│   ├── components/charts/  ★EChart 래퍼 + ConfidenceTrend·ConfidenceGauge·SeverityDonut (ECharts)
│   ├── components/ui/Card.tsx · components/investigation/InvestigationPanel.tsx
│   └── analysis/AnalysisResult.tsx      ★보고서 레이아웃(요약+섹션+원인/조치 카드)
├── lib/api/client.ts       ★axios: withCredentials + 401 silent-refresh interceptor
├── lib/api/                auth · project · log · analysis · report(+trend) · overview · patterns(+mutations) · investigation
├── lib/useLiveEvents.ts    ★EventSource(/events/stream) 훅 + useProjectLiveRefresh(프로젝트별 자동 갱신)
├── lib/time.ts             timeAgo · ruleIdOf
├── types/{analysis,log}.ts Severity·Strategy + ReportSection·InvestigationStatus·InvestigationNote
└── styles/severity.ts      ★severity→color 정본 + 차트용 hex/gradient (cyan/amber/red/fuchsia, 다크테마)

backend/netscope-agent/
├── netscope-agent.py       POST /ingest 배치 · env화(API_URL/KEY/OFFSET_DIR) · ★전송 성공 시에만 offset 전진 · 로그 회전
└── netscope-agent.service  systemd 유닛 (EnvironmentFile 기반 배포)
```

---

## 🧭 3. 작업 컨벤션 (지키지 않으면 머지 보류)

- **언어** — 코드 주석/식별자는 영어, 도메인 문서/기획서는 한국어 가능. 라우터의 한국어 주석은 유지.
- **레이어 경계**
  - 라우터에서 **읽기 query 직접 허용** (분석/리포트 라우터가 그렇게 함).
  - **쓰기/도메인 로직은 `domain/*DomainService` 로 위임** (auth/log/project 가 모범).
  - `analysis/engine.py` 는 **ORM 을 모른다** — `RuleLog`(frozen dataclass) 만 받는다. 여기에 ORM import 하지 말 것.
  - 패턴 매칭(L2)은 **라우터(analysis.py)에서** DB 조회 후 결과를 합침 — engine.py 에 ORM 넣지 않기 위함.
  - **ingest는 완전한 분석을 저장한다** — `ingest/service.py`가 engine으로 분석 후 `summary/severity` 포함 `AnalysisResult`를 저장(`strategy_used="agent"`)하고 `broker.publish`. (예전 `aggregator/persist`는 summary 없이 insert→500이라 호출 제거됨. 되살리지 말 것.)
  - **실시간 이벤트** — DB 변화를 화면에 즉시 반영하려면 `realtime/broker.publish({type,tenant_id,project_id,...})`. SSE 구독자는 tenant로 필터. 멀티워커면 in-memory broker는 못 씀(Redis/LISTEN 필요).
  - **조사/해결(Investigation)** — `analysis_results`의 `investigation_status/resolution/notes`에 사람이 기록. 학습 추천은 `matched_rules` 교집합 쿼리(`GET /analysis/{id}/similar`).
- **Tenant 강제** — 보호 라우트는 항상 `Depends(get_current_context)` → `ctx["tenant_id"]`(+`project_id`) 로 query 필터. cross-tenant 접근 차단이 보안의 핵심.
- **룰 추가 시** ①`rule_engine.py::default_rules()` 에 `Rule(...)` ②필요 시 `interaction_bonus()` 조합 ③`validation/test_cases.py` 양/음성 케이스 ④`tests/test_rule_engine.py` 에 테스트 추가 ⑤`distribution.py` 로 분포 회귀 확인.
- **DTO 변경 시** — `backend/src/schemas/*` 와 `frontend/src/types/*` **양쪽 동기화 필수** (특히 Severity / Strategy).
- **GPT enrichment** — system prompt 의 *"rule-engine analysis is the baseline. Do NOT contradict rules…"* 문구는 **유지**. 빼면 결정성/재현성 깨짐.
- **Agent** — stdlib + `requests` 만. 의존성 추가 신중.
- **DB 스키마 변경** — Alembic은 설정만 됨(적용 revision 없음). **현실: 신규 컬럼은 수동 `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`** 로 기존 DB에 반영 + 모델에도 추가(새 환경 create_all 용). 데이터 보존이 필요하면 `seed.py --reset` 금지.
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
| **Trend** | `/reports/trend/confidence` → ECharts 그라데이션 area + 글로우 + 임계선(0.45 / 0.75) |
| **GPT 보고서** | summary(간결) → `report_sections` 번호 블록 → 원인/조치 카드 → 룰 칩 (AnalysisResult.tsx) |
| **조사/해결** | 상태칩 + 실제원인 입력 + 메모 타임라인 + 📌 유사 해결사례 (InvestigationPanel) |
| **Weekly Report** | 헤더에 기간 + report_count + risk_outlook 색상 그라데이션 배경 |
| **Causes / Actions** | 불릿 X — 아이콘 + 카드 grid, 길면 collapse |
| **Empty / Loading** | 평문 X — 일러스트/아이콘 + CTA 버튼 |
| **실시간** | SSE 이벤트 수신 시 자동 갱신 + `LIVE` 펄스 배지 + 토스트 |
| **다크 테마** | `zinc-950` 배경 위에서 색이 살아야 함 — Tailwind `*-400`/`*-500` 톤 |

권장: **차트 `echarts`(채택 — framework-agnostic, React19 안전 래핑 `components/charts/EChart.tsx`)** · 아이콘 `lucide-react` · 모션 `framer-motion` · **컬러 매핑은 `frontend/src/styles/severity.ts` 에 정본 통일** (hex/gradient 포함, 컴포넌트 하드코딩 금지). 상세 → [`docs/DESIGN_SYSTEM.md`](./docs/DESIGN_SYSTEM.md).

---

## 🚀 5. 자주 쓰는 명령어

```bash
# 전체 스택 (postgres + backend + frontend, hot reload)
docker compose up -d --build

# 데모 데이터 시드  (alice/bob/carol @demo.io · PW Demo1234!)
docker compose exec backend python -m scripts.seed --reset

# 대량 데모 데이터 (트렌드/이슈/라이브피드용 — 14일 backdate)
docker compose exec backend python -m scripts.seed_big          # 증강(원본 보존)
docker compose exec backend python -m scripts.seed_big --purge  # 벌크만 제거

# 룰 분포 회귀 확인 (룰 변경 후 필수)
docker compose exec backend python -m src.analysis.validation.distribution

# 테스트 실행 (43개)
docker compose exec backend python -m pytest tests/ -v

# 7일 리텐션 cleanup (dry-run 먼저)
docker compose exec backend python -m scripts.retention --dry-run
docker compose exec backend python -m scripts.retention

# GPT 켜기: backend/.env.docker 에 OPENAI_API_KEY 채우고 → 백엔드 재생성
docker compose up -d --force-recreate backend

# 신규 컬럼 수동 반영 예시 (데이터 보존)
docker compose exec postgres psql -U netscope -d netscope -c \
  "ALTER TABLE analysis_results ADD COLUMN IF NOT EXISTS <col> <type>;"

# 실시간 데모: /dashboard 열어둔 채 ingest 한 방 (X-Tenant-ID/X-Project-ID 헤더)
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

## 🛰️ 8. 실시간 / 조사 흐름 요약

```
실시간(SSE):  agent/ingest → engine 완전 분석 저장(strategy=agent) → realtime.broker.publish
              → GET /events/stream (cookie, tenant 필터) → 프론트 EventSource → 자동 갱신+토스트
              훅: lib/useLiveEvents.ts (대시보드) · useProjectLiveRefresh (프로젝트 탭)
              broker = in-memory(단일 프로세스). 멀티워커면 Redis/Postgres LISTEN으로 교체.

조사/해결:     analysis_results.{investigation_status, resolution, notes}
              PATCH /analysis/{id}/investigation · POST /analysis/{id}/notes
              학습: GET /analysis/{id}/similar — matched_rules 교집합 큰 'resolved' 사례 추천
```

---

## 🚧 9. 남은 작업 (우선순위)

```
🟡  SSE broker 멀티워커 대응 (Redis pub/sub 또는 Postgres LISTEN/NOTIFY)
🟡  Alembic initial revision (현재 신규 컬럼은 수동 ALTER)
🟡  통합 테스트 (auth + analysis + ingest/SSE e2e)
🟡  Agent 단일 바이너리 (PyInstaller) + INGEST_API_KEY 운영 적용
❌  L5 임베딩 기반 의미 유사도 (sentence-transformer + HDBSCAN)
```

---

```
─── netscope-ai · CLAUDE.md (agent guide) · last sync 2026-05-30 ───
상세 정본은 README.md + docs/ 를 신뢰. 이 파일은 빠른 작업 컨텍스트용.
```
