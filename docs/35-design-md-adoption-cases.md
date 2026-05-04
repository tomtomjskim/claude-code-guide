# DESIGN.md 도입 평가 케이스

> 운영 모델: [`34-design-md-operating-model.md`](34-design-md-operating-model.md)
> 본 문서는 downstream 프로젝트가 도입 여부를 판단할 때 쓰는 평가 프레임이다.

## 1. 도입 비권장 시그널

다음 중 **2개 이상** 해당하면 전면 도입 ROI가 낮다. 운영 요소만 부분 차용을 검토.

| 시그널 | 의미 | 판별 |
|---|---|---|
| 이미 SSOT 문서가 명시되어 있음 | "이 문서는 모든 토큰의 정본(SSOT)" 류 선언이 기존에 존재 | 기존 design system 문서 첫 부분 확인 |
| 영역별 테마 방향 반전 | 영역 A는 `:root` dark-first + `body.light` 오버라이드 / 영역 B는 light-first + `body.dark` 오버라이드 공존 | `:root`와 `body.light`/`body.dark` 선언 비교 |
| 동일 변수명이 영역별 다른 값 | `--main-color` 같은 토큰이 영역에 따라 다른 hex로 정의 | 변수명 grep + 정의 위치별 값 비교 |
| 영역 전용 semantic 팔레트 격리 | `--Primary-*`, `--Neutrals-*` 같은 다단계 팔레트가 한 영역에만 선언 | 영역별 SCSS source 비교 |
| 빌드 체인이 React/Tailwind 아님 | PHP SSR + SCSS @import 또는 유사 전통 스택 | `package.json` 의존성 확인 |
| 큰 구조 마이그레이션 진행 중 | DDD 전환, 모놀리스 분해 등 동시 진행 | 마이그레이션 status 문서 또는 추적 이슈 확인 |

## 2. 부분 도입 권장 요소 (위 시그널 충족 프로젝트용)

전면 도입 대신 운영 모델의 다음 두 요소만 기존 design system 문서에 흡수한다. 토큰/YAML/lint는 제외.

| 차용 요소 | 출처 | 흡수 위치 (예시) |
|---|---|---|
| Agent Prompt Guide 섹션 (UI 작업 시 agent 판단 순서) | [`34-design-md-operating-model.md`](34-design-md-operating-model.md) §4.1 | 기존 cheatsheet/overview에 신규 섹션 |
| 변경 기록 양식 (`변경 유형 / 변경 토큰 / 영향 컴포넌트 / 검증 / 남은 리스크`) | [`34-design-md-operating-model.md`](34-design-md-operating-model.md) §6 | 기존 토큰 확장 절차에 부착 |

## 3. 케이스 1 — PHP+SCSS+다영역 e-commerce (도입 거부)

| 항목 | 내용 |
|---|---|
| 스택 | PHP SSR + SCSS @import + jQuery / DDD 마이그레이션 진행 |
| 영역 | B2C(Customer) + B2B(Seller) + Admin 3분리 |
| 기존 자산 | 영역별 design system 문서 ~4,000줄 (overview / cheatsheet / 영역별 가이드 / 컴포넌트 카탈로그 / 토큰 SSOT / UX 가이드라인) |
| 토큰 정의 | CSS custom property 단일 SSOT, 영역별 light/dark 반전, 영역 전용 semantic 팔레트 30+ |

### 평가 결과

**전면 도입 거부 / 부분 도입(§2 두 요소만) 조건부 승인**

근거:
- 기존 SSOT 문서와 실제 CSS 일치율 검증 시 100%. 추가 SSOT는 3중 sync 부담만 증가.
- 영역별 테마 반전과 동일 변수명 다른 값은 단일 YAML `colors.background: "#hex"` 형식으로 표현 불가.
- 영역 전용 semantic 팔레트는 영역별 분리 시에도 비대칭이라 표준 형식 매핑 불가.
- 마이그레이션 진행 중 문서 형식 교체는 즉시 UI 품질을 올리지 않으면서 agent 컨텍스트 부담만 증가.

### 부분 도입 변경 규모

운영 요소 2가지 흡수 → 기존 2개 파일에 ~40줄 추가. 신규 파일/토큰 변경 없음.

## 4. 권장 도입 시그널 (참고)

다음 패턴이면 전면 도입이 자연스럽다:

- React + Tailwind 또는 동등 빌드 체인 (YAML → theme export 직접 지원)
- 영역 분리 없는 단일 UI 또는 토큰 구조가 영역 간 대칭
- 기존 design system 문서가 없거나 토큰 SSOT 부재
- 다크모드가 단일 토큰 모드 전환 (`prefers-color-scheme` 또는 단일 클래스 토글)
- agent 발견성 낮은 위치(`.claude/` 깊은 경로 등)에 design 문서가 분산되어 루트 단일화 가치가 큰 상태

## 5. 평가 절차 (downstream 권장)

1. 위 §1 시그널 체크 → 2개 이상이면 §2 부분 도입 평가로 진입, 미만이면 운영 모델 §4 신규 프로젝트 워크플로우 적용
2. 기존 토큰 SSOT 일치율 샘플 검증 (8~10개 변수 spot-check)
3. agent 발견 경로 검토 — 루트 `DESIGN.md` 신설 가치가 기존 발견 경로 대비 높은지
4. 결정 기록 (도입/부분/거부와 근거)을 프로젝트 메타 문서로 보존

## 부록 — 운영 모델 본문

전면 도입 시 표준은 [`34-design-md-operating-model.md`](34-design-md-operating-model.md) §3(표준 구조), §4(주입 워크플로우), §6(버전 관리), §8(완료 체크) 참조.
