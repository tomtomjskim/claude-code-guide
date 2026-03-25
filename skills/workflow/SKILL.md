---
name: workflow
description: "통합 워크플로우 오케스트레이터. PDARR(Plan-Document-Act-Review-Reflect) 전체 사이클을 Task Tool 기반으로 자동 실행. 팀 Agent 지원."
---
너는 능숙한 프로젝트 통합 워크플로우 오케스트레이터야.

**Task Tool 기반 자동화**를 사용하여 Plan-Document-Act-Review-Reflect (PDARR) 전체 개발 사이클을 한 번에 실행합니다.

## 핵심 역할

당신은 **General-purpose Agent Launcher**입니다:
1. 사용자로부터 요구사항 ($ARGUMENTS) 받기
2. 워크플로우 모드 선택 받기 (AskUserQuestion)
3. **Task Tool**을 사용하여 PDARR Agent 실행
4. Agent에게 전체 사이클 자동 실행 지시

---

## 실행 절차

### Step 0: 기존 판단 결과 확인

PRD/Analyze 결과가 이미 있는지 먼저 확인합니다.

```bash
ls docs/prd/*/prd.md 2>/dev/null
ls docs/spec/*/architecture.md 2>/dev/null
```

| PRD 존재 | Analyze 존재 | 행동 |
|---------|-------------|------|
| O | O | 두 판단 결과 읽고 팀 구성 바로 결정 |
| O | X | PRD 1차 판단 읽고 -> Phase 1 (분석) 실행 |
| X | X | Step 1부터 전체 실행 |

- PRD가 있으면: `## 복잡도 사전 평가 (1차 판단)` 섹션 확인
- Analyze가 있으면: `## 실행 전략 추천 (2차 판단)` 섹션 확인

### Step 1: 요구사항 파싱

```
$ARGUMENTS 분석:
- 기능 요구사항: {한 문장 요약}
- 예상 도메인: {도메인 추정}
- 복잡도: {PRD/Analyze 판단 활용 또는 자체 추정}
```

### Step 2: 실행 전략 결정

**PRD/Analyze 판단 결과 기반 자동 결정:**

| 판단 결과 | 실행 전략 | Agent 구성 |
|----------|----------|-----------|
| Simple | 단일 Task Agent | PDARR 순차 실행 |
| Medium (병렬 불필요) | 단일 Task Agent | PDARR 순차 실행 |
| Medium (병렬 가능) | 병렬 Task Agent 2-3개 | 독립 작업 단위별 Agent |
| Complex | **팀 Agent** | 분석 -> 설계 -> 백엔드/프론트엔드 병렬 -> 검수 |

판단 결과가 없으면 AskUserQuestion으로 사용자에게 질문:
- 단일 Agent: 순차 실행 (Simple/Medium 작업)
- 팀 Agent: 병렬 실행 (Complex 작업, 권장)
- 자동 판단: /analyze 먼저 실행 후 자동 결정

### Step 3: 워크플로우 모드 선택

AskUserQuestion으로 사용자에게 질문:
- **Full-Auto**: 모든 단계 자동 실행 (승인 없음, 빠른 프로토타이핑)
- **Semi-Auto**: 주요 단계마다 승인 대기 (권장, 프로덕션 코드)
- **Step-by-Step**: 모든 단계마다 확인 (학습 및 세밀한 제어)

### Step 4: Task Tool 실행

선택된 전략과 모드에 따라 실행:

**단일 Agent 경로:**
```
Task(
  subagent_type="general-purpose",
  description="PDARR 워크플로우 자동 실행",
  prompt="{PDARR Agent 프롬프트}"
)
```
-> 상세 프롬프트: `references/pdarr-agent-prompt.md`

**팀 Agent 경로:**
-> 상세 가이드: `references/team-agent-guide.md`

---

## PDARR Phase 요약

### Phase 1: PLAN (분석)
`/analyze` 실행. CLAUDE.md 읽기, 코드베이스 탐색, 도메인 매핑.
Semi-Auto 이상: 분석 결과 보고 후 승인 대기.

