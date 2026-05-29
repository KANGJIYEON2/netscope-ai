# Netscope-AI 고도화 기획안 (PM Plan)

> 작성일: 2026-05-08 · 기준 코드: `main` 브랜치 (`c401ae2`) · 작성자: PM 초안
> 본 문서는 현재 MVP/PoC 코드를 기준으로 **무엇을 / 왜 / 어떤 순서로 / 어떻게 측정**할지 정리한 기획안입니다. 시스템 현황은 [`../CLAUDE.md`](../CLAUDE.md) 참고.
>
> ⚠️ **현황 주의 (2026-05-29 갱신)**: 이 문서는 `c401ae2`(pre-auth·인메모리) 시점의 **스냅샷**이다. 이후 머지로 §1 갭 인벤토리의 **G1(DB 영속화)·G2(인증/CORS)·G3(분석 결과 저장)은 이미 해소**됐고, 룰은 **6개 → 18개(R001~R018)** 로 확장됐다. 로드맵(P0~P3) 방향성은 유효하나, "현재 상태" 서술은 [`../CLAUDE.md`](../CLAUDE.md)·[`../README.md`](../README.md) 를 우선 신뢰할 것.

---

## 0. Executive Summary

| 항목 | 내용 |
| --- | --- |
| **현재 위치** | 룰 엔진 + 옵션 GPT가 동작하는 PoC. 단일 호스트·인메모리·인증 없음 |
| **6개월 목표** | "내 인프라에 깔아 두면 장애 원인 후보가 자동으로 정렬되는 도구"로 외부 베타 진입 |
| **12개월 비전** | **Explainable AIOps for SRE/네트워크 팀** — 룰 + LLM + 자체 학습 신호의 하이브리드 진단 플랫폼 |
| **차별점 ①** | 결과에 항상 `matched_rules` 가 노출되는 **설명 가능한 AI** — "블랙박스 GPT가 우긴다"는 SRE 거부감 해소 |
| **차별점 ②** | **데모/회고 자리에서 그대로 띄울 수 있는 보고서급 대시보드** — 같은 정보를 가진 경쟁 도구도 *"보여주는 화면"* 에서 진다 |
| **차별점 ③** | **사용자 환경에 함께 자라는 룰셋** — 사용자가 보낸 로그에서 *반복 패턴*을 자동 발견하고, 라벨 한 번이면 룰이 된다. 응답에는 *"이건 P-AUTH-401 패턴, 과거 47회 봤음"* 처럼 **역사**가 함께 붙는다 ([RULE_LEARNING.md](./RULE_LEARNING.md)) |

### 한 문장 포지셔닝
> **"Datadog/Grafana는 그래프를 그리고, ChatGPT는 문장을 쓰고, Netscope-AI는 *읽히는 인시던트 보고서*를 *당신의 로그를 학습한 룰*로 만들어낸다."**

---

## 1. 현재 갭 인벤토리 (코드 기반)

