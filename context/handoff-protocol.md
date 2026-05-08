# Handoff Protocol v2.0

에이전트 간 컨텍스트 전달을 위한 표준 프로토콜.
모든 에이전트는 Return 구조에 따라 결과를 반환하고, PM이 핸드오프를 중재합니다.

> v2.0 변경 (2026-03-25): completion_status 4상태, retry 계층 분리, 파일 상태 체인, 세션 재개 지원
> v1.0 → v2.0 마이그레이션: validation_status deprecated (v3.0 제거 예정)

## Context Source Hygiene

핸드오프는 에이전트 간 전달 계약이지 자동 backlog 승격 장치가 아닙니다.

- handoff, backlog, roadmap, gap-review, brainstorm, retrospective 문서는 사용자가 명시적으로 요청했거나 현재 구현에 특정 spec이 필요할 때만 active context로 사용합니다.
- 해당 문서를 참조할 때는 먼저 참조 이유와 범위를 밝힙니다.
- 결과 보고에서는 `현재 사용자 요청`, `문서상 backlog`, `배포/검증 전용 항목`을 분리합니다.
- 문서상 backlog를 사용자 확인 없이 다음 작업 큐로 승격하지 않습니다.
- 기본 next-step 브리핑은 최신 사용자 지시와 실제 커밋/diff/worktree 상태를 기준으로 합니다.

## Handoff Schema

```yaml
handoff:
  # ── 메타 ──
  protocol_version: "2.0"
  from_agent: string        # 전달하는 에이전트 ID
  to_agent: string          # 수신하는 에이전트 ID
  task_id: string           # 태스크 식별자
  timestamp: iso8601        # 핸드오프 시각

  # ── 완료 상태 (v2.0: 4상태) ──
  completion_status: enum   # DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
  completion_detail: string # 상태 판정 근거 (한 문장)

  payload:
    scope: string           # Return.scope에서 가져옴
    findings: string[]      # Return.findings에서 가져옴
    recommendation: string  # Return.recommendation에서 가져옴
    validation_status: string  # [deprecated] pass | fail | partial — v2.0 하위 호환용
    residual_risk: string[] # 잔여 위험 목록
    artifacts: string[]     # 생성된 파일 경로 목록

  # ── 재시도 계층 (v2.0: 2레이어 분리) ──
  handoff_retry:
    retry_count: int        # 현재 재시도 횟수 (0부터)
    max_retries: 1          # 핸드오프 레벨 한도
    retry_reason: string    # 재시도 사유
  # 에이전트 내부 재시도: failure-policy.yaml max_attempts(2)
  # 서킷 브레이커: agents.yaml consecutive_failures(3)

  # ── 파일 상태 체인 (v2.0 신규) ──
  file_state:
    session_dir: string     # ~/.claude/team/context/sessions/{date}_{task_id}/
    status: enum            # running | completed | failed | abandoned
    ttl_rules:
      completed: 90         # 일
      failed: 14
      abandoned: 1
      running: 7            # 7일 초과 시 abandoned 전환

  # ── 세션 재개 (v2.0 신규) ──
  session_resume:
    enabled: boolean
    last_completed_phase: string
    resume_from_phase: string

  validation:
    required_fields: [scope, findings, recommendation, completion_status]
    completeness_check: true
    on_validation_fail: retry_once | escalate_to_pm
```

## Completion Status Rules (v2.0)

| 상태 | 의미 | 다음 단계 | PM 행동 |
|------|------|----------|---------|
| DONE | 완전 완료, 잔여 위험 없음 | 진행 | 다음 에이전트 스폰 |
| DONE_WITH_CONCERNS | 완료, 우려사항 존재 (LOW/MEDIUM) | 진행 가능 | concerns를 다음 에이전트에 전달 |
| BLOCKED | 외부 의존성으로 진행 불가 | 차단 | unblock 조치 후 재개 |
| NEEDS_CONTEXT | 정보 부족으로 판단 보류 | 차단 | PM이 추가 정보 수집 후 재스폰 |

### 판정 기준
- "산출물이 존재하는가?" → YES → DONE 계열, NO → BLOCKED 또는 NEEDS_CONTEXT
- "에이전트 통제권 외부 원인인가?" → YES → BLOCKED, NO → NEEDS_CONTEXT
- "concerns가 HIGH 이상인가?" → YES → BLOCKED, NO → DONE_WITH_CONCERNS

### 재시도 계층 분리

| 계층 | 한도 | 관리 주체 | 설명 |
|------|------|----------|------|
| 에이전트 내부 | max_attempts: 2 | failure-policy.yaml | 멱등 태스크 내부 재시도 |
| 핸드오프 레벨 | max_retries: 1 | handoff-protocol | 다른 접근법으로 재스폰 |
| 서킷 브레이커 | consecutive_failures: 3 | agents.yaml | 워크플로우 전체 중단 |