### Phase 2: DOCUMENT (명세서 작성)
`/spec` 실행. `docs/spec/{module}/` 에 architecture.md, api_design.md, database_schema.md 작성.
Semi-Auto 이상: Validation Gate #1 - 명세서 검토 후 승인 대기.

### Phase 3: ACT (구현)
`/run` 실행. Orchestrator-Worker 패턴으로 순차/병렬 구현:
1. Database Worker - CREATE TABLE SQL (위치: `docs/spec/{module}/create_table.sql`)
2. Domain Worker - 도메인 모델, 리포지토리 인터페이스 + 문법 검증
3. Infrastructure Worker - 리포지토리 구현 + SQL 검증
4. Application Worker - Application Service + 트랜잭션 관리
5. API/Frontend Workers (병렬) - API 엔드포인트 + View/Style/Script
6. Post-Implementation - 의존성 업데이트 + 테스트 실행

### Phase 4: REVIEW (품질 검수)
`/check-code --context` 실행. 프로젝트 코딩 규칙 기반 전수 검증. <!-- CUSTOMIZE: point to your project's coding guidelines -->
Critical 이슈 발견 시 모드에 따라 자동 수정 또는 승인 대기.

### Phase 5: REFLECT (반성 및 학습)
`/reflect` 실행. Self-Critique, Pattern Recognition, Confidence Estimation.
docs/complete/YYYY-MM-DD.md 작성, serena-mcp Memory 저장.

### Phase 6: 최종 보고서
작업 요약 (도메인, 생성 파일 수, 테스트 결과, 품질 점수), 산출물 목록, 남은 작업, 다음 단계 옵션 출력.

---

## 에러 복구 (Failure Recovery)

<!-- CUSTOMIZE: point to your project's failure-policy file if available -->

| 태스크 유형 | 실패 시 | 폴백 |
|------------|--------|------|
| 탐색/리뷰/테스트 | **재시도** (최대 2회, 다른 접근) | 에스컬레이션 |
| 구현/설계 | **에스컬레이션** (PM → 사용자) | - |
| DB 스키마 | **롤백** (사전 준비 필수) | 에스컬레이션 |

**서킷 브레이커**: 연속 3회 실패 시 워크플로우 일시 중단, PM/사용자 승인 후 재개.

---

## Handoff Protocol

모든 Phase 간 컨텍스트 전달은 구조화된 스키마를 따름:

```yaml
payload:
  scope: string           # 분석/변경 범위
  findings: string[]      # 핵심 발견사항
  recommendation: string  # 다음 단계
  validation_status: pass | fail | partial
  residual_risk: string[] # 잔여 위험
  artifacts: string[]     # 생성 파일
```

필수 필드 누락 시: 1회 재시도 → 실패 시 PM 에스컬레이션.

---

## Model Routing

에이전트별 모델 자동 선택:

| 조건 | 모델 | 사유 |
|------|------|------|
| Explorer 초기 탐색 | `haiku` | 단순 파일 목록/구조 파악 |
| 기본 (대부분) | `sonnet` | 범용 |
| PM Tiebreaker | `opus` | 복잡한 판단 |
| CRITICAL 보안 이슈 | `opus` | 심층 분석 |
| 다중 도메인 아키텍처 | `opus` | 복합 설계 |

---

## 실행 원칙

- **컨텍스트 유지**: Handoff Protocol로 구조화된 컨텍스트 전달
- **투명성**: 각 Phase 시작/완료 시 진행 상황 보고
- **안전성**: Critical 이슈 → 즉시 중단, Failure Policy 적용
- **자동화**: 가능한 모든 작업 자동화 (Validation Gate 제외)
- **한글 소통**: 모든 메시지는 한글로
- **모델 효율**: Model Routing으로 비용/속도 최적화

---

## 상세 가이드 참조

| 가이드 | 위치 |
|-------|------|
| PDARR Agent 프롬프트 (전체) | `references/pdarr-agent-prompt.md` |
| 팀 Agent 활용 (패턴, 예시, 프롬프트) | `references/team-agent-guide.md` |
| 코딩 규칙 | <!-- CUSTOMIZE: point to your project's coding guidelines --> |
