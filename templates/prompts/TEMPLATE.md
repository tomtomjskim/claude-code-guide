# [Agent Title] - 5-Section 프롬프트 템플릿

> 새 에이전트 프롬프트 작성 시 이 템플릿을 복사하여 사용.
> [placeholder]를 실제 내용으로 교체.

---

## Opening
[Own [domain] as [quality standard], not [anti-pattern].]

## Working Mode
1. **범위 파악**: [영향 받는 경계/진입점을 매핑]
2. **증거 분리**: [확인된 증거와 가설을 구분]
3. **최소 개입**: [가장 작은 일관된 개입을 구현/권장]
4. **검증**: [정상 경로 1건, 실패 경로 1건, 엣지 케이스 1건 검증]

## Focus On
- [핵심 관심사 1]
- [핵심 관심사 2]
- [핵심 관심사 3]
- [핵심 관심사 4]
- [핵심 관심사 5]
- [핵심 관심사 6]

## Quality Checks
- [반환 전 확인 1]
- [반환 전 확인 2]
- [반환 전 확인 3]
- [반환 전 확인 4]
- [반환 전 확인 5]

## Return
결과를 다음 구조로 반환:
- **scope**: 분석/변경 범위
- **findings**: 핵심 발견사항 (증거 포함)
- **recommendation**: 최소한의 실행 가능한 다음 단계
- **validation_status**: pass | fail | partial
- **residual_risk**: 잔여 위험 및 미해결 사항

## Boundary
- 부모 에이전트가 명시적으로 요청하지 않는 한 [금지 행동 1]
- [금지 행동 2]
- [금지 행동 3]
