# Rule Engine — 설계와 운영

> **차별점 ①의 정본 문서.** 룰 엔진은 Netscope-AI가 "설명 가능한 AI"를 자처할 수 있게 해주는 핵심 자산이다.
> 코드 위치: `backend/src/analysis/rule_engine.py`

## 목차
- [1. 설계 철학](#1-설계-철학)
- [2. 룰 정의 모델](#2-룰-정의-모델)
- [3. 기본 룰 카탈로그 (R001~R024)](#3-기본-룰-카탈로그-r001r024)
- [4. 스코어링 공식](#4-스코어링-공식)
- [5. severity 매핑](#5-severity-매핑)
- [6. 설명가능성 출력](#6-설명가능성-출력)
- [7. GPT와의 관계](#7-gpt와의-관계)
- [8. 검증 (validation 디렉터리)](#8-검증-validation-디렉터리)
- [9. 새 룰 추가 가이드](#9-새-룰-추가-가이드)
- [10. 미래 — 사용자 정의 룰 DSL (P1-2)](#10-미래--사용자-정의-룰-dsl-p1-2)
- [10-A. 룰 학습 (별도 정본)](#10-a-룰-학습-별도-정본)
- [11. 안티패턴](#11-안티패턴)

---

## 1. 설계 철학

| 원칙 | 의미 | 코드 반영 |
| --- | --- | --- |
| **결정성** | 같은 로그 → 같은 결과. 시간이 지나도 재현 가능 | 정규식·키워드 매칭만 사용, 무작위성 0 |
| **누적 증거** | 단일 룰 매칭만으로는 HIGH 안 됨. 여러 신호가 모일 때 점수 상승 | base score + evidence bonus + interaction bonus |
| **상호작용 보너스** | 도메인 지식 명시 — "timeout + 5xx" 같이 자주 같이 일어나는 패턴은 가중 | `R001+R004 → +0.15` 같은 명시 규칙 |
| **설명가능성 의무** | 모든 매칭 결과는 룰 ID + 점수 + 근거가 응답에 노출 | `matched_rules` 응답 필드 |
| **LLM은 baseline을 흔들 수 없다** | GPT는 **추가**만 가능, 룰 결과를 뒤집지 못함 | `gpt_analyzer.py` system prompt 고정 문구 |

---

## 2. 룰 정의 모델

```python
# backend/src/analysis/rule_engine.py — 개념적 형태 (실제는 plain class)
class Rule:
    id: str                                       # "R001"
    title: str                                    # 사람이 읽는 제목 (한국어)
    score: float                                  # 0..1, 매칭 시 base에 가산
    predicate: Callable[[list[RuleLog]], bool]    # 매칭 여부
    evidence: str                                 # 매칭 근거 문자열
    causes: list[str]                             # 의심 원인 후보
    actions: list[str]                            # 권장 액션
```
> ⚠️ 룰은 ORM `Log` 가 아니라 **`RuleLog`(frozen dataclass)** 를 받는다. `engine.py` 가 ORM→RuleLog 변환을 담당하므로 룰 엔진은 DB를 전혀 모른다.

### 평가 흐름
```
logs ─► [Rule.predicate] ─► matched? ─► evidence_builder ─► (causes, actions 누적)
                                              │
                                              ▼
                                        matched_rules.append(
                                          f"{id} {name} (+{score}) - evidence: ..."
                                        )
```

---

## 3. 기본 룰 카탈로그 (R001~R024)

> 룰셋 버전 `v3.0`. 코드 정본: `rule_engine.py::default_rules()` (Rule 24개). 제목/근거 문자열은 한국어.

| 룰 ID | 점수 | 제목 | 트리거 키워드/조건 | 유형 |
| :---: | :---: | --- | --- | --- |
| **R001** | 0.35 | Timeout 발생 | `timeout`, `timed out`, `ETIMEDOUT` | 키워드 |
| **R002** | 0.35 | Connection 실패 | `connection refused`, `ECONNREFUSED`, `reset by peer` | 키워드 |
| **R003** | 0.25 | DNS / Name Resolution | `ENOTFOUND`, `NXDOMAIN`, `DNS`, `name resolution` | 키워드 |
| **R004** | 0.25 | 5xx 응답 | `5\d\d`, `502`, `503`, `504` | 키워드 |
| **R005** | 0.20 | ERROR 레벨 존재 | `level == ERROR` | 레벨 |
| **R006** | 0.20 | 동일 source ≥ 5회 | `_count_by_source ≥ 5` | 통계 |
| **R007** | 0.40 | Out of Memory | `OOM`, `OutOfMemoryError`, `MemoryError` | 키워드 |
| **R008** | 0.30 | DB 관련 오류 | `database`/`SQL`/`pool`/`deadlock` + ERROR/WARN | 복합 |
| **R009** | 0.35 | 디스크 용량 부족 | `disk full`, `ENOSPC`, `no space left` | 키워드 |
| **R010** | 0.25 | CPU 과부하 | `CPU`, `high load`, `throttl` | 키워드 |
| **R011** | 0.25 | 인증/인가 실패 | auth 키워드 + 4xx 동시 | 복합 |
| **R012** | 0.20 | Rate Limit 초과 | `rate limit`, `too many requests`, `quota` | 키워드 |
| **R013** | 0.45 | 애플리케이션 크래시 | `crash`, `panic`, `segfault`, `fatal` | 키워드 |
| **R014** | 0.30 | 서비스 재시작 | `restart`, `reboot`, `killed`, `terminated` | 키워드 |
| **R015** | 0.30 | SSL/TLS 인증서 문제 | `SSL`/`TLS`/`certificate` + ERROR/WARN | 복합 |
| **R016** | 0.25 | 권한 거부 | `permission denied`, `EACCES`, `access denied` | 키워드 |
| **R017** | 0.15 | 4xx 반복 | `4\d\d` 가 ≥ 3회 | 통계 |
| **R018** | 0.15 | WARN ≥ 3회 | `level == WARN` 가 ≥ 3건 | 레벨 |
| **R019** | 0.40 | 에러 버스트 (1분 내) | 1분 윈도우 내 ERROR 5건+ | 시간윈도우 |
| **R020** | 0.45 | 타임아웃→크래시 연쇄 | timeout 후 5분 내 crash/panic | 순서패턴 |
| **R021** | 0.35 | 높은 에러율 | ERROR/전체 ≥ 50% (5건+) | 통계 |
| **R022** | 0.35 | 다중 source 동시 에러 | 3개+ source에서 ERROR | 상관관계 |
| **R023** | 0.25 | 로그 급증 스파이크 | 최근 1분 발생률이 평균 3배+ | 시간윈도우 |
| **R024** | 0.40 | 연결실패→재시작 연쇄 | conn refused 후 5분 내 restart/killed | 순서패턴 |

### 점수 가중 의도
- **0.40~0.45 (R007/R013)**: 최고 증거력 — OOM·크래시는 단독으로도 진단력. 단, HIGH(≥0.75)는 단독 불가.
- **0.30~0.35 (R001/R002/R009/R008/R014/R015)**: 고~중증거력.
- **0.25 (R003/R004/R010/R011/R016)**: 중증거력. 다른 룰과 함께일 때 결정력.
- **0.15~0.20 (R005/R006/R012/R017/R018)**: 보조 신호. 단독 매칭은 LOW 유지가 의도.

> R005/R006/R017/R018 은 "자주 매칭되지만 단독으로는 약한 신호" — 점수가 낮게 설계된 이유.

---

## 4. 스코어링 공식

```
base        = Σ matched_rule.score
evidence_b  = +0.20 (룰 ≥ 5개)          # ← rule_engine.py::evidence_count_bonus
            | +0.15 (룰 4개)
            | +0.10 (룰 3개)
            | +0.05 (룰 2개)
            | 0
interact_b  = +0.15  if R001 ∧ R004     # timeout + 5xx       ← interaction_bonus()
            + +0.10  if R001 ∧ R005     # timeout + ERROR
            + +0.10  if R002 ∧ R003     # connection + DNS
            + +0.15  if R007 ∧ R013     # OOM + crash
            + +0.12  if R008 ∧ R001     # DB + timeout
            + +0.12  if R009 ∧ R013     # disk + crash
            + +0.10  if R010 ∧ R001     # CPU + timeout
            + +0.15  if R019 ∧ R022     # 에러 버스트 + 다중 source
            + +0.12  if R019 ∧ R021     # 에러 버스트 + 높은 에러율
            + +0.15  if R020 ∧ R007     # 타임아웃→크래시 + OOM
            + +0.15  if R024 ∧ R022     # 연결→재시작 + 다중 source
            + +0.12  if R021 ∧ R008     # 높은 에러율 + DB
            + +0.10  if R023 ∧ R019     # 급증 + 버스트
            # (13개 조합, 누적 합산 — 해당하는 모든 쌍의 보너스가 더해짐)
gpt_b       = +0..0.2  (strategy=gpt 이고 OPENAI_API_KEY 존재 시)
confidence  = min(base + evidence_b + interact_b + gpt_b, 1.0)
```

### 가능한 confidence 범위 (룰만, GPT 제외)

| 매칭 시나리오 | 계산 | 결과 |
| --- | --- | --- |
| 매칭 없음 | 0 | 0.00 — LOW |
| R005만 | 0.20 | 0.20 — LOW |
| R001 단독 | 0.35 | 0.35 — LOW |
| R001 + R005 (2룰, 상호작용 +0.10) | 0.35+0.20+0.05+0.10 | **0.70** — MEDIUM |
| R001 + R004 (2룰, 상호작용 +0.15) | 0.35+0.25+0.05+0.15 | **0.80** — HIGH |
| R001 + R004 + R005 (3룰, 상호작용 +0.15) | 0.35+0.25+0.20+0.10+0.15 | **1.00** (clamp) — HIGH |
| 4룰 이상 | base ≥ 1.0 | 1.00 — HIGH |

→ **HIGH는 단독 룰로는 못 도달**. 항상 ≥ 2개의 신호가 모여야 함 = false-positive 방어선.

---

## 5. severity 매핑

| confidence / 조건 | severity | 의미 |
| --- | --- | --- |
| 치명적 룰 조합 (R020+R007, R019+R022, R024+R022) 또는 `≥ 0.85` & 5개+ 룰 | **CRITICAL** | 즉시 대응, 인프라 장애 수준 |
| `≥ 0.75` 또는 크래시/OOM/연쇄크래시 단독 (R013, R007, R020) | **HIGH** | 액션 필요, 알림 대상 |
| `0.45 ≤ x < 0.75` | **MEDIUM** | 주의 관찰 |
| `< 0.45` | **LOW** | 단순 신호 |

`engine.py`에서 confidence + 룰 조합 기반으로 자동 매핑. 임계값 변경 시 회귀 테스트 (`tests/test_rule_engine.py` + `validation/distribution.py`) 필수.

---

## 6. 설명가능성 출력

분석 응답의 `matched_rules` 배열 형식 (`rule_engine.py`: `f"{rule_id} {title} (+{score:.2f}) - {evidence}"`):
```
"R001 Timeout 발생 (+0.35) - 로그 메시지에 timeout / timed out / ETIMEDOUT 키워드가 포함됨"
```
구성요소:
- `R001` — 룰 ID (감사·문서 참조)
- `Timeout 발생` — 사람용 제목 (한국어)
- `(+0.35)` — 이 룰이 base에 기여한 점수 (`:.2f`)
- `- <근거>` — 매칭 근거 문자열 (어떤 키워드/조건이 매칭됐는지)

> P1-0 보고서 대시보드에서는 이 문자열을 파싱하지 않고 **`matched_rules_detail` 구조화 응답**(`API_REFERENCE.md` 참조)을 사용한다. 문자열 형식은 호환성 위해 유지.

---

## 7. GPT와의 관계

`backend/src/analysis/gpt_analyzer.py`:

```
Rule baseline (canonical)
    │
    ▼
[GPTAnalyzer.enrich(logs, rule_summary)]
    ├─ system: "You are an SRE. Rule baseline is authoritative."
    ├─ user:   raw_logs + rule_summary
    │
    ▼
GPT response → 추가 causes + 추가 actions + confidence_bonus(≤ +0.2)
    │
    ▼
merge: rule.causes + gpt.causes (중복 제거)
```

### 보강의 한계 (의도된 제약)
- ✅ 새 cause/action 추가 가능
- ✅ confidence를 끌어올림 (최대 +0.2)
- ❌ **룰이 매칭한 cause를 삭제하지 못함**
- ❌ **severity를 직접 결정하지 못함** (항상 confidence → severity 함수 경유)
- ❌ **matched_rules 를 수정하지 못함** (감사 가능성 보존)

### 폴백
- `OPENAI_API_KEY` 없음 → GPT 호출 안 함, 룰 결과 그대로 반환. 응답의 `strategy_used`가 `rule`로 떨어짐.
  ⚠️ 이 폴백은 현재 사용자에게 알리지 않음 — P0 작업에서 명시화 필요 (헤더 또는 응답 메타).

---

## 8. 검증 (validation 디렉터리)

### `validation/test_cases.py`
**60개** 시나리오 (`TC-001`~`TC-060`), 대략 4개 군:
1. **Silence/Noise** — INFO 스팸, DEBUG만 → LOW 기대
2. **Single rule** — 룰 1개만 매칭 → LOW~MEDIUM 기대
3. **Multi rule** — 2개 이상 룰 매칭 → MEDIUM~HIGH 기대
4. **Edge** — 혼합 (INFO 다수 + ERROR 소수 등)

각 케이스는 dict: `{ id, description, logs, expected_rules, expected_confidence_level }`.

### `validation/distribution.py`
- 위 50개를 일괄 실행
- severity 분포 (LOW/MEDIUM/HIGH 비율) 출력
- expected와 actual 미스매치 케이스 리포트
- **회귀 테스트로 사용**: 룰 추가/임계값 변경 후 항상 실행 권장

### 실행
```bash
cd backend
python -m src.analysis.validation.distribution
```
> 현재 pytest 통합 안 됨. P0의 P0-7(통합 테스트)에서 pytest 변환 권장.

---

## 9. 새 룰 추가 가이드

### 9-1. 코드 변경

> ⚠️ 아래는 **형태 예시일 뿐** — 실제 R007 은 Out of Memory 룰이다(이미 사용 중인 ID). 새 룰은 미사용 ID(예: R019)를 쓸 것.

```python
# backend/src/analysis/rule_engine.py 의 default_rules() 안

Rule(
    id="R019",
    name="TLS handshake failure",
    score=0.25,
    predicate=lambda logs: any(
        re.search(r"(SSL|TLS).{0,20}(handshake|alert)", l.message, re.I)
        for l in logs
    ),
    evidence_builder=lambda logs: f"TLS handshake errors x{count}",
    causes=[
        "인증서 만료 또는 체인 불일치",
        "프로토콜/암호 스위트 불일치",
    ],
    actions=[
        "openssl s_client 로 직접 점검",
        "인증서 만료일 확인",
    ],
),
```

### 9-2. ID 규칙
- `R001~R099` — 네트워크/인프라 (예약)
- `R100~R199` — HTTP/애플리케이션
- `R200~R299` — 인증/보안
- `R300~R399` — 데이터/스토리지
- `Cxxx` — Customer-defined (P1-2 사용자 정의 룰)

### 9-3. 점수 선정 가이드
| 단독 매칭 시 의도 severity | score 권장 |
| --- | --- |
| LOW (단독으론 신호) | 0.15~0.20 |
| MEDIUM 임계 근처 | 0.25 |
| 단독으로도 진단력 있음 | 0.30~0.35 |
| (0.40 이상은 가급적 사용 금지 — 단일 룰이 HIGH 결정하는 건 false-positive 위험) | — |

### 9-4. 검증
```bash
# 1. 양성/음성 케이스를 test_cases.py 에 추가
# 2. 분포 회귀 확인
python -m src.analysis.validation.distribution
# 3. 기존 테스트가 깨지면 점수 재조정
```

### 9-5. 상호작용 보너스 추가 (선택)
```python
# rule_engine.py 의 interaction_bonus() 안에
if "R001" in matched_ids and "R015" in matched_ids:
    bonus += 0.10   # timeout + SSL/TLS — 인증서 만료 시 자주 동시 발생
```
→ **도메인 지식이 있을 때만** 추가. 임의 추가는 점수 인플레 야기.

---

## 10. 미래 — 사용자 정의 룰 DSL (P1-2)

PM 기획안 §3-2와 짝. 핵심은 **`eval` 금지, 안전한 선언적 DSL**.

```json
{
  "id": "C001",
  "name": "Payment gateway 401 spike",
  "score": 0.30,
  "when": {
    "all": [
      { "field": "source", "op": "eq", "value": "payment-gw" },
      { "field": "message", "op": "matches", "value": "(?i)\\b401\\b" },
      { "field": "_count", "op": "gte", "value": 5 }
    ]
  },
  "evidence_template": "payment-gw 401 x{count}",
  "causes": ["인증 토큰 만료", "API 키 회전 누락"],
  "actions": ["KMS 회전 이력 확인", "토큰 TTL 점검"]
}
```

### 안전 제약
| 항목 | 제약 |
| --- | --- |
| `field` 화이트리스트 | `source`, `message`, `level`, `host`, `_count` |
| `op` 화이트리스트 | `eq`, `contains`, `matches`, `gt`, `gte`, `lt`, `lte` |
| 정규식 | 컴파일 시 길이 제한 (≤ 200자), `re.compile` 후 매칭 타임아웃 ≤ 200ms (ReDoS 방어) |
| 점수 상한 | 사용자 룰 score ≤ 0.30 (시스템 룰의 신뢰 보전) |
| 갯수 상한 | 테넌트당 활성 룰 ≤ 50개 |

### 변환 단계
```
JSON DSL ─► validate (schema + 화이트리스트) ─► compile (regex 등) ─► Rule 인스턴스
```
런타임 추가는 핫리로드 — 재시작 없이 다음 분석부터 적용.

### Dryrun 엔드포인트
`POST /rules/dryrun` — 새 룰을 최근 24시간 로그에 시뮬레이션, severity 분포 변화 + false positive 후보 샘플 반환. **활성화 전 안전 점검 의무화**.

---

## 10-A. 룰 학습 (별도 정본)

P1-2의 사용자 정의 룰이 **사용자가 직접 DSL을 작성**하는 모델이라면, 더 강력한 차원이 하나 더 있다 — **시스템이 사용자 로그를 학습하여 룰 후보를 자동 생성**한다.

> **이 메시지는 'auth-token-expiry' 패턴 (30일간 47회, 평균 severity HIGH)** 처럼,
> 응답에 *역사*까지 함께 답하는 능력은 본 룰 엔진의 자연스러운 다음 단계다.

상세 설계는 별도 정본 문서로 분리:
- 📄 [`RULE_LEARNING.md`](./RULE_LEARNING.md) — 패턴 마이닝 파이프라인 / 카탈로그 / 라벨링 UX / 패턴→룰 승격 / 피드백 가중치 학습 / 데이터 모델 / 로드맵

### 룰 ID 네임스페이스 (재정리)
| Prefix | 출처 | 점수 상한 |
| --- | --- | --- |
| `R001~R099` | 시스템 룰 (도메인 정적) | 0.35 |
| `Cxxx` | Customer-defined (P1-2 DSL) | 0.30 |
| `Lxxx` | Learned (패턴 승격, P3-7) | 0.30 |

신뢰의 우선순위: **시스템 > Customer > Learned**. 학습된 룰의 점수 보정은 절대값 ≤ 0.10 (패턴 학습 시스템의 안전 가드).

---

## 11. 안티패턴

❌ **점수 인플레** — "더 많이 매칭시키려고" score를 0.5 이상으로 설정 → 한 룰이 HIGH 결정 → false positive.
❌ **불명확한 evidence_builder** — 단순히 "matched"만 반환 → 사용자가 *왜* 매칭됐는지 모름. 항상 *어떤 로그*, *몇 건* 명시.
❌ **GPT에게 cause/action을 요청해서 룰을 대체** — 결정성 깨짐. GPT는 보강만.
❌ **상호작용 보너스 남발** — 모든 룰 조합에 보너스 부여 → confidence 거의 항상 1.0 도달 → 변별력 상실.
❌ **CRITICAL 임의 도입** — 임계값만 추가하면 분포 망가짐. P2-2에서 multi-signal 모델로 정식 설계 후 도입.

---

## 부록 — 룰 점수 vs severity 시뮬레이션 표

| 매칭 룰 | 룰 수 | base | evidence | interaction | confidence | severity |
| --- | :---: | :---: | :---: | :---: | :---: | :---: |
| (없음) | 0 | 0.00 | 0 | 0 | 0.00 | LOW |
| R005 | 1 | 0.20 | 0 | 0 | 0.20 | LOW |
| R001 | 1 | 0.35 | 0 | 0 | 0.35 | LOW |
| R001+R005 | 2 | 0.55 | 0.05 | 0.10 | **0.70** | MEDIUM |
| R001+R004 | 2 | 0.60 | 0.05 | 0.15 | **0.80** | HIGH |
| R001+R004+R005 | 3 | 0.80 | 0.10 | 0.15 | **1.00** | HIGH |
| R001+R002+R003 | 3 | 0.95 | 0.10 | 0 | **1.00** | HIGH |
| R002+R003 | 2 | 0.60 | 0.05 | 0.10 | **0.75** | HIGH |
| R005+R006 | 2 | 0.40 | 0.05 | 0 | 0.45 | MEDIUM |

→ HIGH 도달 패턴: **R001+R004 (timeout+5xx)** 가 가장 빠른 경로. 이게 곧 도메인 지식의 핵심.
