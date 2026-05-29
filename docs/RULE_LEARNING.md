# Rule Learning — 사용자 로그로부터 패턴을 학습한다

> **개념 한 줄**: 사용자가 보낸 로그에서 *반복되는 모양(template)*을 자동 추출 → 사용자가 라벨링 → 충분히 자주 나오면 **룰 후보**로 승격 → 분석 시 "이건 P-AUTH-401 패턴, 과거 8회 봤음 (HIGH 평균)" 같이 출처를 함께 답한다.
> **위치**: 본 문서는 정본. PM 로드맵 항목으로는 P2~P3 단계에 신규 편입(아래 §10).

## 목차
- [1. 왜 이게 필요한가](#1-왜-이게-필요한가)
- [2. 두 개의 학습 레이어](#2-두-개의-학습-레이어)
- [3. 사용자 시나리오 (말로 풀기)](#3-사용자-시나리오-말로-풀기)
- [4. 패턴 마이닝 파이프라인](#4-패턴-마이닝-파이프라인)
- [5. 패턴 카탈로그 (Pattern Catalog)](#5-패턴-카탈로그-pattern-catalog)
- [6. 사용자 라벨링 UX](#6-사용자-라벨링-ux)
- [7. 패턴 → 룰 승격](#7-패턴--룰-승격)
- [8. 분석 시 추론 (Pattern Lookup)](#8-분석-시-추론-pattern-lookup)
- [9. 피드백 루프 (룰 가중치 학습)](#9-피드백-루프-룰-가중치-학습)
- [10. 단계적 도입 로드맵](#10-단계적-도입-로드맵)
- [11. 데이터 모델](#11-데이터-모델)
- [12. 콜드 스타트 / 경계 사례](#12-콜드-스타트--경계-사례)
- [13. 프라이버시 · 안전](#13-프라이버시--안전)
- [14. 평가 지표](#14-평가-지표)

---

## 1. 왜 이게 필요한가

현재 룰 엔진(`RULE_ENGINE.md`)은 **18개의 도메인 일반 룰(R001~R018)**만 제공한다. 한계:

- 사용자 환경 고유 로그 (예: `payment-gw 401 spike`, `inventory-svc kafka rebalance`)는 매칭 안 됨 → 결과가 항상 LOW.
- 도메인 룰은 사람이 직접 정의해야 함 → 진입 장벽.
- "이 로그 처음 보는 거야 / 자주 보는 거야"를 사용자가 알 수 없음.

**해결**: 사용자가 보낸 로그 자체에서 *반복되는 모양*을 학습하고, 그 모양을 사용자가 의미부여(라벨링)하면 룰 후보가 자동 생성된다. 즉 **"사용자 환경에 맞춰 함께 자라는 룰셋"**.

이 가치는 두 가지를 동시에 제공한다:
1. **콜드 스타트 완화** — 도입 첫 주에 환경 고유 패턴 자동 발견
2. **설명력 강화** — "이 메시지는 P-AUTH-401 패턴 (이전 14건, 평균 severity HIGH)" 처럼 *역사*를 답에 포함

---

## 2. 두 개의 학습 레이어

| 레이어 | 입력 | 출력 | 학습 방식 |
| --- | --- | --- | --- |
| **L1. 패턴 마이닝** | 들어오는 로그 메시지 | 템플릿(상수+변수 구조), 빈도, 시간/소스 분포 | 비지도 (Drain-style 트리) |
| **L2. 룰 가중치 튜닝** | 사용자 피드백 (confirm / dismiss / "잘못 매칭됐다") | 룰별 score 보정값, 상호작용 보너스 가중 | 지도 — logistic regression 또는 BTL 모델 |

> L1은 **모양**을 배우고, L2는 **중요도**를 배운다. 둘 다 합쳐야 룰 학습이 완성됨.
> 본 문서는 주로 L1을 다루며, L2는 §9에서 짧게.

---

## 3. 사용자 시나리오 (말로 풀기)

> **Day 1.** SRE가 에이전트를 깐다. 첫 분석 결과: confidence 0.20, severity LOW. "음… 룰이 별로 안 맞네."
>
> **Day 3.** 시스템이 백그라운드에서 패턴 마이닝을 돌린 결과를 카드로 알린다.
> > 🔎 *3일 동안 이 패턴을 47번 봤어요*
> > `payment-gw : "Auth token expired (***)" - 47회, 주로 03:00~04:00`
> > [라벨 붙이기] [무시]
>
> SRE가 [라벨 붙이기] → 이름 `auth-token-expiry`, cause: "토큰 만료", action: "KMS 회전 로그 확인" 입력. 점수 0.30 으로 시작.
>
> **Day 5.** 새 알람. 분석 결과:
> > severity **HIGH** (0.78)
> > matched_rules: R001 Timeout (+0.35), **C-AUTH (auth-token-expiry, +0.30)** 🆕 *learned*
> > "이 로그는 과거 14번 본 `auth-token-expiry` 패턴과 일치합니다 (이전 평균 severity: HIGH)."
>
> SRE: "오, 정확하네." → confirm 클릭 → L2가 C-AUTH 의 점수를 +0.02 증분 (L2의 작은 가중치 학습).

이 시나리오에서 사용자가 원래 입력했어야 할 것은 *cause/action 텍스트* 뿐. **DSL 룰 정의를 직접 작성하지 않아도 룰이 늘어나는** 게 포인트.

---

## 4. 패턴 마이닝 파이프라인

```
Raw Log Message
   │
   ▼
[ Tokenizer ]            ── 공백/구두점 토큰화, 기본 정규화 (lowercase 옵션)
   │
   ▼
[ Variable Masking ]     ── 숫자/UUID/IP/타임스탬프/경로 → <NUM> <UUID> <IP> <TS> <PATH>
   │                        (정규식 기반, 컴파일 1회)
   ▼
[ Drain Tree ]           ── prefix 트리로 비슷한 길이/접두 묶음 → 클러스터
   │                        (depth 4, similarity 0.4 기본)
   ▼
[ Template ]             ── 클러스터 대표 시퀀스 → "Auth token expired (<UUID>)"
   │
   ▼
[ Catalog Upsert ]       ── 패턴 ID 해시 (SHA-1 prefix 12자), 빈도 카운트, 최근 보임
```

### 4-1. 변수 마스킹 규칙 (초기)

| 패턴 | 마스크 |
| --- | --- |
| `\d+` (3자 이상) | `<NUM>` |
| UUID v4 | `<UUID>` |
| IPv4/IPv6 | `<IP>` |
| ISO8601 / 유닉스 타임 | `<TS>` |
| `/[\w/.-]+` 경로 | `<PATH>` |
| 따옴표 안 임의 문자열 | `<STR>` |
| Base64 길이 ≥ 16 | `<B64>` |

> 마스킹 강도가 너무 강하면 모든 로그가 같은 패턴으로 묶이고, 너무 약하면 패턴이 폭증. **초기는 보수적 마스킹** + 사용자가 "이 변수도 마스킹"을 추가할 수 있는 UX 제공.

### 4-2. Drain 알고리즘 요약
- prefix tree, depth 4 (조정 가능)
- 각 leaf = 클러스터, 각 클러스터 = 1개 템플릿
- 새 로그 → tree 따라 내려감 → 유사도(`#match / #total`) ≥ θ 이면 같은 클러스터, 아니면 새 클러스터 생성
- 시간 복잡도 O(L) per log (L = 토큰 수) — 실시간 처리 가능

### 4-3. 라이브러리 후보
| 후보 | 장단점 |
| --- | --- |
| **drain3** (IBM) | 검증된 구현, 영속화 지원, Apache 2.0. 추천 |
| Custom 구현 | 의존성 0이지만 회귀 위험. 우선 drain3 wrap |
| 임베딩 클러스터링 (sentence-transformer + HDBSCAN) | 의미적 유사도 잡지만 비용·지연 큼. 후순위 (P3) |

> **결정**: **drain3 채택**. P2 단계에서 임베딩 보강 검토.

---

## 5. 패턴 카탈로그 (Pattern Catalog)

추출된 템플릿은 **테넌트별** 카탈로그에 적재.

### 필드
```
pattern_id       sha1 prefix (12자, 결정적)
template         "Auth token expired (<UUID>)"
sample           원본 로그 메시지 1개 (참고)
sources          {gateway: 12, payment-gw: 35} — 출처별 빈도
level_dist       {ERROR: 40, WARN: 7}
first_seen       2026-05-08T03:01:12Z
last_seen        2026-05-11T03:42:00Z
total_count      47
hourly_dist      [0,0,...,18,21,...,0]   — 24버킷 (UTC)
status           "candidate" | "labeled" | "promoted" | "dismissed"
label            null | "auth-token-expiry"     ← 사용자 라벨
notes            free text (사용자가 cause/action 입력)
score_seed       0.30  ← 룰 승격 시 초기 점수
```

### 인덱스
- 빈번 조회: `(tenant_id, status, total_count desc)` — "후보 중 빈도 높은 것"
- 분석 추론: `(tenant_id, pattern_id)` — 들어온 로그의 매칭 조회

### 갱신 정책
- 새 로그가 기존 클러스터에 들어가면 카운트만 증가, 시간/소스 분포 갱신.
- 기존에 없던 새 클러스터 → `status="candidate"` 로 신규 row.
- 카탈로그 크기 한도: 테넌트당 1만 패턴 (초과 시 *오래되고 빈도 낮은* 것부터 garbage collect).

---

## 6. 사용자 라벨링 UX

### 6-1. 알림 카드 (대시보드 사이드바 또는 분석 결과 하단)
```
┌──────────────────────────────────────────────────────────┐
│  🔎 New recurring pattern detected                       │
│                                                          │
│  payment-gw                                              │
│  "Auth token expired (<UUID>)"                           │
│                                                          │
│  Seen 47 times in 3 days · mostly 03:00~04:00 UTC        │
│  Level distribution: ERROR 85%, WARN 15%                 │
│                                                          │
│  [ Label this ▾ ]  [ Dismiss ]  [ Don't show again ]    │
└──────────────────────────────────────────────────────────┘
```

### 6-2. 라벨 입력 폼
```
Label name *      [ auth-token-expiry              ]
Display name *    [ 인증 토큰 만료                   ]
Suspected causes  [ 토큰 TTL 만료, KMS 회전 누락     ]
Recommended       [ KMS 회전 이력 확인              ]
Initial score     [ 0.30 ]    (slider 0.10 ~ 0.30)
```
- score 상한 0.30 — 사용자 정의/학습 룰이 시스템 룰의 신뢰를 흔들지 못하게 (안전 가드, P1-2와 동일 정책).

### 6-3. 패턴 관리 페이지 `/patterns`
- 테이블: 템플릿 / 빈도 / 마지막 본 시각 / 상태 / 라벨
- 필터: candidate / labeled / promoted / dismissed
- 원본 샘플 미리보기 (raw logs 5개)

---

## 7. 패턴 → 룰 승격

라벨이 붙은 패턴은 즉시 "후보 룰" 로 활성화되지만, 자동 매칭 신뢰는 단계적으로 부여한다.

### 7-1. 승격 단계
| 상태 | 매칭 결과의 확신 | UI 표기 |
| --- | --- | --- |
| `candidate` (라벨 없음) | 매칭은 되지만 점수 0 (참고용) | "참고 패턴" 회색 |
| `labeled` (사용자가 라벨함) | score_seed 적용, 룰처럼 동작 | "🆕 learned" 배지 |
| `promoted` (지속 발생 + confirm 누적) | 시스템 룰과 동등 가시화 | 일반 룰처럼 표시 |
| `dismissed` | 매칭 무시 | 숨김 |

### 7-2. 자동 promotion 트리거 (제안)
- `labeled` 상태에서 **confirm 5회 이상** 누적 + dismiss 비율 < 20% → 자동으로 `promoted`.
- 충돌 시 (사용자가 dismiss 다수 → confirm 추월) 다시 `labeled`로 강등.

### 7-3. 룰 ID 부여
- 사용자 정의: `C001+` (P1-2)
- 학습 패턴 승격: `L001+` (Learned)
- 시스템 룰: `R001~R099`

---

## 8. 분석 시 추론 (Pattern Lookup)

### 8-1. 분석 파이프라인 확장
```
Logs
  │
  ├─► RuleEngine.aggregate(logs)         ── R001~R099 (시스템)
  │
  ├─► PatternMatcher.match(logs)         ── 카탈로그에서 일치 패턴 찾기
  │     ├─ labeled / promoted 패턴만 점수 합산
  │     ├─ candidate 패턴은 응답 메타에 "참고" 로만 노출
  │     └─ matched_patterns: [{ id, label, count, history }]
  │
  ├─► (옵션) GPTAnalyzer.enrich(...)      ── 룰 + 패턴 결과 함께 컨텍스트로
  │
  ▼
AnalysisResult (확장)
```

### 8-2. 응답 확장
```python
class MatchedPattern(BaseModel):
    pattern_id: str
    label: str | None         # null → candidate
    template: str
    score: float              # labeled/promoted만 양수
    history: PatternHistory   # 과거 본 빈도, 평균 severity
    matched_log_ids: list[UUID]

class PatternHistory(BaseModel):
    total_count: int
    last_seen: datetime
    avg_severity: SeverityLevel
    confirm_count: int
    dismiss_count: int

class AnalysisResultDTO(...):
    ...
    matched_patterns: list[MatchedPattern]   # 신규
```

### 8-3. 사람용 요약 문장 (summary 보강)
> "**Auth token expired** 패턴이 12회 매칭되었습니다 (지난 30일간 47번 관찰, 평균 severity HIGH)."

이 문장은 결정적으로 만들 수 있어서 GPT 없이도 생성 가능 — *역사를 답에 포함하는 강력한 차별점*.

### 8-4. 대시보드 통합
- `MatchedRules` 패널과 같은 영역에 **Patterns 섹션** 추가.
- `🆕 learned` 배지로 학습된 패턴 강조.
- 클릭 → `/patterns/{id}` 상세 (history 차트 + 과거 인시던트 링크).

---

## 9. 피드백 루프 (룰 가중치 학습) — L2

### 9-1. 신호 수집
모든 분석 결과의 ack/dismiss/correct 액션을 기록.

```
event: { analysis_id, pattern_id|rule_id, action: "confirm"|"dismiss"|"wrong",
         user_id, severity_when_shown, true_severity?: optional, timestamp }
```

### 9-2. 단순한 모델 (시작점)
**Online increment**:
- confirm → score += +0.01 (clip ≤ score_max)
- dismiss → score -= 0.01 (clip ≥ score_min)
- wrong-match (사용자가 "이건 아닌 것 같다" 클릭) → score -= 0.02

> 첫 단계는 ML이 아닌 **단순 카운터**. 데이터가 모이면 logistic regression 으로 업그레이드.

### 9-3. 본격 모델 (P3)
- feature: pattern 빈도, 시간대 일치도, 동시 매칭된 룰셋, 사용자 ack 이력
- target: 사용자가 confirm 했는가?
- model: logistic regression (해석 가능 우선) → score 보정값 산출

### 9-4. 안전 가드
- 학습된 보정값 절대값 ≤ 0.10 (룰 자체 점수의 30% 이내)
- 시스템 룰(R001~)은 **L2의 자동 조정 대상에서 제외** — 항상 도메인이 검증한 점수만 사용.
- 학습 보정은 **테넌트별로 분리** (한 테넌트의 피드백이 다른 테넌트에 영향 안 줌).

---

## 10. 단계적 도입 로드맵

| Phase | 무엇 | PM 로드맵 매핑 |
| --- | --- | --- |
| **L0 (P0 직후)** | drain3 통합 + 카탈로그 적재 (사용자 알림 없이 백그라운드 수집만) | P1 후반 또는 **신규 P1-9** 로 편입 권장 |
| **L1 (P2)** | 패턴 알림 카드 + 라벨링 UX + `/patterns` 페이지 | **신규 P2-9** |
| **L2 (P2 후반)** | 분석 결과에 `matched_patterns` 노출 + 대시보드 통합 | P1-0 대시보드와 동기 |
| **L3 (P3)** | 패턴 → 룰 자동 승격 + 피드백 기반 점수 보정 (단순 카운터) | **신규 P3-7** |
| **L4 (P3 후반)** | logistic regression 기반 가중치 모델 | P3-1 (기존 자체 학습 항목)에 합쳐서 진행 |
| **L5 (장기)** | 임베딩 기반 의미 유사도 (의미는 같지만 표현이 다른 로그 묶기) | P3+ |

> **본 항목은 PM_ENHANCEMENT_PLAN.md 에 신규 P1-9 / P2-9 / P3-7 로 추가됨**. 본 문서가 정본이므로 그쪽에선 본 문서로 링크.

---

## 11. 데이터 모델 (DB 추가 테이블)

```sql
CREATE TABLE patterns (
  id              TEXT PRIMARY KEY,         -- sha1 prefix
  tenant_id       UUID NOT NULL,
  template        TEXT NOT NULL,
  sample          TEXT NOT NULL,
  total_count     INTEGER NOT NULL DEFAULT 0,
  first_seen      TIMESTAMPTZ NOT NULL,
  last_seen       TIMESTAMPTZ NOT NULL,
  sources         JSONB NOT NULL DEFAULT '{}'::jsonb,
  level_dist      JSONB NOT NULL DEFAULT '{}'::jsonb,
  hourly_dist     INTEGER[] NOT NULL DEFAULT array_fill(0, ARRAY[24]),
  status          TEXT NOT NULL DEFAULT 'candidate',
  label           TEXT,
  display_name    TEXT,
  causes          TEXT[] DEFAULT '{}',
  actions         TEXT[] DEFAULT '{}',
  score_seed      NUMERIC(3,2) DEFAULT 0.20,
  score_adjust    NUMERIC(3,2) DEFAULT 0.00,  -- L2 누적 보정
  confirm_count   INTEGER DEFAULT 0,
  dismiss_count   INTEGER DEFAULT 0,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX patterns_tenant_status_count_idx
  ON patterns (tenant_id, status, total_count DESC);

CREATE TABLE pattern_feedback (
  id              BIGSERIAL PRIMARY KEY,
  tenant_id       UUID NOT NULL,
  pattern_id      TEXT NOT NULL REFERENCES patterns(id),
  analysis_id     UUID,
  action          TEXT NOT NULL,             -- confirm | dismiss | wrong
  user_id         UUID,
  severity_shown  TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

> 마이그레이션은 P0-1의 Alembic 셋업과 함께 일관되게.

---

## 12. 콜드 스타트 / 경계 사례

| 상황 | 처리 |
| --- | --- |
| 첫 도입 (카탈로그 비어 있음) | 시스템 룰만 동작, 백그라운드에서 7일 동안 패턴 수집 후 카드 알림 시작 |
| 모든 로그가 다 다름 (변수 마스킹 부족) | "마스킹 추가" 추천 카드 — 자주 등장하는 후보 토큰을 보여주고 사용자가 마스크 룰 추가 |
| 사용자가 라벨을 안 붙임 | candidate 상태 유지, 점수 0 → 답에 "참고 패턴 5개" 만 노출 (워크플로우 강제 X) |
| 동일 메시지가 너무 많아 카탈로그 폭증 | 변수 마스킹 강도를 자동 상향 (top-K 토큰 → 자동 마스크 후보로 제안) |
| 패턴 충돌 (두 라벨이 같은 메시지를 다르게 분류) | 가장 최근 라벨이 우선, 충돌은 패턴 상세 페이지에서 표시 |
| 사용자가 "이 라벨 잘못 붙였어" 수정 | 새 라벨로 갱신, 이전 라벨의 history는 별도 보존 |

---

## 13. 프라이버시 · 안전

| 위험 | 가드 |
| --- | --- |
| 로그에 PII/시크릿 포함 | 마스킹 룰에 **이메일/JWT/API key** 정규식 기본 포함, sample 저장 시 추가 1차 redact |
| 테넌트 간 데이터 누수 | 모든 쿼리에 `tenant_id` 강제, FK·index도 항상 prefix |
| LLM 컨텍스트로 패턴/샘플 전송 | GPT 호출 시에는 **template만** 전송 (sample 원문 금지). 옵션 토글로 sample 포함 허용 |
| 학습 보정의 폭주 | score_adjust 절대값 ≤ 0.10, daily delta ≤ ±0.05 |
| 악의적 사용자가 score 조작 | 같은 사용자 ack 가중치 감소 (sigmoid), 단일 사용자 confirm 폭주 시 보너스 캡 |
| 카탈로그 메모리 폭증 | tenant당 ≤ 10K 패턴 + LRU 기반 GC + 빈도 임계 미만 30일 후 archive |

---

## 14. 평가 지표

### 제품
- **라벨링 전환율**: candidate → labeled 비율 (도구가 충분히 똑똑한지)
- **자동 발견 가치**: 라벨링된 패턴이 분석 결과 HIGH 매칭에 기여한 비율
- **재발견 시간(MTTI)**: 같은 인시던트가 재발했을 때 인지 속도 (패턴 history 효과)
- **dismiss 비율**: 너무 높으면 마이닝 정밀도 부족

### 모델
- **클러스터 순도(homogeneity)**: 같은 클러스터의 로그들이 의미상으로 같은가 (수동 샘플링)
- **template 안정성**: 시간이 지나도 같은 패턴 ID 유지율
- **추론 지연**: 1로그당 패턴 매칭 < 1ms (실시간 분석 보장)

### 운영
- **카탈로그 크기 / 테넌트** + 증가 추이
- **GC 주기**의 archive 비율
- **변수 마스킹 갱신**으로 인한 클러스터 합병 빈도

---

## 부록 — 한 페이지 요약 (외부 설명용)

> Netscope-AI는 도입 첫 주부터 *당신 환경의 로그를 같이 읽는다*.
> 비슷하게 생긴 메시지들을 자동으로 묶어서 **반복 패턴**을 찾고,
> 당신이 한 번 라벨을 붙이면 **그 패턴은 룰이 되어** 다음 분석부터 매칭된다.
> 그리고 결과는 항상 *역사*까지 함께 답한다 — "이 메시지는 'auth-token-expiry' 패턴 (30일간 47회, 평균 severity HIGH)".
> 룰 직접 작성은 선택, 라벨 한 번이면 충분.

---

## 관련 문서
- 룰 엔진 본체: [`RULE_ENGINE.md`](./RULE_ENGINE.md)
- API 응답 확장: [`API_REFERENCE.md`](./API_REFERENCE.md) — `matched_patterns` 필드
- 대시보드 통합: [`DESIGN_SYSTEM.md`](./DESIGN_SYSTEM.md) — `🆕 learned` 배지, 패턴 차트
- 로드맵 위치: [`PM_ENHANCEMENT_PLAN.md`](./PM_ENHANCEMENT_PLAN.md) — P1-9 / P2-9 / P3-7