### v1.0 → v2.0 마이그레이션
- `validation_status` 필드는 deprecated: v2.0에서 하위 호환용 유지, v3.0에서 제거
- 상태 매핑: pass→DONE, partial→DONE_WITH_CONCERNS, fail→BLOCKED
- PM 핸드오프 템플릿: `{{PREVIOUS_VALIDATION_STATUS}}`와 `{{PREVIOUS_COMPLETION_STATUS}}` 병기

## Data Flow Contracts

### analysis → design
| 필드 | 소스 | 설명 |
|------|------|------|
| codebase_analysis | explorer.findings | 코드 구조 분석 결과 |
| requirements | pm.scope | 분해된 요구사항 |
| impact_assessment | explorer.residual_risk | 변경 위험도 |

### design → preparation
| 필드 | 소스 | 설명 |
|------|------|------|
| design_doc | architect.artifacts | 승인된 설계 문서 |
| schema_changes | architect.findings | DB 변경 필요 사항 |
| component_specs | designer.artifacts | UI 컴포넌트 명세 |

### preparation → implementation
| 필드 | 소스 | 설명 |
|------|------|------|
| schema.sql | dba.artifacts | 마이그레이션 스크립트 |
| component_specs | designer.artifacts | 컴포넌트 명세 |
| design_doc | architect.artifacts | 구현 가이드 |

### implementation → verification
| 필드 | 소스 | 설명 |
|------|------|------|
| changed_files | developer.artifacts | 변경된 파일 목록 |
| implementation_scope | developer.scope | 구현 범위 |
| known_risks | developer.residual_risk | 개발자가 인지한 위험 |

### verification → deployment
| 필드 | 소스 | 설명 |
|------|------|------|
| test_report | qa.artifacts | 테스트 결과 |
| approval_status | qa.completion_status | DONE 필수 |
| review_reports | reviewers.artifacts | 리뷰 결과 목록 |

### deployment → documentation
| 필드 | 소스 | 설명 |
|------|------|------|
| deployment_log | publisher.artifacts | 배포 로그 |
| changed_files | developer.artifacts | 변경 파일 목록 |
| api_changes | api-reviewer.findings | API 변경 사항 |

## Handoff Validation Rules

1. **필수 필드 검증**: scope, findings, recommendation, completion_status가 비어있으면 핸드오프 실패
2. **CRITICAL 이슈 차단**: 이전 단계에서 CRITICAL 이슈가 해결되지 않으면 다음 단계 진행 불가
3. **잔여 위험 전달**: 이전 에이전트의 residual_risk는 다음 에이전트 태스크 설명에 반드시 포함
4. **아티팩트 존재 확인**: artifacts에 명시된 파일이 실제 존재하는지 확인
5. **재시도 정책**: 핸드오프 레벨 1회 재시도 → 재실패 시 PM에게 에스컬레이션 (에이전트 내부 재시도는 failure-policy 관장)

## PM Handoff Template

PM이 에이전트를 스폰할 때 사용하는 컨텍스트 전달 템플릿:

```markdown
## 컨텍스트
- 프로젝트: {{PROJECT_PATH}}
- 기술스택: {{TECH_STACK}}
- 태스크 ID: {{TASK_ID}}

## 이전 단계 결과
- **범위**: {{PREVIOUS_SCOPE}}
- **발견사항**: {{PREVIOUS_FINDINGS}}
- **권장사항**: {{PREVIOUS_RECOMMENDATION}}
- **완료 상태**: {{PREVIOUS_COMPLETION_STATUS}}
- **상태 근거**: {{PREVIOUS_COMPLETION_DETAIL}}
- **검증 상태 (deprecated)**: {{PREVIOUS_VALIDATION_STATUS}}
- **잔여 위험**: {{PREVIOUS_RESIDUAL_RISK}}
- **산출물**: {{PREVIOUS_ARTIFACTS}}

## 현재 태스크
{{TASK_DESCRIPTION}}

## 주의사항
{{INHERITED_RISKS}}
```

## Quality Gate Pass Criteria (v2.0)

| completion_status | 게이트 결과 | 조건 |
|-------------------|-----------|------|
| DONE | 통과 | 무조건 |
| DONE_WITH_CONCERNS | 조건부 통과 | concerns가 LOW/MEDIUM이면 통과, HIGH면 PM 판단 |
| BLOCKED | 차단 | 무조건 |
| NEEDS_CONTEXT | 차단 | 무조건 |