| # | 영역 | 현재 상태 | 사용자 영향 | 심각도 |
| --- | --- | --- | --- | :---: |
| G1 | **DB 영속화** | ORM·repository 정의만, 라우터 미연결 | 재시작 시 전체 로그/분석 유실 | 🔴 |
| G2 | **인증/CORS** | `core/security.py` 빈 파일, CORS=`*` | 누구나 POST 가능 → 사실상 운영 불가 | 🔴 |
| G3 | **분석 결과 저장** | `save_analysis_result` 호출 없음 | 사후 감사·트렌드 분석 불가 | 🔴 |
| G4 | **헬스 엔드포인트** | 본문 비어 있음 | k8s liveness/readiness 불가 | 🟠 |
| G5 | **GPT 모델명** | `gpt-4.1-mini` 표기 | 의도가 `gpt-4o-mini`라면 호출 실패 | 🟠 |
| G6 | **멀티 인스턴스** | 인메모리 싱글톤 | 워커>1이면 로그 분산 | 🟠 |
| G7 | **로그 파서** | `parser.py` 빈 파일 | JSON/syslog/구조화 로그 미지원 | 🟠 |
| G8 | **룰 관리** | 코드 하드코딩 | 사용자 룰 추가/수정 불가, 핫리로드 불가 | 🟡 |
| G9 | **에이전트 resume** | 매 시작 시 EOF | 재시작 사이 라인 누락 | 🟡 |
| G10 | **7일 윈도우** | README에만 언급 | 리텐션·비용 제어 부재 | 🟡 |
| G11 | **프론트 에러 UX** | `alert("Analysis failed")` | 사용자가 원인 모름 | 🟡 |
| G12 | **테스트 커버리지** | `test_health.py` 1개 | 회귀 방어 사실상 0 | 🟡 |
| G13 | **알림/연동** | 없음 | 결과를 사람이 직접 봐야 함 | 🟡 |
| G14 | **CRITICAL 매핑 누락** | enum만 존재, 매핑 룰 없음 | severity 한 단계 부족 | 🟢 |
| G15 | **결과 Export** | 없음 | 인시던트 회고에 복붙 의존 | 🟢 |
| G16 | **대시보드/보고서 UI** | 단일 페이지에 리스트+패널만, 차트·타임라인·그래프 없음 | 데모/세일즈/회고 자리에서 임팩트 부족, "그래서 뭐가 일어났는지" 한눈에 안 들어옴 | 🔴 |
| G17 | **룰 학습 / 패턴 마이닝** | 미존재 — 6개의 정적 룰만 있음 | 사용자 고유 로그 (예: payment-gw 401)는 영영 매칭 안 됨, 도입 첫 주에 가치를 못 느낌 | 🔴 |

**범례**: 🔴 운영 차단 / 🟠 운영 위험 / 🟡 사용성 저하 / 🟢 nice-to-have

---

## 2. 우선순위 로드맵

### 🚀 P0 — "운영 가능한 베타" (M1, 4주)
**목표: 재시작해도 데이터가 살아 있고, 외부에 안전하게 노출 가능한 상태**

| # | 기능 | 갭 해소 | 인수 기준 |
| --- | --- | --- | --- |
| P0-1 | PostgreSQL 영속화 활성화 | G1, G3 | 로그/분석 결과가 DB에 저장되고 재시작 후 조회 가능. Alembic 마이그레이션 1차 도입 |
| P0-2 | API Key 인증 + 테넌트 헤더 | G2 | `X-API-Key` 검증, `X-Tenant-ID`로 데이터 스코프 분리. 401/403 처리 |
| P0-3 | CORS 허용 도메인 화이트리스트 | G2 | `ALLOWED_ORIGINS` env로 제어, 와일드카드 제거 |
| P0-4 | `/health`, `/readiness` 구현 | G4 | DB·OpenAI 연결 점검, k8s probe 사용 가능 |
| P0-5 | GPT 모델명 정정 + 재시도/타임아웃 | G5 | `gpt-4o-mini` (또는 검증된 모델), 30s 타임아웃, 1회 재시도 |
| P0-6 | 분석 결과 ID 발급 + GET 조회 | G3 | `GET /analysis/{id}` 동작, 결과에 `id` 필드 추가 |
| P0-7 | 핵심 시나리오 통합 테스트 | G12 | 로그 POST → 분석 → 결과 조회의 e2e pytest 5개 이상 |

**산출 지표**
- API 99분위 응답 시간 < 1.5s (룰 단독), < 8s (GPT)
- 콜드 스타트 후 7일 누적 로그 손실 0건
- 보안: `gobuster`/`nuclei` 기본 스캔 통과

---

### 🛠 P1 — "팀이 쓰는 제품" (M2, 4~6주)
**목표: SRE 팀 1곳을 진짜 베타 고객으로 받을 수 있는 상태 + 데모 자리에서 *"오, 화면 좋다"* 가 자동으로 나오는 UI**

