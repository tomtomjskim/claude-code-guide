# 미션 1: CLAUDE.md 설정 — "AI에게 업무 가이드 주기"

> 예상 소요: 5분 | 난이도: ★★☆☆☆

## 목표
CLAUDE.md가 무엇인지 이해하고, 프로젝트에 맞게 작성한다.

## 배경

### CLAUDE.md란?
새 팀원이 입사하면 "우리 팀 규칙 문서"를 줍니다.
**CLAUDE.md는 AI 팀원에게 주는 업무 가이드**입니다.

| 사람 | AI (Claude Code) |
|------|-----------------|
| 온보딩 문서 | CLAUDE.md |
| "우리는 이렇게 해" | 코딩 컨벤션, 프로젝트 구조 |
| "이건 하면 안 돼" | 금지 사항, 주의사항 |
| "모르면 여기 봐" | 참고 문서 경로 |

### 왜 중요한가요?
CLAUDE.md가 없으면 Claude는 매번 추측합니다.
CLAUDE.md가 있으면 **프로젝트를 이해하고 일관되게** 일합니다.

## 실습

### Step 1: 기존 CLAUDE.md 분석
```
tutorial/sandbox/todo-app/.claude/CLAUDE.md 파일을 읽고 각 섹션이 뭘 하는지 설명해줘
```

### Step 2: CLAUDE.md 개선 요청
```
todo-app의 CLAUDE.md를 더 상세하게 개선해줘:
- 새 기능 추가 시 따라야 할 패턴 (기존 addTodo 함수 패턴 참고)
- 금지사항: jQuery 사용 금지, 외부 CDN 금지
- 테스트 방법: 브라우저에서 직접 확인
```

### Step 3: 효과 체험
개선된 CLAUDE.md가 있는 상태에서:
```
todo-app에 "우선순위" 기능을 추가해줘. 높음/보통/낮음 3단계.
```
→ CLAUDE.md의 컨벤션을 따라 구현하는지 확인

## 성공 기준
- [x] CLAUDE.md 각 섹션의 역할을 이해했다
- [x] 프로젝트에 맞게 CLAUDE.md를 커스터마이징했다
- [x] CLAUDE.md가 실제 구현 품질에 영향을 미치는 것을 확인했다

## 핵심 포인트
- CLAUDE.md는 `.claude/` 폴더 안에 위치
- 프로젝트 루트의 CLAUDE.md → 전역 설정
- `.claude/CLAUDE.md` → 프로젝트별 설정
- **구체적일수록 좋다** — "코드를 잘 짜줘" (X) → "함수당 20줄 이내, JSDoc 필수" (O)

## 다음 미션
→ [미션 2: /dispatch로 시작하기](02-dispatch-routing.md)
