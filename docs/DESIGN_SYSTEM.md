# Design System — Incident Report Dashboard

> **목적**: 차별점 ② "보고서급 대시보드"의 일관성·임팩트를 보장하는 디자인 토큰·컴포넌트 룰북.
> **현재 상태 (2026-05-29)**: 본 문서는 대부분 **목표 스펙(SSOT)** 이며 아직 코드에 미반영. 구체적으로:
> - `frontend/src/styles/severity.ts` = **빈 파일** (§9 의 `severityToken`/`ruleColor` 헬퍼 미구현)
> - `globals.css` 에 §9-1 의 `--surface-*`/`--sev-*` CSS 변수 **없음**
> - 실제 `SeverityBadge.tsx` 는 스펙과 다름 — prop 이 `level: "LOW"|"MEDIUM"|"HIGH"|"UNKNOWN"`(§5-1 의 `severity`+`CRITICAL`+`confidence` 아님), 색은 `bg-red-600`/`bg-yellow-500`/`bg-emerald-600` **하드코딩**(이 문서가 금지하는 안티패턴), 아이콘·신뢰도 표시 없음
>
> → 즉 이 문서는 "이렇게 만들자"는 타깃이고, 새 컴포넌트는 여기에 맞춰 구현하면서 `severity.ts` 를 채우는 게 정답이다.