| # | 기능 | 갭 해소 | 핵심 사양 |
| --- | --- | --- | --- |
| **P1-0** ⭐ | **인시던트 보고서 대시보드 (Flagship UI)** | **G16, G3, G11** | 메인 셀링 포인트. 별도 섹션 §3-0 참고 |
| P1-1 | **룰 관리 API + UI** | G8 | `GET/POST/PATCH/DELETE /rules`, 룰을 JSON으로 export/import. 활성화 토글. 핫리로드 (재시작 불필요) |
| P1-2 | **사용자 정의 룰** | G8 | predicate를 안전한 DSL (정규식 + 키워드 + level 필터) 로 표현. eval 금지, sandboxed |
| P1-3 | **분석 이력 페이지** | G3, G15 | 최근 분석 N건 리스트 → 상세는 P1-0 보고서 뷰로 연결 |
| P1-4 | **멀티테넌시 강화** | G2 | 테넌트별 룰셋, 테넌트별 OpenAI 키, 테넌트별 사용량 |
| P1-5 | **Webhook 알림** | G13 | severity ≥ HIGH 시 등록된 URL로 POST (Slack incoming webhook 호환) |
| P1-6 | **에이전트 resume** | G9 | 마지막 inode + offset을 로컬 `.netscope-agent-state` 에 저장, 재시작 시 이어서 |
| P1-7 | **구조화 로그 파서** | G7 | JSON 라인 / syslog RFC 5424 / Apache combined 자동 감지 → `message`, `level`, `timestamp` 추출 |
| P1-8 | **프론트 에러 UX 개선** | G11 | API 4xx/5xx 메시지를 toast로 노출, 분석 실패 시 재시도 버튼 |
| **P1-9** ⭐ | **패턴 마이닝 백그라운드 수집 (룰 학습 L0)** | **G17** | drain3 통합, 들어오는 로그에서 템플릿 자동 추출 → `patterns` 카탈로그 적재. 사용자 노출 없이 7일 수집 후 알림 카드 활성. 정본: [`RULE_LEARNING.md`](./RULE_LEARNING.md) |

**산출 지표**
- 베타 고객 1곳 도입, MAU 5명 이상
- 사용자 정의 룰 평균 ≥ 3개 / 테넌트
- HIGH 알림 수신 → 인지까지 중앙값 < 5분

---

### 🌐 P2 — "차별화 + 확장" (M3, 6~8주)

| # | 기능 | 핵심 사양 |
| --- | --- | --- |
| P2-1 | **시간 윈도우 분석** (7일 슬라이딩) | 동일 시그니처가 7일 내 N회 발생 시 자동 escalate, 트렌드 차트 |
| P2-2 | **CRITICAL severity 매핑** | 다중 룰 + 시간 밀집도 + 영향 범위(소스 다양성)로 CRITICAL 산정 |
| P2-3 | **Redis 캐시** | 동일 입력 (log_ids 정렬 해시) 분석 결과 5분 캐시, GPT 재호출 방지 |
| P2-4 | **GPT 비용/토큰 가시성** | 호출당 토큰·비용 기록, 테넌트별 일일 한도 + 알림 |
| P2-5 | **룰 A/B 평가** | 룰 변경 시 과거 N일 로그에 새 룰셋을 시뮬레이션, confidence 분포 비교 리포트 |
| P2-6 | **결과 Export (PDF/JSON)** | 인시던트 회고용 1-page PDF (severity·causes·actions·matched rules·관련 로그) |
| P2-7 | **Slack/Teams 통합** | Webhook을 넘어선 양방향 (스레드 생성, ack/dismiss) |
| P2-8 | **OpenTelemetry** | 트레이스/메트릭/구조화 로깅 (`core/logging.py` 채우기) |
| **P2-9** ⭐ | **패턴 라벨링 UX + 분석 결과 통합 (룰 학습 L1·L2)** | candidate 패턴 알림 카드, `/patterns` 관리 페이지, 분석 응답에 `matched_patterns[]` 추가, 보고서 대시보드의 "🆕 learned" 배지로 노출. 라벨링 UX는 [`RULE_LEARNING.md`](./RULE_LEARNING.md) §6 참고 |

---

### 🔭 P3 — "AIOps로의 도약" (M4+, 후속)

