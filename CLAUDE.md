# Netscope-AI — 프로젝트 컨텍스트 (CLAUDE.md)

> **한 줄 요약**: 네트워크/애플리케이션 로그를 **룰 엔진 + 선택적 LLM**으로 분석해, 매칭된 룰 ID·근거·신뢰도까지 함께 노출하는 **설명 가능한** 진단 시스템.
> 현재 단계는 **MVP / PoC** — 룰 엔진·GPT 보강·프론트 표시까지 동작, DB 영속화·인증·멀티테넌시 등은 미연결.

PM 고도화 기획안은 별도 파일: [`docs/PM_ENHANCEMENT_PLAN.md`](./docs/PM_ENHANCEMENT_PLAN.md)

---

## 1. 시스템 다이어그램

```
┌─────────────────────────────────────────────────────────────┐
│ 애플리케이션 / OS 로그 (stdout, stderr, syslog)               │
└────────────────────────────┬────────────────────────────────┘
                             │ tail -f
                             ▼
┌─────────────────────────────────────────────────────────────┐
│ NETSCOPE AGENT  (backend/netscope-agent/netscope-agent.py)  │
│  · 1초 폴링 tail · BOM/제어문자 정리 · level 자동 감지        │
│  · 1차 필터: ERROR / WARN / TIMEOUT / 5xx 만 전송            │
│  · POST /logs (host, source 포함)                           │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP JSON
                             ▼
┌─────────────────────────────────────────────────────────────┐
│ BACKEND  (FastAPI · backend/src)                            │
│   POST/GET /logs   →  LogService → InMemoryLogStorage       │
│   POST /analysis   →  AnalysisEngine                        │
│                        ① RuleEngine (R001~R006)             │
│                        ② (옵션) GPTAnalyzer                  │
│                        ③ severity 매핑 (LOW/MEDIUM/HIGH)     │
└────────────────────────────┬────────────────────────────────┘
                             │ 3초 폴링 / 분석 요청
                             ▼
┌─────────────────────────────────────────────────────────────┐
│ FRONTEND (Next.js 16 · React 19 · Tailwind 4)               │
│  · 실시간 로그 리스트  · Strategy 선택 (Rule/GPT)             │
│  · severity 배지 + confidence + matched_rules 표시           │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 디렉터리 매핑

```
backend/src/
├── main.py                     FastAPI 부트, CORS, 라우터 등록
├── api/v1/
│   ├── logs.py                 POST/GET /logs
│   ├── analysis.py             POST /analysis
│   └── health.py               (스텁)
├── log/
│   ├── service.py              LogService — storage 래퍼
│   ├── models.py               Log dataclass (메모리)
│   └── parser.py               (스텁)
├── analysis/
│   ├── engine.py               오케스트레이션 (Rule → GPT → severity)
│   ├── rule_engine.py          R001~R006 + 점수 + 상호작용 보너스
│   ├── gpt_analyzer.py         OpenAI 호출 (옵션)
│   ├── result.py               결과 결합 헬퍼
│   └── validation/             50개 시나리오 + 분포 검증 스크립트
├── schemas/                    Pydantic DTO + Enum (Strategy, Severity, Level)
├── model/                      SQLAlchemy ORM (Log, AnalysisResult) — ⚠️ 미연결
├── repositories/               analysis_repository — ⚠️ 라우터에서 미호출
├── infrastructure/
│   ├── storage.py              InMemoryLogStorage (싱글톤, 동작)
│   ├── database.py             ⚠️ 스텁
│   └── redis.py                ⚠️ 스텁
└── core/                       config / logging / security 모두 스텁

backend/netscope-agent/
└── netscope-agent.py           149줄, stdlib + requests, 단일 스크립트

