# 커맨드 및 스킬 가이드

## 개요

Claude Code의 슬래시 커맨드와 커스텀 스킬을 활용하여
반복 작업을 자동화하고 일관된 워크플로우를 구축합니다.

---

## 1. 기본 슬래시 커맨드

### 내장 커맨드
| 커맨드 | 설명 | 사용 예시 |
|--------|------|----------|
| `/help` | 도움말 | `/help` |
| `/clear` | 대화 초기화 | `/clear` |
| `/compact` | 컨텍스트 압축 | `/compact` |
| `/cost` | 토큰 사용량 확인 | `/cost` |
| `/doctor` | 상태 진단 | `/doctor` |

---

## 2. 웹 개발 권장 커맨드

### 프로젝트 관리
```markdown
/init-project
프로젝트 초기화 및 기본 구조 생성

/status
현재 프로젝트 상태 및 진행중 태스크 확인
```

### 개발 파이프라인
```markdown
/analyze [요구사항]
요구사항 분석 및 체크리스트 생성

/design [기능명]
설계 모드 진입 - 아키텍처/API/UI 설계

/implement [태스크]
구현 모드 - 코드 작성

/review [대상]
코드/설계 검수

/document [대상]
문서화 작업
```

### 세션 관리
```markdown
/session-start
새 작업 세션 시작 - 히스토리 파일 생성

/session-end
세션 종료 - 작업 내용 저장

/session-summary
현재 세션 요약
```

---

## 3. 커스텀 스킬 구조

### 스킬 디렉토리
```
~/.claude/skills/           # 글로벌 스킬
프로젝트/.claude/skills/    # 프로젝트별 스킬
```

### 스킬 파일 구조
```yaml
# ~/.claude/skills/analyze-requirements.yaml
name: analyze-requirements
description: 요구사항 분석 및 체크리스트 생성
trigger: /analyze

prompt: |
  ## 요구사항 분석 프로세스

  다음 단계로 요구사항을 분석해주세요:

  ### 1. 요구사항 이해
  - 핵심 기능 식별
  - 사용자 스토리 도출
  - 비기능 요구사항 파악

  ### 2. 기술적 분석
  - 기존 코드베이스 영향도
  - 필요한 API/모듈
  - 의존성 확인

  ### 3. 체크리스트 생성
  다음 질문에 답변해주세요:

  **기능 요구사항**
  - [ ] 핵심 기능은 무엇인가?
  - [ ] 예외 케이스는?
  - [ ] 사용자 플로우는?

  **기술 요구사항**
  - [ ] 어떤 기술 스택을 사용하는가?
  - [ ] 기존 코드 수정이 필요한가?
  - [ ] 새로운 의존성이 필요한가?

  **품질 요구사항**
  - [ ] 테스트 범위는?
  - [ ] 성능 기준은?
  - [ ] 보안 고려사항은?

  ### 4. 산출물
  `docs/requires/REQ-XXX-[기능명].md` 파일 생성
```

---

## 4. 권장 스킬 세트

### 4.1 요구사항 분석 스킬
```yaml
name: analyze
trigger: /analyze
prompt: |
  요구사항을 분석합니다.

  ## 분석 프로세스
  1. 요구사항 명확화 질문
  2. 기존 코드 영향도 분석 (Serena 사용)
  3. 체크리스트 생성
  4. docs/requires/ 문서 생성

  ## 필수 질문 체크리스트
  - 핵심 기능 정의가 명확한가?
  - 입력/출력이 정의되었는가?
  - 예외 케이스가 정의되었는가?
  - 성공 기준이 명확한가?
  - 기존 기능과의 관계가 명확한가?
```

### 4.2 설계 스킬
```yaml
name: design
trigger: /design
prompt: |
  설계 모드를 시작합니다.

  ## 설계 프로세스
  1. 아키텍처 설계
  2. API 설계 (필요시)
  3. UI/UX 설계 (필요시)
  4. 데이터 모델 설계 (필요시)

  ## 산출물
  - docs/spec/architecture/[기능명].md
  - docs/spec/api/[기능명].md
  - docs/spec/ui/[기능명].md

  ## 설계 체크리스트
  - [ ] 컴포넌트 구조가 명확한가?
  - [ ] 데이터 흐름이 정의되었는가?
  - [ ] 인터페이스가 정의되었는가?
  - [ ] 에러 핸들링이 고려되었는가?

  ## 주의사항
  - 예시 코드 최소화
  - 다이어그램으로 설명 (mermaid 활용)
  - 구체적인 타입/인터페이스 정의
```