| # | 기능 | 핵심 가치 |
| --- | --- | --- |
| P3-1 | **자체 학습 보조 모델** | 사용자가 dismiss/confirm한 결과로 룰 점수를 가중치 학습 (logistic regression부터) — P3-7과 합쳐서 진행 |
| P3-2 | **상관관계 그래프** | source × time × rule 매칭의 인과 그래프 시각화. "gateway timeout 직전에 db conn-refused 25건" 같은 자동 narrative |
| P3-3 | **이상 탐지** | source별 baseline 대비 ERROR 빈도 z-score, 룰과 독립적인 anomaly 신호 |
| P3-4 | **HYBRID strategy 실구현** | 룰 + GPT + anomaly 신호 + 학습된 패턴을 가중 결합, 각 컴포넌트 기여도 노출 |
| P3-5 | **온프레미스 LLM** | OpenAI 외 vLLM/Ollama 백엔드 지원 (보안/규제 산업) |
| P3-6 | **에이전트 자동 배포** | DaemonSet helm chart, systemd unit, Windows 서비스 인스톨러 |
| **P3-7** ⭐ | **패턴 자동 승격 + 피드백 가중치 (룰 학습 L3·L4)** | confirm 누적이 임계 넘으면 `labeled` → `promoted` 자동 승격, 단순 카운터 → logistic regression 으로 점수 보정값 학습. 안전 가드(±0.10) 포함. [`RULE_LEARNING.md`](./RULE_LEARNING.md) §9 |
| P3-8 | **임베딩 기반 패턴 의미 유사도** | drain 한계 보완 — "auth token expired" 와 "JWT validation failed" 를 의미상 같은 패턴으로 묶기. 후순위 |

---

## 3. 핵심 기능 상세 명세 (P0/P1 발췌)

### 3-0. ⭐ 인시던트 보고서 대시보드 (P1-0, Flagship)

> **콘셉트**: 분석 결과 한 건을 *"한 페이지짜리 인시던트 리포트"* 로 띄운다. 캡처해서 슬랙에 던져도, 회고 자리에서 빔으로 띄워도 그대로 자료가 되는 화면.

#### 3-0-1. 무엇을 / 왜
- **무엇**: 기존의 단순 "결과 패널"을 대체하는 **레포트 그레이드 대시보드 뷰**.
- **왜**:
  1. **세일즈/데모**: 룰·LLM 설명력은 강한데 *보여줄 화면*이 약하면 첫인상이 안 산다.
  2. **사용자**: SRE는 인시던트 후 회고 문서를 매번 손으로 만든다 → 우리가 그 문서를 자동 생성하면 도구 도입 ROI가 즉시 보인다.
  3. **차별화**: 같은 결과 데이터라도 "리스트 + 텍스트"는 ChatGPT 답변 수준, "구조화된 리포트 UI"는 제품의 격이 된다.

#### 3-0-2. 화면 와이어프레임 (요구 정의용 ASCII)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Netscope-AI                                  Tenant ▾  ⚙  🔔(2)  ⨀ KJY │
├─────────────────────────────────────────────────────────────────────────┤
│  ◀ Back to History    Incident Report  #IR-20260508-0042                │
│                                                                         │
│  ┌──[ HEADER ]──────────────────────────────────────────────────────┐   │
│  │  🔴 HIGH     Confidence 0.82       Strategy: Rule + GPT          │   │
│  │  Gateway timeout cascade — 12 logs across 3 sources              │   │
│  │  Detected 2026-05-08 14:31:02 KST · Window 06m 12s · 1 host      │   │
│  │  [ Acknowledge ] [ Export PDF ] [ Share Slack ] [ Re-run ]       │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──[ TIMELINE ]────────────────────────────────────────────────────┐   │
│  │  14:25 ─┬───────────●●──────●──●●●●─────●────●●●─── 14:32        │   │
│  │         │            R001    R001 R004  R001  R004                │   │
│  │   level │   ··········■■■····■■■■■■····■■■■■■■····  ERROR        │   │
│  │   level │   ····█····█·····█······█········█·····  WARN          │   │
│  │   src   │   gateway / payment-gw / orders                         │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌──[ MATCHED RULES ]────────────────┐  ┌──[ CONFIDENCE BREAKDOWN ]──┐  │
│  │ R001 Timeout            +0.35  ▓▓ │  │  Base score        0.60   │  │
│  │ R004 5xx upstream       +0.25  ▓  │  │  Evidence bonus    +0.10  │  │
│  │ R005 ERROR level        +0.20  ▓  │  │  Interaction bonus +0.15  │  │
│  │ R006 Repeated source    +0.20  ▓  │  │  GPT bonus         +0.07  │  │
│  │   (12 evidences shown)            │  │  ────────────────  ─────  │  │
│  │                                   │  │  Final             0.82   │  │
│  └───────────────────────────────────┘  └────────────────────────────┘  │
│                                                                         │
│  ┌──[ SUSPECTED CAUSES ]─────────────┐  ┌──[ RECOMMENDED ACTIONS ]──┐   │
│  │  ① upstream 지연 (rule)           │  │  □ upstream 헬스체크       │   │
│  │  ② proxy 오류 (rule)              │  │  □ timeout 설정 재검토     │   │
│  │  ③ 인증 토큰 회전 누락 (gpt 보강) │  │  □ KMS 회전 이력 확인       │   │
│  └───────────────────────────────────┘  └────────────────────────────┘  │
│                                                                         │
│  ┌──[ RELATED LOGS · 12 ]───────────────────────────────────────────┐   │
│  │  14:30:58  ERROR  gateway     Request timed out after 30s        │   │
│  │  14:31:01  ERROR  gateway     Upstream returned 502              │   │
│  │  14:31:02  WARN   payment-gw  Retry 3/3 failed: ECONNREFUSED     │   │
│  │  ...                                              [ View raw ▾ ] │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 3-0-3. 모듈별 사양

