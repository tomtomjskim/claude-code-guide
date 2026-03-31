# 전문가 치트시트

> 에이전트 설계, 팀 오케스트레이션, 고급 패턴 빠른 참조

---

## 5-Section 에이전트 템플릿

```markdown
## Opening (역할 정의)
"당신은 {프로젝트}의 {역할} 전문가입니다."

## Working Mode (작업 방식)
1. 먼저 ~ 파악
2. 그다음 ~ 분석
3. 마지막으로 ~ 생성

## Focus On (집중 포인트)
- 특히 ~ 에 주의
- ~ 패턴을 우선 확인

## Quality Checks (완료 전 체크)
- [ ] ~ 확인했는가?
- [ ] ~ 누락은 없는가?

## Return / Boundary (산출물 + 범위)
산출물: ~
범위 제한: ~ 는 하지 않음
```

## 팀 구성 패턴

| 유형 | 구성 | 사용 시점 |
|------|------|----------|
| Type A | PM + Dev | 단순 기능 추가 |
| Type B | PM + Explorer + Dev | 기존 코드 수정 |
| Type C | PM + Architect + Dev×2 + QA | 신규 모듈 |
| Type D | PM + Architect + Dev×3 + DBA + QA | 대규모 |
| Type E | Reviewer×4 + Tiebreaker | 코드 리뷰 전용 |

## Handoff Protocol 필드

```yaml
scope: 작업 범위
findings: 발견 사항
recommendation: 추천 사항
validation_status: pass | fail | partial
residual_risk: 남은 위험
```

## Failure Recovery 정책

| 에이전트 | 실패 시 |
|---------|--------|
| Explorer, Reviewer | 자동 재시도 (3회) |
| Developer | PM 에스컬레이션 |
| Architect | 사용자 개입 요청 |
| 3회 연속 실패 | circuit-breaker → 자동 중단 |

## Model Routing

```
haiku  ← 탐색, 단순 분류
sonnet ← 구현, 리뷰 (기본)
opus   ← 보안 이슈, 복잡 아키텍처, CRITICAL
```

## 커스텀 커맨드 작성법

```
위치: .claude/commands/{name}.md
변수: $ARGUMENTS — 사용자 입력
호출: /{name} {arguments}
```

핵심 구조:
```markdown
# 커맨드 이름

## 입력
$ARGUMENTS: 설명

## 실행 단계
1. ...
2. ...

## 산출물
- 결과 형식

## 실패 시
- 대응 방법
```

## Tiebreaker Protocol (리뷰 충돌 시)

```
1단계: 투표 (과반수)
2단계: 기준 적용 (보안 > 성능 > 유지보수 > 스타일)
3단계: PM 에스컬레이션
4단계: 사용자 최종 판단
```

## 핵심 파일 경로

| 파일 | 역할 |
|------|------|
| `templates/prompts/TEMPLATE.md` | 에이전트 템플릿 |
| `templates/prompts/*.md` | 16개 에이전트 프롬프트 |
| `.claude/commands/*.md` | 커스텀 커맨드 |
| `.claude/CLAUDE.md` | 프로젝트 설정 |
| `docs/12-v3-architecture.md` | 시스템 아키텍처 |
