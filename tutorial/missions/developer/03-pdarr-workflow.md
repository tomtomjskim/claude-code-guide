# 미션 3: PDARR 워크플로우 — "계획부터 완료까지"

> 예상 소요: 10분 | 난이도: ★★★☆☆

## 목표
PDARR 전체 사이클을 처음부터 끝까지 한 번 돌려본다.

## 배경

### PDARR이란?
프로젝트 관리의 기본 사이클입니다:

```
Plan     → 무엇을, 왜 하는지 정리
Document → 어떻게 할지 설계
Act      → 실제 구현
Review   → 잘 만들었는지 검수
Reflect  → 배운 점 정리
```

| 단계 | 회사에서 | Claude Code에서 |
|------|---------|----------------|
| Plan | 기획 회의 | `/prd`, `/analyze` |
| Document | 설계 문서 | `/spec` |
| Act | 개발 | `/run` |
| Review | 코드 리뷰 | `/check-code` |
| Reflect | 회고 | `/reflect`, `/complete` |

## 실습: todo-app에 "마감일" 기능 추가

### Step 1: Plan — 분석
```
/analyze todo-app에 마감일(due date) 기능을 추가하려고 해.
각 할 일에 마감일을 설정하고, 지난 마감일은 빨간색으로 표시.
```
→ 어떤 파일을 수정해야 하는지, 복잡도가 어느 정도인지 분석 결과를 확인

### Step 2: Document — 설계
```
/spec
```
→ 분석 결과를 기반으로 기술 명세 작성. 어떤 함수를 추가/수정할지 확인

### Step 3: Act — 구현
```
/run
```
→ spec을 기반으로 구현 시작. 완료될 때까지 대기

### Step 4: Review — 검수
```
/check-code todo-app
```
→ 구현된 코드 품질 검사. 문제가 있으면 수정 제안

### Step 5: 결과 확인
```bash
open tutorial/sandbox/todo-app/index.html
```
→ 마감일 기능이 추가되었는지 직접 확인

## 성공 기준
- [x] 분석(/analyze) → 설계(/spec) → 구현(/run) → 검수(/check-code) 순서 실행
- [x] 각 단계의 산출물(분석 리포트, spec, 코드, 검수 결과)을 확인
- [x] 마감일 기능이 실제로 동작

## 핵심 포인트
- **모든 작업에 전체 사이클이 필요한 건 아님** — 간단한 작업은 `/run`만으로 충분
- 분석과 설계에 투자하면 **구현 품질이 올라감**
- 검수(/check-code)는 사람 대신 **AI 코드 리뷰어** 역할

## 다음 미션
→ [미션 4: 프리셋 활용](04-presets.md)