frontend/src/
├── app/
│   ├── page.tsx                상태 + 3초 폴링 + 분석 호출
│   ├── layout.tsx              dark 테마 (zinc-950)
│   └── components/
│       ├── analysis/{AnalysisResult, StrategySelect}.tsx
│       └── logs/{AgentStatus, LogForm, LogList}.tsx
├── lib/
│   ├── api/{analysis,log}.ts   axios 래퍼
│   └── config.ts               API_BASE_URL (NEXT_PUBLIC_*)
├── types/{analysis,log}.ts
└── styles/severity.ts          ⚠️ 스텁 (색은 컴포넌트에 하드코딩)
```

---

## 3. 핵심 가치 — 룰 엔진 (R001~R006)

| 룰 | 점수 | 트리거 | 주요 cause | 주요 action |
| --- | --- | --- | --- | --- |
| **R001** Timeout | 0.35 | `TIMEOUT`, `ETIMEDOUT`, `timed out` | upstream 지연·네트워크 손실·과부하 | timeout 설정·upstream 헬스 |
| **R002** Connection | 0.35 | `ECONNREFUSED`, `connection reset` | 포트 미LISTEN·방화벽·프로세스 다운 | 포트 점검·FW 룰·서비스 헬스 |
| **R003** DNS | 0.25 | `ENOTFOUND`, `NXDOMAIN`, `getaddrinfo` | 레코드 누락·resolver 장애 | A/AAAA 확인·dig/nslookup |
| **R004** 5xx | 0.25 | `502`, `503`, `504` | upstream 오류·게이트웨이 오류·트래픽 폭주 | upstream/proxy 로그·오토스케일 |
| **R005** ERROR-level | 0.20 | level=ERROR | 앱/시스템 에러 | 타임라인 상관관계·배포 이력 |
| **R006** Repeated source | 0.20 | 같은 source ≥5회 | 컴포넌트 루프·재시도 무한 | 상세 로그·circuit breaker |

### 점수식
```
base       = Σ(매칭된 룰의 점수)
evidence   = +0.15 (룰 4+) | +0.10 (3) | +0.05 (2) | 0
interaction= +0.15 (R001+R004) | +0.10 (R001+R005 또는 R002+R003)
confidence = min(base + evidence + interaction, 1.0)
severity   = HIGH (≥0.75) | MEDIUM (0.45~0.75) | LOW (<0.45)
```

### 설명가능성
- 응답의 `matched_rules: ["R001 Timeout detection (+0.35) - evidence: ...", ...]` 로 **왜** 이 점수인지 그대로 노출.
- GPT 보강 시에도 **룰 결과는 baseline** — `gpt_analyzer.py`의 system prompt가 "Rule baseline is authoritative"로 고정.

### 검증 자산
- `backend/src/analysis/validation/test_cases.py` — 50개 시나리오 (silence/single rule/multi rule/edge)
- `backend/src/analysis/validation/distribution.py` — 신뢰도 분포 분석 + 미스매치 리포트

---

## 4. API 레퍼런스 (현재 동작 기준)

### `POST /logs`
```json
// Request — LogCreateDTO
{
  "source": "gateway",          // 영문/숫자/-/_ 만 허용
  "message": "Request timed out after 30s",
  "level": "ERROR",             // DEBUG | INFO | WARN | ERROR
  "timestamp": "2026-05-08T15:01:00Z"  // 선택, 미제공 시 서버 UTC
}
// Response — LogResponseDTO
{ "id": "uuid", "source": "...", "message": "...", "level": "...",
  "timestamp": "...", "received_at": "...", "host": null }