## 목차
- [1. 디자인 원칙](#1-디자인-원칙)
- [2. 컬러 토큰](#2-컬러-토큰)
- [3. 타이포그래피](#3-타이포그래피)
- [4. 스페이싱·레이아웃 그리드](#4-스페이싱레이아웃-그리드)
- [5. 컴포넌트 룰](#5-컴포넌트-룰)
- [6. 데이터 시각화](#6-데이터-시각화)
- [7. 인쇄/PDF 모드](#7-인쇄pdf-모드)
- [8. 접근성 가드레일](#8-접근성-가드레일)
- [9. 토큰 → 코드](#9-토큰--코드)

---

## 1. 디자인 원칙

| # | 원칙 | 의미 |
| --- | --- | --- |
| 1 | **데이터 밀도 > 장식** | 한 화면이 곧 보고서. 화이트스페이스는 충분히, 그러나 정보를 가리는 그라데이션·이펙트는 금지 |
| 2 | **색은 의미만 전달** | severity 외의 데코용 컬러 금지. 5톤 이내 |
| 3 | **숫자는 모노스페이스** | confidence·점수·시간은 `tabular-nums` 로 정렬 |
| 4 | **다크 우선, 인쇄는 라이트로 자동** | 발표/회고 양쪽 시나리오 모두 자연스럽게 |
| 5 | **모듈 단위 캡처 가능** | 패널 1개를 잘라 슬랙에 붙여도 맥락이 살아 있어야 함 |

---

## 2. 컬러 토큰

> 베이스: Tailwind 4 zinc / emerald / amber / rose / violet / sky.

### 2-1. 표면 (Surface)

| 토큰 | 다크 | 라이트(인쇄) | 용도 |
| --- | --- | --- | --- |
| `--surface-base` | `zinc-950` | `white` | 페이지 배경 |
| `--surface-card` | `zinc-900` | `zinc-50` | 패널 배경 |
| `--surface-card-elevated` | `zinc-800` | `white` + shadow | hover/모달 |
| `--surface-divider` | `zinc-800` | `zinc-200` | ring/border |

### 2-2. 텍스트

| 토큰 | 다크 | 라이트 |
| --- | --- | --- |
| `--text-primary` | `zinc-100` | `zinc-900` |
| `--text-secondary` | `zinc-400` | `zinc-600` |
| `--text-muted` | `zinc-500` | `zinc-500` |

### 2-3. Severity (의미 컬러)

| 토큰 | 컬러 | 용도 | 동반 아이콘 |
| --- | --- | --- | --- |
| `--sev-low` | `emerald-500` | LOW | `check` |
| `--sev-mid` | `amber-500` | MEDIUM | `alert-triangle` |
| `--sev-high` | `rose-500` | HIGH | `alert-octagon` |
| `--sev-crit` | `violet-600` | CRITICAL (P2-2) | `siren` |

배경/배지 전용 *희석* 변형:
- `--sev-*-bg` = base 컬러 12% 알파 위에 ring 1px 동일 base.
- 색만으로 구분 금지 — 항상 라벨 텍스트 + 아이콘 동반.

### 2-4. 강조/액션

| 토큰 | 컬러 | 용도 |
| --- | --- | --- |
| `--accent` | `sky-500` | primary 버튼, 링크 |
| `--accent-bg` | `sky-500/10` | hover, 선택 상태 |
| `--success` | `emerald-500` | confirm 토스트 |
| `--warn` | `amber-500` | dismiss 가능 경고 |
| `--danger` | `rose-500` | 파괴적 액션 |

### 2-5. 차트 팔레트 (8색, 시계열용)
순서: `sky-400` → `emerald-400` → `amber-400` → `rose-400` → `violet-400` → `cyan-400` → `lime-400` → `pink-400`.
**룰 마커**는 별도 — 룰 ID별로 결정적 매핑(R001=rose, R002=amber, R003=sky, R004=violet, R005=zinc-300, R006=cyan).

---

## 3. 타이포그래피

| 역할 | 패밀리 | 사이즈 | 비고 |
| --- | --- | --- | --- |
| Display (헤더 제목) | sans (기본) | 28~32px / 700 | severity 라벨과 같은 라인 |
| H1 인시던트 ID | mono | 18px / 600, `tabular-nums` | `IR-20260508-0042` 가지런하게 |
| Body | sans | 14px / 400 | 라인하이트 1.5 |
| Body small (메타) | sans | 12px / 400 | secondary 텍스트 |
| Number callout (confidence) | mono | 36px / 700, `tabular-nums` | 0.82 같은 큰 숫자 |
| Code / log line | mono | 13px / 400 | 라인 그대로 보존 |

폰트 패밀리는 시스템 default + `ui-monospace`. 외부 폰트 로딩은 인쇄 일관성 위해 **하지 않음** (필요 시 self-host).

---

## 4. 스페이싱·레이아웃 그리드

### 4-1. 스페이싱 스케일 (Tailwind 호환)
`0 / 1(4px) / 2(8px) / 3(12px) / 4(16px) / 6(24px) / 8(32px) / 12(48px) / 16(64px)` — 그 외 값 사용 금지.

### 4-2. 페이지 그리드 (`/incident/[id]`)
- Max width **1280px**, 좌우 패딩 32px.
- 12 컬럼 그리드, 24px gutter.
- 패널 배치 (PM_ENHANCEMENT_PLAN.md §3-0-2 와이어와 일치):

```
row1: Header                   [12]
row2: Timeline                 [12]
row3: MatchedRules [7]  ConfidenceBreakdown [5]
row4: Causes [6]        Actions [6]
row5: RelatedLogs              [12]
```

768px 이하: 모든 패널 [12] 세로 스택. 가로 차트는 가로 스크롤로 폴백.

### 4-3. 카드 룰
- 패딩 24px (모바일 16px).
- 코너 8px (`rounded-lg`).
- 1px ring `--surface-divider`.
- 그림자 금지 (다크 모드). 라이트(인쇄) 모드에서만 `shadow-sm`.

---

## 5. 컴포넌트 룰

### 5-1. SeverityBadge
```
┌─────────────────┐
│ ⛔ HIGH          │   ← 아이콘 + 라벨 + (옵션) 신뢰도
│  82%            │
└─────────────────┘
```
- prop: `severity: "LOW"|"MEDIUM"|"HIGH"|"CRITICAL"`, `confidence?: number`
- 절대 `<span style={{color:'red'}}>` 같은 인라인 컬러 금지 — 토큰만.

### 5-2. ConfidencePill
- 36px 큰 숫자 + 막대 4개 (base/evidence/interaction/gpt 기여) 시각화.
- API의 `breakdown` 객체 (P1-0)를 직접 prop으로 받음.

### 5-3. RuleChip
- `R001 Timeout (+0.35)` 형식. 점수는 양수면 항상 `+`. 음수 없음.
- 클릭 → 해당 룰의 매칭된 로그 라인으로 스크롤 (앵커 동기화).

### 5-4. LogLine
- mono 폰트, 좌측 24px에 룰 매칭 라벨 영역 (룰 매칭 시 `R001` 컬러칩).
- 시간은 `HH:mm:ss` 만 표시 (날짜는 헤더에 단 1번).

### 5-5. ActionItem
- 체크박스 + 텍스트 + 출처 배지 (`rule` / `gpt` / `learned`).
- 체크 → 백엔드에 ack 저장 (P1-5 webhook 연동 가능 지점).

### 5-6. EmptyState
- "Waiting for logs from agent…" 같은 빈 상태는 회색 + 보조 일러스트 1개. 텍스트 톤 친근하게.

### 5-7. 토스트
- 우상단, 4초 자동 사라짐. 에러는 사용자가 닫을 때까지 유지.
- API 에러 메시지 그대로 표시 금지 → 사용자 친화 텍스트 + "자세히" 토글에 raw 표시.

---

## 6. 데이터 시각화

### 6-1. 차트 라이브러리 정책
- 단순 선/막대/도넛: **자체 SVG 컴포넌트** (의존성 0)
- 복잡한 차트(인시던트 타임라인 등): `recharts` 1개로 한정. d3 직접 의존 금지.

### 6-2. 타임라인
- 가로축: 인시던트 윈도우 (start~end)
- 트랙 1: level 밀도 (희미한 영역, ERROR=rose, WARN=amber)
- 트랙 2: 룰 매칭 마커 (해당 룰 ID 컬러 점)
- 트랙 3: source 변경 라인 (회색 가는 선)
- hover → tooltip (시간, 매칭 룰, 메시지 50자)

### 6-3. 점수 막대
- 4개 컴포넌트(base/evidence/interaction/gpt)를 누적막대로.
- 총합이 1.0을 넘는 경우(clamp) 막대 끝에 작은 ▶ 마크 + tooltip "clamped at 1.0".

### 6-4. 차트 인쇄 호환
- 색만으로 구분되는 차트는 **패턴**(점/사선) 도 함께 — 인쇄(흑백) 시 구분 보장.

---

## 7. 인쇄/PDF 모드

같은 컴포넌트로 PDF Export까지 처리하기 위해 `@media print` 를 일급 시민 취급.

```css
@media print {
  :root {
    --surface-base: white;
    --surface-card: white;
    --text-primary: #111;
    --text-secondary: #444;
  }
  @page { size: A4; margin: 16mm; }
  .no-print { display: none !important; }
  .page-break { break-before: page; }
}
```

### 인쇄 레이아웃
- 헤더 + 매칭 룰 + 신뢰도 분해 → **1페이지**
- 인과/액션 + 관련 로그 → **2페이지** (필요 시)
- 페이지 푸터: `Generated by Netscope-AI · {timestamp} · IR-{id}`

### 금지
- `position: fixed` 패널 (인쇄 시 잘림)
- 다크 배경 위 흰 텍스트만 사용 (인쇄 시 회색 박스)

---

## 8. 접근성 가드레일

| 항목 | 기준 |
| --- | --- |
| 색 대비 | WCAG AA: 일반 텍스트 4.5:1, 큰 텍스트 3:1 |
| 색만으로 의미 전달 금지 | severity는 항상 아이콘+텍스트 동반 |
| 키보드 네비 | 모든 인터랙션 요소 tab 접근 가능, focus ring 가시 |
| 스크린리더 | severity 배지에 `aria-label="severity high, confidence 82%"` |
| 모션 | `prefers-reduced-motion` 시 차트 애니메이션 비활성 |
| 폰트 사이즈 | 200% 확대해도 가로 스크롤 안 생기게 (반응형 회귀) |

---

## 9. 토큰 → 코드

### 9-1. CSS 변수 정의 (제안)
```css
/* frontend/src/app/globals.css */
:root {
  --surface-base: theme(colors.zinc.950);
  --surface-card: theme(colors.zinc.900);
  --surface-divider: theme(colors.zinc.800);
  --text-primary: theme(colors.zinc.100);
  --text-secondary: theme(colors.zinc.400);
  --sev-low: theme(colors.emerald.500);
  --sev-mid: theme(colors.amber.500);
  --sev-high: theme(colors.rose.500);
  --sev-crit: theme(colors.violet.600);
  --accent: theme(colors.sky.500);
}
```

### 9-2. severity 헬퍼 (`src/styles/severity.ts` 채우기)
```ts
export type Severity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export const severityToken = {
  LOW:      { fg: "var(--sev-low)",  icon: "check",          label: "Low" },
  MEDIUM:   { fg: "var(--sev-mid)",  icon: "alert-triangle", label: "Medium" },
  HIGH:     { fg: "var(--sev-high)", icon: "alert-octagon",  label: "High" },
  CRITICAL: { fg: "var(--sev-crit)", icon: "siren",          label: "Critical" },
} as const;
```
컴포넌트는 항상 이 헬퍼 경유. 인라인 컬러 PR은 리뷰에서 거절.

### 9-3. 룰 컬러 매핑
```ts
export const ruleColor: Record<string, string> = {
  R001: "var(--sev-high)",
  R002: "var(--sev-mid)",
  R003: "var(--accent)",
  R004: "var(--sev-crit)",
  R005: "var(--text-secondary)",
  R006: "theme(colors.cyan.400)",
};
```
사용자 정의 룰(`Cxxx`)은 ID 해시로 차트 팔레트에서 결정적으로 선택.

---

## 부록 — 컴포넌트 체크리스트 (PR 셀프리뷰)

- [ ] 인라인 `style={{color:...}}` 또는 `bg-[#...]` 같은 임시 컬러 없음
- [ ] severity 표시는 아이콘 + 텍스트 + 토큰 컬러 모두 사용
- [ ] 숫자 표시는 `tabular-nums` 또는 mono 폰트
- [ ] `@media print` 에서 깨지지 않음 (다크 배경 인쇄 회색 블록 금지)
- [ ] 키보드 tab 으로 도달 가능, focus ring 보임
- [ ] 모션은 `prefers-reduced-motion` 존중
- [ ] 모듈 단위 스크린샷이 단독으로 의미 전달 가능
