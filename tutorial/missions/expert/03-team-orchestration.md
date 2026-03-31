# 미션 3: 팀 오케스트레이션 — "AI 팀 운영하기"

> 예상 소요: 20분 | 난이도: ★★★★★

## 목표
대규모 기능을 여러 에이전트가 병렬로 처리하는 팀 오케스트레이션을 설계하고 실행한다.

## 배경

### 팀 오케스트레이션이란?
오케스트라 지휘자처럼, 여러 AI 에이전트를 조율해서
**하나의 큰 프로젝트를 병렬로 진행**하는 것입니다.

```
지휘자 (PM)
  ├─ 바이올린 (Frontend Dev) ─── 동시 연주
  ├─ 첼로 (Backend Dev)     ─── 동시 연주
  ├─ 타악기 (DBA)           ─── 동시 연주
  └─ 평론가 (Reviewer)      ─── 연주 후 평가
```

### 실행 전략 3가지
| 전략 | 파일 규모 | 방법 |
|------|----------|------|
| A: 단일 Agent | 1~3개 | 커맨드만 사용 |
| B: 병렬 Task | 4~6개 | Task()로 독립 작업 분배 |
| C: 팀 Agent | 7개+ | TeamCreate + Task + SendMessage |

## 실습: api-service 대규모 확장

### Step 1: 요구사항 정의
```
/prd api-service를 다음과 같이 확장하고 싶어:
1. 인증 시스템 (JWT 로그인/회원가입)
2. 게시판 CRUD API (/api/posts)
3. 댓글 CRUD API (/api/posts/:id/comments)
4. 입력 검증 미들웨어
5. 에러 핸들링 표준화
6. 기본 테스트 코드
```

### Step 2: 팀 분석
```
/analyze --team 위 PRD 기반으로 팀 구성과 작업 분배를 제안해줘
```

→ 확인할 것:
- 어떤 에이전트를 추천하는가?
- 어떤 작업을 병렬로 할 수 있는가?
- 작업 간 의존성은?

### Step 3: 워크플로우 실행
```
/workflow
```

→ 팀 에이전트가 병렬로 작업 시작. 관찰할 것:
- 에이전트 간 핸드오프 (분석 결과 → 구현)
- 병렬 실행 (Backend + 인증이 동시에?)
- 실패 복구 (에러 발생 시 어떻게 처리?)

### Step 4: 팀 리뷰
```
/check-code --team api-service
```

→ 전문 리뷰어 4명 이상이 다관점 검수:
- Security Sentinel: 인증 구현 보안
- API Arbiter: API 설계 일관성
- Code Reviewer: 코드 품질
- Performance Prophet: 성능 병목

## 성공 기준
- [x] PRD → 분석 → 팀 워크플로우 → 검수 전체 사이클 실행
- [x] 에이전트 간 핸드오프 과정 관찰
- [x] 팀 리뷰 결과에서 다관점 피드백 확인

## 핵심 개념

### Handoff Protocol
에이전트 A가 에이전트 B에게 작업을 넘길 때의 구조:
```
scope             — 작업 범위
findings          — 발견한 것
recommendation    — 추천 사항
validation_status — 검증 상태
residual_risk     — 남은 위험
```

### Failure Recovery
| 에이전트 유형 | 실패 시 |
|-------------|--------|
| Explorer/Reviewer | 자동 재시도 (최대 3회) |
| Developer | PM에게 에스컬레이션 |
| 3회 연속 실패 | 자동 중단 → 사용자 판단 |

### Model Routing
```
탐색 (Explorer) → haiku (빠르고 저렴)
구현 (Developer) → sonnet (기본)
보안/아키텍처 → opus (정확)
```

## 전문가 코스 완료!

### 전체 학습 경로 정리

```
초보자 (30분)
  ├─ 파일 읽기/수정/생성
  ├─ 자연어로 작업 요청
  └─ Git 기초

개발자 (45분)
  ├─ CLAUDE.md 설정
  ├─ /dispatch 라우팅
  ├─ PDARR 워크플로우
  ├─ 프리셋 시스템
  └─ 멀티 에이전트

전문가 (50분)
  ├─ 커스텀 에이전트 설계
  ├─ 워크플로우 커맨드 설계
  └─ 팀 오케스트레이션
```

### 더 깊이 배우려면
- [v3.0 아키텍처](../../../docs/12-v3-architecture.md) — 시스템 전체 구조
- [핸드오프 & 실패 복구](../../../docs/13-handoff-and-failure.md) — 상세 설정
- [프리셋 시스템](../../../docs/14-preset-system.md) — 깊이/실행 2축 완전 가이드
- [에이전트 페르소나](../../../docs/05-agent-personas.md) — 16개 에이전트 상세