| 모듈 | 데이터 소스 | 핵심 요건 |
| --- | --- | --- |
| **Header** | `AnalysisResultDTO` | severity별 액센트 컬러, confidence 큰 숫자, window/source 카운트는 입력 로그에서 계산 |
| **Timeline** | 입력 로그 + matched_rules | 가로축 = 시간, 점 = 룰 매칭 이벤트, 띠 = level density. 100~500 로그까지 부드럽게(Canvas 또는 lightweight SVG, d3 의존 최소화) |
| **Matched Rules** | `matched_rules[]` 파싱 | 룰 ID·기여 점수·근거 미리보기. 클릭 시 해당 근거 로그로 스크롤 |
| **Confidence Breakdown** | `rule_engine.aggregate` 노출 확장 필요 | base / evidence / interaction / gpt 4개 컴포넌트로 분해. **백엔드 API 변경 동반** (다음 섹션 참고) |
| **Causes / Actions** | `suspected_causes`, `recommended_actions` | 룰 vs GPT 출처 구분 배지. 액션은 체크박스 (acknowledge 시 저장) |
| **Related Logs** | `log_ids` | severity 색 코딩, 룰 매칭된 라인은 좌측에 룰 ID 라벨, "View raw" 토글 |

#### 3-0-4. 백엔드 변경 동반사항 (UI 때문에 새로 필요)

이 화면을 위해 **API 응답 확장**이 필요합니다 (P1-0 백엔드 작업으로 묶음):

```python
# AnalysisResultDTO 추가 필드
class ConfidenceBreakdown(BaseModel):
    base: float
    evidence_bonus: float
    interaction_bonus: float
    gpt_bonus: float
    final: float

class MatchedRuleDetail(BaseModel):
    id: str           # "R001"
    name: str         # "Timeout detection"
    score: float
    evidence: list[str]
    matched_log_ids: list[str]  # 어떤 로그가 이 룰에 매칭됐는지

class AnalysisResultDTO(...):
    ...
    breakdown: ConfidenceBreakdown
    matched_rules_detail: list[MatchedRuleDetail]   # 기존 문자열 배열은 호환용으로 유지
    window: TimeWindow                              # {start, end, duration_sec}
    sources: list[SourceSummary]                    # source별 카운트
```
- `rule_engine.aggregate()` 에 *어떤 로그가 어떤 룰에 매칭됐는지* 추적이 추가되어야 함 (현재는 evidence 문자열만 누적).

#### 3-0-5. 디자인 시스템 가드레일

- **Severity 컬러 토큰**: `--sev-low: emerald-500`, `--sev-mid: amber-500`, `--sev-high: rose-500`, `--sev-crit: violet-600`
- **타이포**: 헤더는 모노스페이스 숫자(`tabular-nums`)로 confidence 정렬. 인시던트 ID도 모노.
- **상태 표시**: badge → pill → chip 의 위계 명확화. 색은 5톤 이내로 제한 (남발 금지).
- **다크 우선**: 현재 zinc-950 베이스 유지, 단 카드 배경은 zinc-900 + 1px ring-zinc-800 으로 깊이 부여.
- **차트 라이브러리**: 의존성 폭증 방지 — **선차트/막대 자체 SVG 컴포넌트** + 복잡한 차트만 `recharts` 1개 정도로 한정.
- **반응형**: 1280px 데스크톱 우선 (대시보드는 큰 화면이 본진), 768px 이하는 카드 세로 스택으로 폴백.

