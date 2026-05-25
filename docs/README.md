# Netscope-AI 문서 인덱스

> 프로젝트 컨텍스트(CLAUDE.md) 외 모든 상세 문서의 진입점.

## 📂 문서 목록

| 문서 | 대상 | 한 줄 요약 |
| --- | --- | --- |
| [`../CLAUDE.md`](../CLAUDE.md) | 모두 | 프로젝트 전체 개요 · 디렉터리 매핑 · 갭 · 컨벤션 |
| [`PM_ENHANCEMENT_PLAN.md`](./PM_ENHANCEMENT_PLAN.md) | **PM/기획** | 고도화 로드맵 P0~P3, 갭 인벤토리, 보고서 대시보드 명세 |
| [`API_REFERENCE.md`](./API_REFERENCE.md) | FE/BE 통합 | 엔드포인트 스펙, DTO 카탈로그, P1-0 응답 확장 |
| [`RULE_ENGINE.md`](./RULE_ENGINE.md) | BE/도메인 | R001~R006 정본, 스코어링 공식, 룰 추가 가이드 |
| ⭐ [`RULE_LEARNING.md`](./RULE_LEARNING.md) | BE/도메인/PM | **사용자 로그 패턴 학습** — 마이닝→라벨→룰 승격 (차별점 ③) |
| [`DESIGN_SYSTEM.md`](./DESIGN_SYSTEM.md) | FE/디자인 | 컬러 토큰, 타이포, 컴포넌트 룰, 인쇄 모드 |
| [`DEVELOPMENT.md`](./DEVELOPMENT.md) | 신규 합류자 | 5분 셋업, 컨벤션, 테스트, Git/PR 정책 |

## 🚦 빠른 진입

- **PM 회의 자료** → `PM_ENHANCEMENT_PLAN.md`
- **새로 합류한 개발자** → `../CLAUDE.md` → `DEVELOPMENT.md` → `RULE_ENGINE.md`
- **프론트만 작업** → `DESIGN_SYSTEM.md` + `API_REFERENCE.md`
- **룰 / 학습 도메인** → `RULE_ENGINE.md` → `RULE_LEARNING.md`
- **외부 통합/SDK** → `API_REFERENCE.md`

## 📌 세 차별점

1. **설명 가능한 AI** — 응답에 항상 `matched_rules` (룰 ID + 점수 + 근거). 정본: `RULE_ENGINE.md`
2. **보고서급 대시보드** — 회고/데모에 그대로 쓰이는 UI. 정본: `PM_ENHANCEMENT_PLAN.md` §3-0 + `DESIGN_SYSTEM.md`
3. **사용자 환경에 함께 자라는 룰셋** — 패턴 학습으로 도입 첫 주에 환경 맞춤 룰 자동 생성. 정본: `RULE_LEARNING.md`
