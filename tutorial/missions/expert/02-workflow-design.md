# 미션 2: 워크플로우 커맨드 설계 — "나만의 파이프라인"

> 예상 소요: 15분 | 난이도: ★★★★★

## 목표
프로젝트에 맞는 커스텀 워크플로우 커맨드를 설계하고 등록한다.

## 배경

### 워크플로우 커맨드란?
Claude Code의 슬래시 커맨드(/)는 **자동화된 업무 절차**입니다.
`.claude/commands/` 폴더에 마크다운 파일로 정의합니다.

```
.claude/commands/
├── deploy-check.md      # /deploy-check → 배포 전 체크리스트
├── hotfix.md            # /hotfix → 긴급 수정 절차
└── onboard-feature.md   # /onboard-feature → 새 기능 온보딩
```

### 언제 만들까?
- 같은 패턴의 작업을 반복할 때
- 팀원마다 다르게 처리하는 작업을 표준화할 때
- 여러 단계를 하나의 명령으로 묶고 싶을 때

## 실습: /api-test 커맨드 만들기

### Step 1: 워크플로우 가이드 확인
```
.claude/workflow-commands-guide.md에서 커맨드 작성법을 요약해줘.
핵심만 5줄로.
```

### Step 2: 커맨드 설계
```
api-service 프로젝트용 /api-test 커맨드를 만들어줘.
.claude/commands/api-test.md 파일로.

이 커맨드가 실행되면:
1. api-service의 모든 엔드포인트를 파악
2. 각 엔드포인트에 curl 테스트 스크립트 생성
3. 테스트 실행 결과를 표로 정리
4. 실패한 테스트의 원인 분석

입력: $ARGUMENTS (특정 엔드포인트만 지정 가능)
예: /api-test users → users 관련 API만 테스트
```

### Step 3: 커맨드 테스트
```
/api-test
```
→ 만든 커맨드가 의도대로 동작하는지 확인

### Step 4: 복합 워크플로우 설계
```
api-service용 /api-release 커맨드를 만들어줘.
이 커맨드가 실행되면:
1. /check-code --thorough api-service 실행
2. /api-test 전체 실행
3. 결과 종합 리포트 작성
4. 통과 시 "배포 준비 완료" 표시, 실패 시 수정 필요 항목 목록
```

## 성공 기준
- [x] 커스텀 커맨드 파일(.claude/commands/*.md)을 작성
- [x] $ARGUMENTS를 활용한 동적 커맨드 이해
- [x] 여러 커맨드를 조합한 복합 워크플로우 설계

## 커맨드 작성 팁
- `$ARGUMENTS` — 사용자 입력을 받는 변수
- 단계를 명확하게 번호로 나눌 것
- 각 단계의 산출물을 명시할 것
- 실패 시 대응을 정의할 것 (예: "테스트 실패 시 원인 분석 후 수정 제안")

## 다음 미션
→ [미션 3: 팀 오케스트레이션](03-team-orchestration.md)