#### 3-0-6. Export PDF (P2-6와 결합)

- 같은 보고서 뷰를 **A4 1~2페이지로 인쇄용 CSS** (`@page`, `@media print`) 적용 → 별도 PDF 빌더 없이 브라우저 인쇄로 동일 디자인 보장.
- Export 버튼은 PDF + 마크다운 + JSON 3종.

#### 3-0-7. 인수 기준 (Definition of Done)

- [ ] 동일 분석을 두 번 열어도 동일한 차트가 그려진다 (결정성)
- [ ] 로그 500건 입력해도 렌더 < 200ms (가상 스크롤 / 차트 다운샘플링)
- [ ] 모든 패널이 단독으로 캡처 가능 (대시보드 전체가 스크린샷 자료가 되는 게 목표)
- [ ] `print` 미디어로 출력 시 헤더·룰·근거가 1~2 페이지 안에 깨지지 않게 들어간다
- [ ] WCAG AA — 색만으로 severity 구분하지 않음 (아이콘 동반)

#### 3-0-8. 단계 분리 (스프린트 쪼개기 제안)

1. **Sprint A (1주)**: API 확장 (breakdown, matched_rules_detail) + 기존 페이지를 새 라우트 `/incident/[id]` 로 이동
2. **Sprint B (1주)**: Header + Matched Rules + Confidence Breakdown 패널 (텍스트/카드 위주, 차트 없음)
3. **Sprint C (1.5주)**: Timeline 차트 (level density + 룰 마커)
4. **Sprint D (0.5주)**: Print CSS + Export 버튼 + Slack 공유 링크
5. **Sprint E (예비)**: 인터랙션 폴리싱 (룰 클릭 → 로그 스크롤, hover tooltip)

---

### 3-1. PostgreSQL 영속화 (P0-1)

**왜 지금**: 인메모리는 PoC 한정. 사용자가 "어제 그 분석 다시 보여줘"를 못 함.

**스펙**
- 테이블: `logs`, `analysis_results`, `tenants`, `api_keys`
- 마이그레이션 도구: Alembic
- 라우터에서 SQLAlchemy `Session` 의존성 주입 (`Depends(get_db)`)
- `InMemoryLogStorage` 는 **개발/테스트 모드**로 유지 (env로 토글)

**사용자 스토리**
> SRE A는 어제 14시에 일어난 timeout 사건을 다시 열어, 그때 매칭됐던 룰과 추천 액션을 인시던트 리뷰 자료로 가져간다.

**리스크**
- 로그 폭증 시 DB 비용 → P2-1의 7일 리텐션과 함께 설계 필요.
- 마이그레이션 실수 → CI에 `alembic upgrade head` 단계 필수.

---

### 3-2. 사용자 정의 룰 DSL (P1-2)

**왜 지금**: 6개의 기본 룰만으론 도메인 다양성 못 따라감. 보안상 `eval` 금지.

**DSL 예시 (JSON)**
```json
{
  "id": "C001",
  "name": "Payment gateway 401 spike",
  "score": 0.30,
  "when": {
    "all": [
      { "field": "source", "op": "eq", "value": "payment-gw" },
      { "field": "message", "op": "matches", "value": "(?i)\\b401\\b" }
    ]
  },
  "evidence_template": "payment-gw 401 발생 (count={count})",
  "causes": ["인증 토큰 만료", "API 키 회전 누락"],
  "actions": ["KMS 회전 이력 확인", "토큰 TTL 점검"]
}
```

**제약**
- `field` 화이트리스트: `source | message | level | host`
- `op` 화이트리스트: `eq | contains | matches(regex) | gt | lt`
- 정규식은 컴파일 시 길이/복잡도 제한 (ReDoS 방지)

**관리 UX**
- `/rules` 페이지: 표 + 토글 + import/export
- 새 룰 저장 시 **드라이런** 모드 — 최근 24시간 로그에 적용해 매칭 건수만 보여주고 활성화 여부 결정

---

### 3-3. 룰 A/B 평가 (P2-5)