### 4.3 구현 스킬
```yaml
name: implement
trigger: /implement
prompt: |
  구현 모드를 시작합니다.

  ## 구현 전 확인
  1. 설계 문서 확인 (docs/spec/)
  2. 기존 코드 분석 (Serena)
  3. 의존성 확인

  ## 구현 규칙
  - 설계 문서를 정확히 따름
  - 타입 안전성 유지
  - 에러 핸들링 포함
  - 테스트 코드 작성

  ## 예시 코드 규칙
  - 핵심 로직만 예시로 제공
  - 보일러플레이트 최소화
  - 실제 구현에 집중

  ## 산출물
  - 구현 코드
  - 테스트 코드
  - docs/tasks/ 태스크 업데이트
```

### 4.4 검수 스킬
```yaml
name: review
trigger: /review
prompt: |
  검수 모드를 시작합니다.

  ## 검수 체크리스트

  ### 코드 품질
  - [ ] 타입 안전성
  - [ ] 에러 핸들링
  - [ ] 코드 중복 없음
  - [ ] 네이밍 컨벤션

  ### 기능 검증
  - [ ] 요구사항 충족
  - [ ] 예외 케이스 처리
  - [ ] 성능 기준 충족

  ### 테스트
  - [ ] 단위 테스트 존재
  - [ ] 테스트 커버리지
  - [ ] 엣지 케이스 테스트

  ### 문서화
  - [ ] 코드 주석 적절
  - [ ] API 문서화
  - [ ] 변경 사항 기록
```

### 4.5 문서화 스킬
```yaml
name: document
trigger: /document
prompt: |
  문서화 모드를 시작합니다.

  ## 문서화 대상
  1. 완료된 기능 → docs/complete/
  2. API 문서
  3. 사용자 가이드

  ## 문서 구조
  ```
  # [기능명]

  ## 개요
  [기능 설명]

  ## 사용법
  [사용 방법]

  ## API (해당시)
  [API 명세]

  ## 참고
  - 관련 문서 링크
  - 관련 코드 위치
  ```

  ## 문서화 규칙
  - 예시 코드 최소화
  - 실제 동작하는 예시만 포함
  - 스크린샷보다 텍스트 설명 우선
```

### 4.6 세션 관리 스킬
```yaml
name: session-start
trigger: /session-start
prompt: |
  새 작업 세션을 시작합니다.

  ## 세션 시작 프로세스
  1. 이전 세션 히스토리 확인 (docs/history/)
  2. 진행중 태스크 확인 (docs/tasks/)
  3. TODO 목록 확인 (docs/todo/)
  4. 새 세션 히스토리 파일 생성

  ## 히스토리 파일 생성
  `docs/history/YYYY-MM-DD-session-N.md`

  ```markdown
  # 세션 히스토리: YYYY-MM-DD #N

  ## 목표


  ## 진행 사항


  ## 완료


  ## TODO


  ## 메모

  ```
```

---

## 5. CLAUDE.md에 스킬 통합

```markdown
# CLAUDE.md

## 커스텀 커맨드

### /analyze [요구사항]
요구사항 분석 모드. 체크리스트 기반으로 질문하고 docs/requires/에 문서 생성.

### /design [기능명]
설계 모드. 아키텍처/API/UI 설계 후 docs/spec/에 문서 생성.

### /implement [태스크]
구현 모드. 설계 문서 기반으로 코드 작성.

### /review [대상]
검수 모드. 체크리스트 기반 코드 리뷰.

### /session-start
세션 시작. 히스토리 파일 생성하고 이전 작업 확인.

### /session-end
세션 종료. 작업 내용 저장하고 TODO 정리.
```

---

## 6. 스킬 활용 예시

### 새 기능 개발 흐름
```
1. /session-start
   → 이전 세션 확인, 새 히스토리 파일 생성

2. /analyze "로그인 기능 구현"
   → 체크리스트 기반 질문
   → docs/requires/REQ-001-login.md 생성

3. /design login
   → 아키텍처 설계
   → docs/spec/architecture/login.md 생성

4. /implement login
   → 설계 기반 구현
   → 코드 작성

5. /review login
   → 체크리스트 기반 검수

6. /document login
   → docs/complete/DONE-001-login.md 생성

7. /session-end
   → 히스토리 저장, TODO 정리
```

---

## 다음 단계

- [개발 파이프라인](03-development-pipeline.md)
- [문서화 규칙](04-documentation-rules.md)
