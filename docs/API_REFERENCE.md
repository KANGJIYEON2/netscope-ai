# API Reference

> **기준**: `main` 브랜치 (`c401ae2`) 코드. 미구현/미연결 항목은 ⚠️ 표시.
> **Base URL**: 기본 `http://localhost:8000`. 프론트는 `NEXT_PUBLIC_API_BASE_URL` env로 오버라이드.

## 목차
- [공통](#공통)
- [POST /logs](#post-logs)
- [GET /logs](#get-logs)
- [POST /analysis](#post-analysis)
- [GET /health](#get-health)
- [에러 모델](#에러-모델)
- [DTO 카탈로그](#dto-카탈로그)
- [향후 확장 (P0~P1)](#향후-확장-p0p1)

---

## 공통

### 컨텐츠 타입
- 요청/응답 모두 `application/json; charset=utf-8`
- 시간 표기 ISO 8601 UTC (`2026-05-08T14:31:02Z`). 미제공 시 서버 UTC `now()`.

### 인증 (현재)
- ❌ **없음**. CORS 도 `*`. P0-2/P0-3에서 `X-API-Key`, `X-Tenant-ID` 도입 예정.

### 라우터 등록
- `backend/src/main.py` 가 `/logs`, `/analysis` 두 라우터를 마운트. `/health` 는 등록만 되어 있고 핸들러 본문 없음.

---

## POST /logs

단일 로그를 인메모리 스토리지에 저장하고 UUID를 발급한다.

### 요청
```http
POST /logs
Content-Type: application/json
```
```json
{
  "source": "gateway",
  "message": "Request timed out after 30s",
  "level": "ERROR",
  "timestamp": "2026-05-08T14:31:02Z"
}
```

### 필드 검증 (`schemas/log.py`)
| 필드 | 타입 | 필수 | 제약 |
| --- | --- | :---: | --- |
| `source` | string | ✅ | 영문/숫자/`-`/`_` 만 허용. 길이 1~64. 정규식: `^[A-Za-z0-9_-]+$` |
| `message` | string | ✅ | 1~4096자 |
| `level` | enum | ✅ | `DEBUG | INFO | WARN | ERROR` |
| `timestamp` | ISO8601 | — | 미제공 시 서버 UTC |

### 응답 — `200 OK`
```json
{
  "id": "8f3a1b2c-9c4d-4e3f-9a1b-2c3d4e5f6a7b",
  "source": "gateway",
  "message": "Request timed out after 30s",
  "level": "ERROR",
  "timestamp": "2026-05-08T14:31:02Z",
  "received_at": "2026-05-08T14:31:02.184Z",
  "host": null
}
```

> `host` 는 에이전트가 보낼 때만 채움. 직접 호출 시 항상 `null`.

### 에러
- `422` — Pydantic 검증 실패 (잘못된 level, 비어있는 message 등)

### 사용 예 — netscope-agent
```python
requests.post(f"{API_URL}/logs", json={
    "source": "gateway",
    "message": line,
    "level": detect_level(line),
    "timestamp": datetime.utcnow().isoformat() + "Z",
})
```

---

## GET /logs

저장된 모든 로그를 반환한다 (페이지네이션 ❌).

### 요청
```http
GET /logs
```

### 응답 — `200 OK`
```json
[
  { "id": "...", "source": "gateway", "message": "...", "level": "ERROR",
    "timestamp": "2026-05-08T14:31:02Z", "received_at": "...", "host": null },
  ...
]
```

### 주의
- 인메모리 — 백엔드 재시작 시 빈 배열.
- 프론트는 3초 폴링 → 로그가 1만 건 넘으면 응답 폭증. P0-1 DB 영속화 + P1 페이지네이션 함께 필요.

---

## POST /analysis

선택한 로그 ID들에 대해 룰 엔진(+옵션 GPT)을 실행하고 분석 결과를 반환한다.

### 요청
```http
POST /analysis
Content-Type: application/json
```
```json
{
  "log_ids": ["8f3a1b2c-...", "...", "..."],
  "strategy": "rule"
}
```

### 필드
| 필드 | 타입 | 필수 | 비고 |
| --- | --- | :---: | --- |
| `log_ids` | string[] | ✅ | 최소 1개. 모두 존재해야 함 |
| `strategy` | enum | — | `rule (기본) | gpt | ai | hybrid` — 현재 `rule`/`gpt` 만 분기 동작. 나머지는 `rule`로 폴백 |

### 응답 — `200 OK`
```json
{
  "summary": "Timeout cascade detected across gateway and payment-gw...",
  "severity": "HIGH",
  "confidence": 0.82,
  "suspected_causes": [
    "upstream 지연으로 인한 timeout",
    "proxy/게이트웨이 오류 (5xx)",
    "인증 토큰 회전 누락 (gpt 보강)"
  ],
  "recommended_actions": [
    "upstream 헬스 체크",
    "timeout 설정 재검토",
    "KMS 회전 이력 확인 (gpt 보강)"
  ],
  "matched_rules": [
    "R001 Timeout detection (+0.35) - evidence: 'Request timed out after 30s' x4",
    "R004 5xx upstream error (+0.25) - evidence: 'Upstream returned 502' x2",
    "R005 ERROR-level (+0.20) - evidence: 12 ERROR logs",
    "R006 Repeated source (+0.20) - gateway x8 occurrences"
  ],
  "strategy_used": "gpt",
  "received_at": "2026-05-08T14:31:08Z"
}
```

### 동작 (`analysis/engine.py`)
1. 모든 `log_ids` 가 스토리지에 있는지 검증 → 누락 시 **400**
2. `RuleEngine.aggregate(logs)` → base_score, evidence, matched_rules
3. `strategy=="gpt"` 이고 `OPENAI_API_KEY` 환경변수 존재 시 → `GPTAnalyzer.enrich(logs, rule_summary)` 호출, +0.2 max bonus
4. confidence = `min(base + evidence_bonus + interaction_bonus + gpt_bonus, 1.0)`
5. severity 매핑:
   - `≥ 0.75` → `HIGH`
   - `0.45 ≤ x < 0.75` → `MEDIUM`
   - `< 0.45` → `LOW`
6. causes/actions 가 빈 배열이 되지 않도록 폴백 보장

### 에러
- `400` — `log_ids` 중 존재하지 않는 항목 있음
  ```json
  { "detail": "log_ids not found: ['abc', 'def']" }
  ```
- `422` — 빈 `log_ids` 배열, 잘못된 strategy 값
- `500` — 분석 엔진 내부 예외 (현재 catch-all 없음 → P0 작업에서 추가)

### 동작 변형
| 환경 / 입력 | 결과 |
| --- | --- |
| `strategy=rule` | 룰 결과만, GPT 호출 없음 |
| `strategy=gpt` + `OPENAI_API_KEY` 있음 | 룰 + GPT 병합 |
| `strategy=gpt` + key 없음 | 룰 결과만, `strategy_used="rule"` 로 응답 ⚠️ (조용한 폴백 — 사용자에게 안 알려짐, P0에서 명시화 필요) |
| `strategy=hybrid|ai` | 현재 `rule`로 폴백 |

---

## GET /health

⚠️ **현재 구현 안 됨** (`api/v1/health.py` 본문 없음).

### P0 목표 응답
```json
{
  "status": "ok",
  "checks": {
    "database": "ok",
    "openai": "ok|degraded|unavailable",
    "version": "0.2.0",
    "uptime_sec": 3641
  }
}
```
- k8s liveness: `status==ok` 시 200, 그 외 503.
- readiness: DB 연결 확인 추가.

---

## 에러 모델

FastAPI 기본:
```json
{ "detail": "string | object | array" }
```

검증 실패 (422) 예시:
```json
{
  "detail": [
    {
      "loc": ["body", "level"],
      "msg": "value is not a valid enumeration member",
      "type": "type_error.enum"
    }
  ]
}
```

> P0에서 통일된 에러 envelope 검토 권장:
> ```json
> { "error": { "code": "LOGS_NOT_FOUND", "message": "...", "details": {...} } }
> ```

---

## DTO 카탈로그

### `LogCreateDTO`
```python
source: str                 # ^[A-Za-z0-9_-]+$
message: str                # 1..4096
level: LogLevel             # DEBUG | INFO | WARN | ERROR
timestamp: datetime | None  # 옵션
```

### `LogResponseDTO`
```python
id: UUID
source: str
message: str
level: LogLevel
timestamp: datetime
received_at: datetime
host: str | None
```

### `AnalysisRequestDTO`
```python
log_ids: list[UUID]                # min_items=1
strategy: AnalysisStrategy = RULE  # RULE | AI | HYBRID | GPT
```

### `AnalysisResultDTO` (현재)
```python
summary: str
severity: SeverityLevel            # LOW | MEDIUM | HIGH | (CRITICAL — enum만, 미사용)
confidence: float                  # 0..1
suspected_causes: list[str]
recommended_actions: list[str]
matched_rules: list[str]           # "R001 Timeout (+0.35) - evidence..."
strategy_used: AnalysisStrategy
received_at: datetime
```

### Enum 정리
| Enum | 값 | 비고 |
| --- | --- | --- |
| `LogLevel` | `DEBUG`, `INFO`, `WARN`, `ERROR` | — |
| `SeverityLevel` | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` | CRITICAL 매핑 룰 없음 (P2-2 예정) |
| `AnalysisStrategy` | `RULE`, `AI`, `HYBRID`, `GPT` | 현재 RULE/GPT만 분기. 나머지는 reserved |

> **프론트 동기화 누락**: `frontend/src/types/analysis.ts`의 `Severity` 가 `"LOW" | "MEDIUM" | "HIGH"` 만 정의 → CRITICAL 도입 시 타입 에러. P2-2와 함께 갱신.

---

## 향후 확장 (P0~P1)

### P0 — 인증 헤더 도입
```http
POST /analysis
X-API-Key: nks_live_xxxxxxxxxxxx
X-Tenant-ID: 7f3a-...
```
- 미제공/무효 → `401 { "error": { "code": "AUTH_REQUIRED" } }`
- 키 ↔ 테넌트 매핑은 DB에서 검증.

### P0 — 분석 결과 ID 발급 + 조회
```http
GET /analysis/{id}        # 단건 조회
GET /analysis             # 최근 N건 (테넌트 스코프)
```
응답에 `id`, `tenant_id`, `created_by` 추가.

### P1-0 (대시보드 동반) — 응답 확장
```python
class ConfidenceBreakdown(BaseModel):
    base: float
    evidence_bonus: float
    interaction_bonus: float
    gpt_bonus: float
    final: float

class MatchedRuleDetail(BaseModel):
    id: str               # "R001"
    name: str             # "Timeout detection"
    score: float
    evidence: list[str]
    matched_log_ids: list[UUID]   # 어떤 로그가 이 룰에 매칭됐는가

class TimeWindow(BaseModel):
    start: datetime
    end: datetime
    duration_sec: int

class SourceSummary(BaseModel):
    source: str
    log_count: int
    error_count: int

class AnalysisResultDTO(...):  # 기존 필드 +
    breakdown: ConfidenceBreakdown
    matched_rules_detail: list[MatchedRuleDetail]
    window: TimeWindow
    sources: list[SourceSummary]
```
- `matched_rules: list[str]` 는 **호환 유지** 위해 남겨둠.

### P1 — 룰 관리
```http
GET    /rules              # 활성 룰 목록
POST   /rules              # 사용자 정의 룰 추가 (DSL JSON)
PATCH  /rules/{id}         # 활성/비활성 토글, 점수 조정
DELETE /rules/{id}
POST   /rules/dryrun       # 최근 24h 로그에 시뮬레이션 (활성화 전 검토)
```

### P1 — Webhook
```http
POST /tenants/me/webhooks
{ "url": "https://hooks.slack.com/...", "min_severity": "HIGH" }
```

---

## 변경 이력

| 버전 | 변경 |
| --- | --- |
| 0.1 (현재) | 본 문서 — MVP 기준 작성 |
| 0.2 (예정) | P0 완료 후 인증·DB·헬스 확정 시 |
| 1.0 | P1-0 응답 확장 + 룰 관리 API 포함 |