**왜**: 룰 추가/수정이 기존 분석 분포에 미치는 영향을 사전 검증해야 SRE가 안심하고 룰을 늘릴 수 있음.

**스펙**
- 입력: 룰셋 v1 (현행), v2 (편집안), 시뮬레이션 기간 (예: 최근 7일)
- 출력: severity 분포 비교 (HIGH/MEDIUM/LOW 막대), false positive 후보 (이전 LOW → 신규 HIGH로 점프한 케이스 샘플)
- `validation/distribution.py` 를 멀티 룰셋 비교가 가능하도록 일반화

---

### 3-4. 알림 (P1-5 → P2-7)

**P1 단계 (Webhook)**
- 테넌트 설정에 `webhook_url`, `min_severity` 두 필드.
- POST payload (Slack incoming webhook 호환):
  ```json
  { "text": "🚨 [HIGH] gateway timeout x12\n신뢰도 82%\nhttps://app.netscope/analysis/{id}" }
  ```
- 재시도: 5xx 시 지수 백오프 3회, 실패는 테넌트별 알림 이력에 기록.

**P2 단계 (양방향 Slack)**
- 슬래시 커맨드 `/netscope ack <id>` → 결과를 acknowledged 처리, 다음 같은 시그니처는 일정 시간 dedupe.

---

## 4. 비기능 요구사항 (NFR)

| 분야 | 목표 |
| --- | --- |
| 가용성 | 99.5% (베타), 99.9% (GA) — DB·LLM 의존성 격리 |
| 응답 시간 | 룰 분석 P99 < 1.5s (로그 100건 기준), GPT 분석 P99 < 8s |
| 보안 | API Key 해시 저장 (bcrypt/argon2), 모든 PII 로그 마스킹 옵션, 감사 로그 (analysis 호출 기록) |
| 비용 | GPT 호출 캐시 적중률 ≥ 30% (P2 이후), 테넌트별 일일 한도 |
| 관찰성 | 모든 라우트 OpenTelemetry trace, 룰 매칭률·LLM 토큰 메트릭 노출 |

---

## 5. 측정 지표 (성공 정의)

### 제품 지표
- **DAU/MAU** (베타): 활성 SRE 사용자 수
- **분석 호출 수 / 일** : 사용 빈도
- **HIGH→인지 시간 중앙값** : 알림 도달성
- **사용자 정의 룰 수 / 테넌트** : 끈적함(stickiness)
- **룰 매칭률 분포**: LOW가 80% 넘으면 룰 부족 신호, HIGH가 50% 넘으면 false positive 의심
- **🆕 보고서 공유율**: 분석 1건당 PDF/Slack 공유 횟수 — 대시보드가 진짜 "보고서로 쓰이는가"의 직접 지표
- **🆕 액션 체크율**: recommended_actions 체크박스 완료율 — 화면이 워크플로우로 들어가 있는지의 신호
- **🆕 패턴 라벨링 전환율**: candidate → labeled 패턴 비율. 시스템이 보여주는 패턴이 *진짜 의미 있는지* 의 신호. 목표 30%+
- **🆕 학습 룰 매칭 비여**: HIGH severity 결과에서 학습 룰(L*)이 차지하는 비율 — 사용자 환경에 우리가 정말 적응하고 있는가
- **🆕 패턴 history 효과**: "이전 N회 봤음" 문구가 포함된 결과의 평균 acknowledge 시간 vs 미포함 — 역사 정보가 인지를 빠르게 하는가

### 기술 지표
- API 응답 P50/P99
- LLM 호출 비용 / 분석 1건
- 캐시 적중률
- 에이전트 → 백엔드 라인 손실률 (P1-6 도입 후)

---

## 6. 리스크와 가드레일

| 리스크 | 영향 | 가드레일 |
| --- | --- | --- |
| LLM 응답이 룰 결과와 모순 | 결정성/신뢰 훼손 | system prompt "Rule baseline is authoritative" 유지, GPT는 추가만 가능, 충돌 시 GPT 무시 |
| 사용자 정의 룰의 ReDoS | 백엔드 다운 | 정규식 컴파일 제한 + 실행 타임아웃 (예: 200ms) |
| 로그 PII 유출 | 컴플라이언스 | 테넌트별 마스킹 정책, GPT 호출 시 옵트인 |
| 멀티테넌시 데이터 누수 | 사고 직결 | 모든 쿼리에 `tenant_id` 강제 — 리뷰 시 raw SQL 금지 정책 |
| GPT 비용 급증 | 운영 부담 | P2-3 캐시 + P2-4 한도, 무료 플랜은 룰 전용 |

