# 미션 2: /dispatch로 시작하기 — "접수처에 업무 맡기기"

> 예상 소요: 5분 | 난이도: ★★★☆☆

## 목표
`/dispatch`가 작업 복잡도를 판단하고 최적 경로를 추천하는 과정을 체험한다.

## 배경

### /dispatch란?
회사에 "접수 데스크"가 있다고 생각하세요.
업무를 가져가면 복잡도를 판단해서 적절한 담당자에게 보내줍니다.

```
"프린터 토너 교체" → 직접 처리 (Trivial)
"보고서 오타 수정" → 담당자 1명 (Simple)
"신규 제품 기획"   → 팀 회의 필요 (Complex)
```

`/dispatch`도 마찬가지입니다:
```
/dispatch "버튼 색상 변경"    → Simple → /run 직행
/dispatch "검색 기능 추가"    → Medium → /analyze → /run
/dispatch "결제 시스템 구현"  → Complex → /prd → /analyze → /workflow
```

## 실습

### Step 1: 간단한 작업 dispatch
```
/dispatch "todo-app에서 완료된 항목 삭제 버튼 추가"
```
→ Simple~Medium 판정 예상. 어떤 경로를 추천하는지 확인.

### Step 2: 복잡한 작업 dispatch
```
/dispatch "todo-app에 카테고리 분류, 검색, 정렬, 날짜별 필터, 통계 대시보드 추가"
```
→ Complex 판정 예상. 팀 Agent나 단계적 접근을 추천하는지 확인.

### Step 3: 추천 경로 따라가기
Step 1에서 추천받은 경로대로 실제 실행해보세요.
(보통 `/run` 또는 `/analyze` → `/run`)

## 성공 기준
- [x] /dispatch가 복잡도를 판정하는 것을 확인
- [x] 작업 크기에 따라 다른 경로를 추천하는 것을 이해
- [x] 추천 경로 중 하나를 실행해봄

## 핵심 포인트

### 복잡도 판정 기준
| 수준 | 수정 파일 | 특성 | 추천 경로 |
|------|----------|------|----------|
| Trivial | 1개 | 한 줄 수정 | 직접 처리 |
| Simple | 1~2개 | 명확한 수정 | `/run` |
| Medium | 3~5개 | 분석 필요 | `/analyze` → `/run` |
| Complex | 6개+ | 설계 필요 | `/prd` → `/analyze` → `/workflow` |

### /dispatch를 안 쓰면?
안 써도 됩니다! 직접 `/run`이나 `/analyze`를 불러도 됩니다.
하지만 `/dispatch`를 쓰면 **과도하거나 부족한 처리를 방지**할 수 있습니다.

## 다음 미션
→ [미션 3: PDARR 워크플로우](03-pdarr-workflow.md)