```

### `GET /logs`
인메모리 전체 로그 배열 반환. 페이지네이션 없음.

### `POST /analysis`
```json
// Request — AnalysisRequestDTO
{
  "log_ids": ["uuid1", "uuid2"],
  "strategy": "rule"            // rule | gpt | ai | hybrid (현재 rule/gpt만 동작)
}
// Response — AnalysisResultDTO
{
  "summary": "...",
  "severity": "HIGH",
  "confidence": 0.82,
  "suspected_causes": ["..."],
  "recommended_actions": ["..."],
  "matched_rules": ["R001 Timeout detection (+0.35) - evidence: ..."],
  "strategy_used": "rule",
  "received_at": "..."
}
```
- 존재하지 않는 `log_ids` 가 섞이면 **400** 반환.
- `strategy=gpt` 인데 `OPENAI_API_KEY` 미설정 시 → 룰 결과만 반환 (조용히 fallback).

### `GET /health`
⚠️ 라우터는 등록되어 있으나 핸들러 본문이 비어 있음.

---

## 5. 데이터 모델

### Pydantic DTO (`backend/src/schemas/`)
- `LogLevel`: `DEBUG | INFO | WARN | ERROR`
- `SeverityLevel`: `LOW | MEDIUM | HIGH | CRITICAL` (CRITICAL은 enum만 존재, 매핑 미사용)
- `AnalysisStrategy`: `RULE | AI | HYBRID | GPT` (현재 RULE/GPT만 분기)

### ORM (`backend/src/model/`) — 미연결 상태
- `Log`: id / source / message / level / timestamp / received_at / host
- `AnalysisResult`: causes·actions를 JSONB, severity·strategy enum

### Frontend types
- `Severity = "LOW" | "MEDIUM" | "HIGH"` ← **CRITICAL 누락** (백엔드와 불일치)
- `Strategy = "rule" | "gpt"` ← AI/HYBRID 미반영

---

## 6. 프론트엔드 동작 요약

- **page.tsx**: `useEffect` 안에서 `setInterval(fetchLogs, 3000)` — 폴링 방식.
- **AgentStatus**: 마지막 `received_at`이 30초 이내면 connected — *진짜 헬스체크 아님, 휴리스틱*.
- **StrategySelect**: 두 버튼 (Rule = neutral, GPT = indigo).
- **AnalysisResult**: severity 색은 컴포넌트 내부에서 직접 하드코딩 (`styles/severity.ts`는 빈 파일).
- **LogForm**: PoC 용 수동 입력. 운영에서는 에이전트만 사용.
- 에러 처리: `alert("Analysis failed")` 수준 — 상세 메시지 없음.

---

## 7. 에이전트 동작 요약

```bash
python netscope-agent.py --path /var/log/app.log --source gateway
```
- `--path` 필수, `--source` 옵션 (기본 = 파일 이름).
- 파일 끝부터 시작 (재시작 시 마지막 위치 기억 안 함 — 매번 EOF부터).
- 1초 슬립 루프, EOF 시 대기.
- 라인 정규화: BOM(`﻿`), `\r`, `\x00` 제거 → Windows/PowerShell 환경에서도 안전.
- level 추론: 본문에서 `ERROR|WARN|INFO` 키워드 첫 매치.
- 1차 필터 통과 조건 (OR):
  - level이 ERROR 또는 WARN
  - 본문에 `TIMEOUT` / `TIMED OUT`
  - HTTP 5xx 코드 (`50x`)
- POST 실패 시 stdout에 에러 출력 후 다음 라인으로 계속 진행 (루프 유지).

---

## 8. 실행 방법 (현재 코드 기준)

### Backend
```bash
cd backend
pip install -r requirements.txt
# 옵션: GPT 사용 시
$env:OPENAI_API_KEY = "sk-..."
uvicorn src.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
# 옵션: API 위치 변경 시
$env:NEXT_PUBLIC_API_BASE_URL = "http://localhost:8000"
npm run dev   # http://localhost:3000
```

### Agent
```bash
cd backend/netscope-agent
python netscope-agent.py --path ../../test-log/shell.log --source demo
```

---

## 9. 알려진 갭 / 주의 사항

| 영역 | 현재 상태 | 영향 |
| --- | --- | --- |
| DB 영속화 | ORM·repository 정의됨, 라우터 미연결 | **재시작 시 모든 로그/결과 유실** |
| 인증·테넌시 | `core/security.py` 비어 있음, CORS=`*` | 누구나 `/logs` POST 가능 |
| 헬스 엔드포인트 | `health.py` 본문 없음 | 외부 모니터링 불가 |
| GPT 모델명 | `gpt-4.1-mini` 표기 | 의도가 `gpt-4o-mini`라면 수정 필요 |
| 분석 결과 저장 | `save_analysis_result` 미호출 | 분석 이력/감사 로그 없음 |
| 인메모리 싱글톤 | 단일 워커 가정 | 멀티 워커/멀티 인스턴스에서 로그 분산 |
| 7일 윈도우 | README에만 언급 | 리텐션 정책 코드 없음 |
| 로그 파서 | `log/parser.py` 비어 있음 | 구조화 포맷(JSON/syslog) 파싱 불가 |
| 프론트 Severity 타입 | CRITICAL 누락 | 향후 CRITICAL 매핑 추가 시 타입 에러 |
| Agent resume | EOF부터 시작, 위치 미저장 | 재시작 사이 라인 누락 가능 |
| 테스트 | `tests/test_health.py` 1개 | 회귀 방어 부재 |

→ 우선순위 + 기획 명세는 [`docs/PM_ENHANCEMENT_PLAN.md`](./docs/PM_ENHANCEMENT_PLAN.md)

---

## 10. 작업 시 컨벤션 / 에이전트 가이드

- **언어**: 코드 주석/식별자 영어, 도메인 문서·기획서는 한국어 OK.
- **레이어 경계**: 라우터는 storage 직접 접근 금지 — 반드시 `LogService` 경유. 분석 엔진은 ORM/DB 모름.
- **룰 추가 시**:
  1. `rule_engine.py`의 `default_rules()`에 `Rule(id, score, predicate, evidence, causes, actions)` 추가
  2. `validation/test_cases.py`에 양성/음성 케이스 추가
  3. `validation/distribution.py` 실행해 분포 회귀 확인
- **DTO 변경 시**: `backend/src/schemas/` 와 `frontend/src/types/` **양쪽** 동기화 필수.
- **GPT enrichment 변경**: system prompt의 "Rule baseline is authoritative" 문구는 유지 — 그렇지 않으면 결과의 결정성·재현성이 깨짐.
- **에이전트**: stdlib + `requests` 만 사용 유지 (배포 친화). 의존성 추가 신중.

---

## 11. 다음 단계 트리아지 (요약)

P0 — DB 영속화, 인증/CORS 강화, health 엔드포인트, GPT 모델명 정정
P1 — **인시던트 보고서 대시보드 (Flagship UI)**, 룰 관리 API, 분석 이력, 멀티테넌시, Webhook 알림, **패턴 마이닝 백그라운드 수집 (룰 학습 L0)**
P2 — 7일 윈도우 리텐션, 구조화 파서, Redis 캐시, 에이전트 resume, PDF Export, **패턴 라벨링 UX + 분석 결과 통합 (룰 학습 L1·L2)**
P3 — 룰 A/B 테스트, 비용/토큰 트래킹, **패턴 자동 승격 + 피드백 가중치 (룰 학습 L3·L4)**, 양방향 Slack

> 룰 학습 정본: [`docs/RULE_LEARNING.md`](./docs/RULE_LEARNING.md) — 본 시스템의 차별점 ③.

상세는 `docs/PM_ENHANCEMENT_PLAN.md`.