---

## 7. 분기 계획 (제안)

```
M1 (4주)     ─ P0 전부 + P1-1 시작
M2 (4~6주)   ─ P1 완성, 베타 고객 1곳 온보딩
M3 (6~8주)   ─ P2 1차 (캐시 + 비용 가시성 + Export), 고객 3곳 확장
M4 (8주~)    ─ P3 탐색 (자체 학습 보조 모델 PoC)
```

---

## 8. 오픈 이슈 / 결정 필요 사항

1. **DB 선택**: 단일 PostgreSQL vs OLAP 병행 (ClickHouse) — 로그 볼륨 가정에 따라 변동.
2. **LLM 정책**: OpenAI 단독 vs 멀티 프로바이더 (Anthropic/Bedrock) — 베타 고객 요구에 따라.
3. **에이전트 배포 모델**: 사이드카 vs DaemonSet vs 외부 에이전트 (Vector/Fluent Bit 플러그인) — P3-6에서 결정.
4. **무료 플랜 범위**: 룰만 무료 / GPT는 유료? 또는 테넌트 토큰 쿼터?
5. **데이터 보존 기간 기본값**: 7일 vs 30일 — 비용 vs 회고 가치 트레이드오프.

---

## 9. 다음 액션 (이번 주 내)

- [ ] PM: 본 문서로 엔지니어링 합의 미팅, P0 백로그 티켓 발행
- [ ] **PM/디자인: 보고서 대시보드 (P1-0) Figma 와이어 1차 — §3-0-2 ASCII 기반 픽셀 시안화**
- [ ] **PM: 룰 학습(`RULE_LEARNING.md`) 정독 후 베타 SRE 인터뷰에 "패턴 라벨링 워크플로우" 검증 질문 포함**
- [ ] **백엔드: drain3 의존성 도입 가능 여부 검토 (라이선스 Apache 2.0 OK), 카탈로그 테이블 마이그레이션 초안**
- [ ] 백엔드 리드: PostgreSQL 스키마 초안 + Alembic 셋업 PR (P0-1과 P1-9의 `patterns` 테이블 함께 설계)
- [ ] 백엔드: GPT 모델명 정정 + 헬스 엔드포인트 PR (작은 단위로 빠르게)
- [ ] **백엔드: `AnalysisResultDTO` 확장 스펙 합의 (breakdown / matched_rules_detail / window / sources)**
- [ ] 프론트: 분석 결과에 `id` 필드 표시 + 에러 toast 컴포넌트
- [ ] **프론트: `/incident/[id]` 라우트 스캐폴딩, 기존 결과 패널 이주 경로 검토**
- [ ] DevOps: API Key 인증 미들웨어 인터페이스 합의
- [ ] PM: 베타 후보 SRE 팀 2곳과 사전 인터뷰 (룰 정의 니즈 + **"이 화면이면 회고에 쓸 만한가"** 동시 검증)

---

## 10. 부록 — 한 줄 비전 보드

| 슬로건 | 대상 | 단일 가치 |
| --- | --- | --- |
| 결과를 *설명하는* AIOps | 중견 이상 SRE/네트워크팀 | "왜 그 판단인가"를 룰 ID로 증명 |
| 도입 5분, 분석 5초 | 스타트업 인프라팀 | 단일 스크립트 에이전트 + 셀프호스트 |
| **인시던트가 끝나면 보고서가 이미 와 있다** | **회고 문화가 강한 팀** | **자동 생성되는 한 페이지 보고서 (P1-0)** |
| **당신의 로그를 같이 읽는 룰셋** | **고유 시스템을 가진 팀 (전부 다름)** | **패턴 학습으로 도입 첫 주에 환경 맞춤 룰 자동 생성 (P1-9~P3-7)** |
| 룰은 우리 팀이, 추론은 같이 | 컴플라이언스 산업 | 사용자 룰 + 온프레 LLM (P3) |
