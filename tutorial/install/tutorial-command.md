# /tutorial — 인터랙티브 학습 가이드

> 이 파일을 프로젝트의 `.claude/commands/tutorial.md`에 복사하면 `/tutorial` 커맨드로 사용 가능합니다.
> ```bash
> mkdir -p .claude/commands
> cp tutorial/install/tutorial-command.md .claude/commands/tutorial.md
> ```

사용자의 수준을 파악하고 적절한 튜토리얼 경로로 안내하는 커맨드.

## 입력
$ARGUMENTS

## 실행 규칙

### 인자가 없는 경우 (`/tutorial`)
사용자에게 다음 3가지 질문을 하고, 답변을 기반으로 레벨을 판별한다:

**질문 1**: "터미널(명령 프롬프트)을 열어본 적 있나요?"
- 아니오 / 잘 모르겠어요 → 초보자 +0점
- 네 → +1점

**질문 2**: "Git을 사용해본 적 있나요? (직접 또는 AI 에이전트를 통해)"
- 아니오 / 이름만 들어봤어요 → +0점
- 기본적인 것은 해봤어요 (commit, push 등) → +1점
- 브랜치, PR, 리뷰까지 활용해요 → +2점

**질문 3**: "Claude Code나 AI 코딩 도구를 써본 적 있나요?"
- 처음이에요 → +0점
- 간단한 질문/수정 정도 해봤어요 → +1점
- 워크플로우, 커맨드, 에이전트까지 활용해요 → +2점

**레벨 판별**:
- 0~1점: **초보자** 코스
- 2~3점: **개발자** 코스
- 4~5점: **전문가** 코스

판별 후 해당 레벨의 코스 개요를 보여주고, 첫 번째 미션 내용을 안내한다.

---

### 인자가 "beginner"인 경우 (`/tutorial beginner`)
초보자 코스 전체 로드맵과 첫 번째 미션을 안내한다:

```
초보자 코스 (총 5개 미션, 약 15분)

 1. 첫 대화       — "이 파일이 뭐예요?" (2분)
 2. CSS 버그 수정  — "이거 왜 안 보여요?" (3분)
 3. 내용 바꿔보기  — "내 걸로 만들기" (3분)
 4. 새 파일 만들기 — "이런 페이지 만들어줘" (3분)
 5. Git 저장      — "작업 기록 남기기" (3분)

실습 폴더: tutorial/sandbox/hello-world/
```

`tutorial/missions/beginner/01-first-conversation.md` 파일을 읽고 내용을 요약하여 첫 미션을 시작하도록 안내한다.

---

### 인자가 "developer"인 경우 (`/tutorial developer`)
개발자 코스 전체 로드맵과 첫 번째 미션을 안내한다:

```
개발자 코스 (총 5개 미션, 약 35분)

 1. CLAUDE.md 설정    — "AI에게 업무 가이드 주기" (5분)
 2. /dispatch 라우팅  — "접수처에 업무 맡기기" (5분)
 3. PDARR 워크플로우  — "계획부터 완료까지" (10분)
 4. 프리셋 활용       — "업무 강도 조절하기" (5분)
 5. 멀티 에이전트     — "팀으로 일하기" (10분)

실습 폴더: tutorial/sandbox/todo-app/
```

`tutorial/missions/developer/01-claudemd-setup.md` 파일을 읽고 내용을 요약하여 첫 미션을 시작하도록 안내한다.

---

### 인자가 "expert"인 경우 (`/tutorial expert`)
전문가 코스 전체 로드맵과 첫 번째 미션을 안내한다:

```
전문가 코스 (총 3개 미션, 약 50분)

 1. 커스텀 에이전트     — "나만의 전문가 정의" (15분)
 2. 워크플로우 커맨드   — "나만의 파이프라인" (15분)
 3. 팀 오케스트레이션   — "AI 팀 운영하기" (20분)

실습 폴더: tutorial/sandbox/api-service/
```

`tutorial/missions/expert/01-custom-agent.md` 파일을 읽고 내용을 요약하여 첫 미션을 시작하도록 안내한다.

---

### 인자가 "next"인 경우 (`/tutorial next`)
현재 작업 디렉토리와 대화 맥락을 기반으로 다음 미션을 추천한다:
- 현재 `hello-world` 폴더 → 초보자 코스의 다음 미션
- 현재 `todo-app` 폴더 → 개발자 코스의 다음 미션
- 현재 `api-service` 폴더 → 전문가 코스의 다음 미션
- 판단 불가 시 → 레벨 판별 질문으로 돌아감

해당 미션 파일을 읽고 내용을 안내한다.

---

### 인자가 "status"인 경우 (`/tutorial status`)
전체 학습 경로를 보여주고, 현재 위치를 표시한다:

```
전체 학습 경로:

초보자 (15분)          개발자 (35분)          전문가 (50분)
├─ 01 첫 대화          ├─ 01 CLAUDE.md        ├─ 01 커스텀 에이전트
├─ 02 버그 수정        ├─ 02 /dispatch        ├─ 02 워크플로우 설계
├─ 03 내용 변경        ├─ 03 PDARR            └─ 03 팀 오케스트레이션
├─ 04 파일 생성        ├─ 04 프리셋
└─ 05 Git 저장         └─ 05 멀티 에이전트
```

---

### 인자가 "cheatsheet"인 경우 (`/tutorial cheatsheet`)
현재 수준에 맞는 치트시트를 보여준다.
수준 판단이 안 되면 3개 모두의 파일 경로를 안내한다:
- `tutorial/cheatsheets/beginner-cheatsheet.md`
- `tutorial/cheatsheets/developer-cheatsheet.md`
- `tutorial/cheatsheets/expert-cheatsheet.md`

---

### 인자가 "glossary"인 경우 (`/tutorial glossary`)
`tutorial/glossary.md` 파일을 읽고, 용어 사전을 보여준다.

---

## 응답 스타일
- 한국어로 응답
- 친근하고 격려하는 톤 ("잘하고 있어요!", "걱정 마세요")
- 전문 용어 사용 시 반드시 일상 비유를 함께 제공
- 각 미션 안내 시 "예상 소요 시간"과 "난이도"를 표시
