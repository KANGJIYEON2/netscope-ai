# API Reference

> **기준**: 현재 `main` 코드 (auth/DB/멀티테넌시 머지 이후, 2026-05-29).
> **Base URL**: 기본 `http://localhost:8000`. 프론트는 `NEXT_PUBLIC_API_BASE_URL` env로 오버라이드.
> **인증**: 보호 라우트는 httpOnly 쿠키 `access_token` 필요. tenant/project 경계는 서버에서 강제.

## 목차
- [공통](#공통)
- [라우트 트리](#라우트-트리)
- [Auth](#auth)
- [Projects](#projects)
- [Logs](#logs)
- [Analysis](#analysis)
- [Reports](#reports)
- [Ingest](#ingest)
- [Analysis Test](#analysis-test)
- [에러 모델](#에러-모델)
- [DTO 카탈로그](#dto-카탈로그)
- [향후 확장](#향후-확장)

---

## 공통

### 컨텐츠 타입
- 요청/응답 모두 `application/json; charset=utf-8`
- 시간 표기 ISO 8601 UTC (`2026-05-29T14:31:02Z`). 미제공 시 서버 UTC `now()`.

### 인증
- **보호 라우트**(`/projects/...`)는 쿠키 `access_token` 필수 — `Depends(get_current_context)`(`api/v1/dep.py`)가 JWT를 디코드해 `{user_id, tenant_id}` 주입.
- 쿠키는 `/auth/{login,register,refresh}` 응답의 `Set-Cookie`로 발급 (프론트가 토큰을 직접 보관하지 않음).
- CORS는 `settings.FRONTEND_ORIGIN` **단일 오리진** 화이트리스트 + `allow_credentials=True` (`main.py:17-23`). `*` 아님.

### 라우터 등록 (`backend/src/main.py`)
`logs · analysis · ingest · reports · projects · auth · test` 7개 라우터 마운트.
`/health` 는 **미등록** (`api/v1/health.py` 비어있음). `/projects/overview` 는 **존재하지 않음** (프론트만 호출 → 404).

---

## 라우트 트리

```
🔓 PUBLIC
├── POST   /auth/register          email/password → tenant 자동 생성 + 쿠키 set
├── POST   /auth/login             자격 확인 → 쿠키 set (refresh rotation 시작점)
├── POST   /auth/refresh           refresh 쿠키만으로 access 갱신 + rotation
└── POST   /auth/logout            현 refresh revoke + 쿠키 제거

🔓 SEMI-PUBLIC (헤더 기반 — 에이전트/외부)
├── POST   /ingest                 X-Tenant-ID, X-Project-ID 필수, raw 보관 X
└── POST   /analysis/test          DB 없이 룰만 실행 (개발/검증용)

🔐 PROTECTED (cookie:access_token 필요, tenant 자동 적용)
├── GET    /projects                       내 tenant 프로젝트 목록
├── POST   /projects                       { name } → 201 ProjectResponse
├── DELETE /projects/{project_id}          → 204
├── POST   /projects/{project_id}/logs                       → 201 LogResponseDTO
├── GET    /projects/{project_id}/logs                       최근 200건 (timestamp desc)
├── DELETE /projects/{project_id}/logs/{log_id}              → 204
├── POST   /projects/{project_id}/analysis                   { log_ids[], strategy } → 201
├── GET    /projects/{project_id}/reports                    목록 (start_date/end_date/limit)
├── GET    /projects/{project_id}/reports/weekly             최근 7일 GPT 요약 + 리스크 (캐시)
├── GET    /projects/{project_id}/reports/trend/confidence   일자별 평균 confidence
└── GET    /projects/{project_id}/reports/{analysis_id}      단건

🚧 MISSING (코드 없음)
├── GET    /health                 (api/v1/health.py 비어있음)
└── GET    /projects/overview      (프론트 lib/api/overview.ts 만 호출)
```

---

## Auth

`prefix=/auth`. 본문은 `{email, password}` (둘 다 필수, email은 `EmailStr`). 응답은 모두 `{ "ok": true }` + `Set-Cookie`.

| 메서드 | 경로 | 동작 | 에러 |
| --- | --- | --- | --- |
| POST | `/auth/register` | tenant + user 생성 후 access/refresh 쿠키 발급 | `409 Email already exists` |
| POST | `/auth/login` | 자격 확인 후 새 refresh 발급 | `401 Invalid email or password` |
| POST | `/auth/refresh` | refresh 쿠키 → 새 access+refresh (rotation) | `401 NO_REFRESH_TOKEN` · `401 <reuse/invalid 사유>` (쿠키 삭제) |
| POST | `/auth/logout` | 현 refresh revoke + 쿠키 삭제 | (항상 200) |

- Access 쿠키: `access_token` · httpOnly · path=`/` · max-age=`ACCESS_TOKEN_EXPIRE_MINUTES*60`.
- Refresh 쿠키: `refresh_token` · httpOnly · **path=`/auth`** · max-age=`REFRESH_TOKEN_EXPIRE_DAYS*24h`.
- `secure`/`samesite` 는 `COOKIE_SECURE`/`COOKIE_SAMESITE` 설정값 (기본 false/lax). 운영 시 변경 필요.
- **Reuse 탐지**: revoked 된 refresh 재사용 또는 token_hash 불일치 시 해당 user 전체 세션 강제 revoke.

```http
POST /auth/login
Content-Type: application/json

{ "email": "alice@demo.io", "password": "Demo1234!" }
```

---

## Projects

`prefix=/projects`. 모두 보호 라우트, `ctx["tenant_id"]` 로 자동 필터.

### `GET /projects` → `200`
```json
[ { "id": "uuid", "name": "gateway-prod", "created_at": "2026-05-22T09:00:00Z" } ]
```

### `POST /projects` → `201`
```json
// Request
{ "name": "gateway-prod" }
// Response — ProjectResponse
{ "id": "uuid", "name": "gateway-prod", "created_at": "2026-05-29T..." }
```

### `DELETE /projects/{project_id}` → `204`
- 내 tenant 소유가 아니거나 미존재 → `404 Project not found`.

---

## Logs

`prefix=/projects/{project_id}/logs`. 보호 라우트. tenant+project 경계 강제.

### `POST /projects/{project_id}/logs` → `201`
수동 단건 입력 (`source_type="manual"`).

```json
// Request — LogCreateDTO
{
  "source": "gateway",
  "message": "Request timed out after 30s",
  "level": "ERROR",
  "timestamp": "2026-05-29T14:31:02Z"
}
// Response — LogResponseDTO
{
  "id": "uuid", "source": "gateway", "message": "Request timed out after 30s",
  "level": "ERROR", "timestamp": "2026-05-29T14:31:02Z",
  "received_at": "2026-05-29T14:31:02.184Z", "host": null
}
```

필드 검증 (`schemas/log.py`):

| 필드 | 타입 | 필수 | 제약 |
| --- | --- | :---: | --- |
| `source` | string | ✅ | 길이 **2~50**, 정규식 `^[a-zA-Z0-9_\-]+$` |
| `message` | string | ✅ | `min_length=1` (상한 없음) |
| `level` | enum | — | `DEBUG \| INFO \| WARN \| ERROR`, **기본 `INFO`** |
| `timestamp` | ISO8601 | — | 미제공 시 서버 UTC `now()` |

### `GET /projects/{project_id}/logs` → `200`
- 최근 **200건**만, `timestamp DESC`. (페이지네이션 없음)

### `DELETE /projects/{project_id}/logs/{log_id}` → `204`
- 미존재/경계 밖 → `404 Log not found`.

---

## Analysis

`prefix=/projects/{project_id}/analysis`. 보호 라우트.

### `POST /projects/{project_id}/analysis` → `201`
선택한 로그들을 룰 엔진(+옵션 GPT)으로 분석하고 **DB에 저장**한 뒤 반환. 조건 충족 시 주간 리포트도 자동 트리거.

```json
// Request — AnalysisRequestDTO
{ "log_ids": ["uuid-1", "uuid-2"], "strategy": "rule" }   // rule | gpt (ai/hybrid 미구현)

// Response — AnalysisResultDTO (저장된 결과)
{
  "summary": "룰 기반 분석 결과, 다음과 같은 이상 징후가 감지되었습니다: Timeout 발생, 5xx 응답 감지.",
  "severity": "HIGH",
  "confidence": 0.85,
  "suspected_causes": ["Upstream 응답 지연", "프록시/게이트웨이 오류"],
  "recommended_actions": ["timeout 설정값 확인", "Upstream 헬스 점검"],
  "matched_rules": [
    "R001 Timeout 발생 (+0.35) - 로그 메시지에 timeout / timed out / ETIMEDOUT 키워드가 포함됨",
    "R004 5xx 응답 감지 (+0.25) - 로그 메시지에 5xx(502/503/504) 상태 코드 패턴이 포함됨"
  ],
  "strategy_used": "rule",
  "received_at": "2026-05-29T10:11:12Z"
}
```

> `matched_rules` 문자열 포맷(`rule_engine.py`): `f"{rule_id} {title} (+{score:.2f}) - {evidence}"` — **제목/근거는 한국어**.

### 동작 (`analysis/engine.py`)
1. `log_ids` 가 모두 내 tenant+project 에 속하는지 검증 → 불일치 시 **400** (`"Some log_ids are invalid or not accessible"`).
2. RuleEngine 집계 → base + evidence + interaction → confidence.
3. `strategy=="gpt"` 이고 `OPENAI_API_KEY` 존재 시 GPTAnalyzer 보강 (룰이 baseline, 뒤집지 못함).
4. severity 매핑: `≥0.75 HIGH · ≥0.45 MEDIUM · <0.45 LOW`.
5. causes/actions 비면 fallback 문구 보장.
6. `AnalysisResult` 저장 (tenant+project 강제). 최근 7일 ≥5건 & 주간 리포트 미존재 → 자동 생성.

| 환경 / 입력 | 결과 |
| --- | --- |
| `strategy=rule` | 룰 결과만 |
| `strategy=gpt` + `OPENAI_API_KEY` 있음 | 룰 + GPT 병합 |
| `strategy=gpt` + key 없음 | 룰만, `strategy_used="rule"` 로 조용히 폴백 ⚠️ |
| `strategy=ai\|hybrid` | 미구현 (사실상 rule 폴백) |

---

## Reports

`prefix=/projects/{project_id}/reports`. 보호 라우트.

### `GET /projects/{project_id}/reports` → `200`
`AnalysisResultDTO[]`. Query: `start_date`, `end_date` (YYYY-MM-DD), `limit` (1~100, 기본 20).

### `GET /projects/{project_id}/reports/weekly` → `200`
최근 7일 집계. 같은 기간 리포트가 이미 있으면 캐시 반환, 없으면 GPT 요약 + 리스크 예측 후 저장.
```json
{
  "period": "last_7_days",
  "from": "2026-05-22", "to": "2026-05-29",
  "report_count": 17,
  "summary": "지난 주는 게이트웨이 5xx 가 우세했고, ...",
  "risk_outlook": { "level": "보통", "reason": "..." }
}
```
- 7일 내 분석 결과 0건이면 `report_count: 0` + `level: "낮음"` 기본 응답.

### `GET /projects/{project_id}/reports/trend/confidence` → `200`
```json
{
  "metric": "confidence_trend",
  "points": [ { "date": "2026-05-28", "avg_confidence": 0.612, "report_count": 4 } ]
}
```

### `GET /projects/{project_id}/reports/{analysis_id}` → `200`
단건 `AnalysisResultDTO`. 미존재 → `404 Report not found`.

> ⚠️ 라우트 정의 순서상 `/weekly` 와 `/trend/confidence` 가 `/{analysis_id}` 보다 먼저 선언되어 경로 충돌 없음.

---

## Ingest

`POST /ingest` — 에이전트/외부 수집용 hot path. **raw 로그 비저장**, 룰 결과만 `analysis_results` 로 영속화.

```http
POST /ingest
X-Tenant-ID: <uuid>        (필수)
X-Project-ID: <uuid>       (필수)
X-Agent-ID: agent-001      (선택)
Content-Type: application/json

{ "logs": ["[ERROR] timeout", "[ERROR] 502 Bad Gateway"] }
```
응답: `{ "status": "ok" }`. 헤더 누락 시 `422`.

---

## Analysis Test

`POST /analysis/test` — DB·인증 없이 룰만 돌리는 검증용.
```json
// Request — TestAnalysisRequestDTO
{ "messages": ["[ERROR] Request timed out", "502 Bad Gateway"], "strategy": "rule" }
// Response — AnalysisResultDTO (저장 안 함)
```

---

## 에러 모델

FastAPI 기본: `{ "detail": "string | array" }`.

| 상태 | 케이스 |
| :---: | --- |
| 400 | `analysis.log_ids` 일부가 tenant/project 경계 밖 (`"Some log_ids are invalid or not accessible"`) |
| 401 | `NO_REFRESH_TOKEN`, refresh 재사용/위조 탐지, access 토큰 만료/무효 |
| 404 | project / log / report 단건 미존재 |
| 409 | `Email already exists` |
| 422 | Pydantic 검증 실패 (잘못된 level, source 패턴 위반, 필수 헤더 누락 등) |

---

## DTO 카탈로그

### `LogCreateDTO` (`schemas/log.py`)
```python
source: str                 # min 2, max 50, ^[a-zA-Z0-9_\-]+$
message: str                # min_length=1
level: LogLevel = INFO      # 기본 INFO
timestamp: datetime | None  # 기본 now(UTC)
```

### `LogResponseDTO`
```python
id: str
source: str
message: str
level: LogLevel
timestamp: datetime
received_at: datetime
host: str | None
```

### `AnalysisRequestDTO`
```python
log_ids: list[str]                 # min_items=1
strategy: AnalysisStrategy = RULE  # rule (기본) | gpt  (ai/hybrid 정의만 존재)
```

### `AnalysisResultDTO`
```python
summary: str
severity: SeverityLevel            # LOW | MEDIUM | HIGH | (CRITICAL — enum만, 미사용)
confidence: float                  # 0..1
suspected_causes: list[str]        # min_items=1
recommended_actions: list[str]     # min_items=1
matched_rules: list[str]           # "R001 Timeout 발생 (+0.35) - <근거>"
strategy_used: str = "rule"
received_at: datetime
```

### Enum 정리 (`schemas/enums.py`)
| Enum | 값 | 비고 |
| --- | --- | --- |
| `LogLevel` | `DEBUG`, `INFO`, `WARN`, `ERROR` | FE 동일 ✅ |
| `SeverityLevel` | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` | CRITICAL 매핑 룰 없음 (엔진 미사용) |
| `AnalysisStrategy` | `rule`, `ai`, `hybrid`, `gpt` | 현재 rule/gpt만 분기. ai/hybrid 미구현 |

> **프론트 동기화 누락**: `frontend/src/types/analysis.ts` 의 `Severity` 는 `"LOW" | "MEDIUM" | "HIGH"` 만, Strategy 는 `"rule" | "gpt"` 만 정의. CRITICAL/ai/hybrid 도입 시 양쪽 동기화 필요.

---

## 향후 확장

> 아래는 **미구현** 제안 — 현재 코드에 없음.

### 분석 결과 응답 확장 (대시보드 동반)
```python
class ConfidenceBreakdown(BaseModel):
    base: float; evidence_bonus: float; interaction_bonus: float; gpt_bonus: float; final: float

class MatchedRuleDetail(BaseModel):
    id: str            # "R001"
    name: str
    score: float
    evidence: list[str]
    matched_log_ids: list[str]
```
- 기존 `matched_rules: list[str]` 는 호환 유지 위해 남겨둠.

### 룰 관리 API (P1)
```http
GET /rules · POST /rules · PATCH /rules/{id} · DELETE /rules/{id} · POST /rules/dryrun
```

### Webhook (P1)
```http
POST /tenants/me/webhooks   { "url": "https://hooks.slack.com/...", "min_severity": "HIGH" }
```

### 운영 필수 (P0)
- `GET /health` (liveness/readiness) — 현재 미구현.
- `GET /projects/overview` — 프론트가 호출하나 백엔드 없음.

---

## 변경 이력

| 버전 | 변경 |
| --- | --- |
| 0.1 | MVP (in-memory, no-auth) 기준 |
| **0.2 (현재)** | auth/DB/멀티테넌시/projects/reports/ingest 반영 — 전 라우트 `/projects/{id}/...` 로 이전 |
| 1.0 (예정) | 응답 확장 + 룰 관리 API + /health |
