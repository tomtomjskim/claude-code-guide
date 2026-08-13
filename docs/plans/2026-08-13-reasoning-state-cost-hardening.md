# Reasoning State And Cost Hardening Plan

작성일: 2026-08-13
대상: `claude-code-guide`
상태: implementation candidate

## 목표

Claude Code 가이드의 비용 계산, Fast Mode, context/compaction, thinking state, harness 설명을 현재 공식 문서와 맞추고, 검증되지 않은 내부 구현과 위험한 예시를 제거합니다.

## 선설계 범위

| Task | 문제 | 설계 결정 |
|---|---|---|
| T1 비용 | 1,000배 계산 오류, cache token 이중 계산 | usage field 기반 공식 계산식으로 교체 |
| T2 Fast Mode | 4.6 전용·6배·자동 활성화 단정 | 현재 지원 모델, opt-in, 2배 단가, workload decision으로 교체 |
| T3 Context | v2.1.88 내부 상수와 고정 threshold | 현재 공식 설정과 model-tuned default 중심으로 재작성 |
| T4 Reasoning state | thinking, redacted thinking, summary 경계 부족 | same-model round-trip, model-switch strip, log 격리 계약 추가 |
| T5 Harness | managed precedence 역전, unsafe SQL 예시, raw audit log | 현재 precedence, 안전한 query 규칙, metadata allowlist로 교체 |
| T6 Regression | 잘못된 숫자와 문구 재발 가능 | unittest로 필수·금지 문자열과 계산 검증 |

## 제외 범위

- 실제 API credential 또는 private trace 사용
- 논문 취약점 재현
- 모든 Claude Code 설정 키의 전수 최신화
- 구독 플랜별 사용량 예측
- 신규 Skill 또는 runtime package 생성
- 기존 installer와 hook runtime 동작 변경

## 공식 소스

- https://platform.claude.com/docs/en/about-claude/pricing
- https://platform.claude.com/docs/en/build-with-claude/prompt-caching
- https://platform.claude.com/docs/en/about-claude/models/extended-thinking-models
- https://code.claude.com/docs/en/model-config
- https://code.claude.com/docs/en/sub-agents
- https://code.claude.com/docs/en/settings
- https://code.claude.com/docs/en/fast-mode

## 적대적 검수 Lens

### Correctness

- MTok 계산 단위가 맞는가.
- cache_creation과 input을 중복 계산하지 않는가.
- current model과 retired model을 혼동하지 않는가.

### Security

- raw response, thinking, command, secret이 audit log로 복사되지 않는가.
- model switch 시 opaque state가 남지 않는가.
- SQL 예시가 injection을 유도하지 않는가.

### Cost

- 단일 호출 단가 대신 retry와 accepted-result cost를 보는가.
- Fast Mode를 절대 금지 또는 무조건 권장하지 않는가.
- subagent model 하향 후 품질 동일을 가정하지 않는가.

### Freshness

- 버전 내부 상수를 장기 계약으로 쓰지 않는가.
- source와 확인 날짜가 있는가.
- preview 기능의 변동 가능성을 표시했는가.

### Adoption

- 기존 runtime behavior를 변경하지 않고 문서와 regression만 수정하는가.
- 일반 프로젝트에 새로운 gate를 강제하지 않는가.

## 특이사항

- 초기 정적 검수에서는 기존 `$0.000345`를 단순히 1,000배 보정한 `$0.345`로 판단했으나, 공식 usage field를 재검토한 결과 cache write 40K를 일반 input 50K와 중복 계산한 두 번째 오류가 확인됐습니다. 최종 올바른 예시는 일반 input 10K + cache write 40K + output 3K로 `$0.225`입니다.
- 현재 Claude Code 공식 문서는 managed settings를 최고 우선순위로 정의합니다. 기존 harness 문서는 managed를 최저로 적어 정책 우회 오해를 만들 수 있었습니다.
- 별도 모델 subagent runtime은 현재 작업 환경에 노출되지 않아, 독립 lens를 순차 적용한 adversarial review로 대체합니다.
- 로컬 `gh`와 network가 없어 GitHub connector로 branch와 PR을 생성하고 CI 결과를 authoritative validation으로 사용합니다.

## 검증 계약

```bash
python3 -m unittest discover -s scripts/tests -p 'test_*.py' -v
bash scripts/validate-repository.sh
git diff --check
```

## 완료 조건

- 기존 오계산과 obsolete Fast Mode 문구가 제거됨
- current source와 as-of 날짜가 있음
- thinking state와 semantic checkpoint가 분리됨
- unsafe SQL 예시와 raw audit logging 예시가 제거됨
- regression test 통과
- draft PR CI 또는 미실행 사유가 기록됨
