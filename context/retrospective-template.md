# Retrospective Template v1.0

워크플로우 완료 후 PM이 수집하는 피드백 양식.
20+ 데이터포인트 축적 후 PM 자기 개선에 활용.

## 피드백 양식

### 워크플로우 메타
- **워크플로우**: {{workflow_name}} ({{preset}})
- **날짜**: {{date}}
- **프로젝트**: {{project_path}}
- **총 에이전트**: {{agent_count}}
- **총 비용**: {{total_cost_usd}}

### 에이전트 유용성 평가
| 에이전트 | 발견 수 | 유용한 발견 | 오탐(False Positive) | 유용성 점수 (1-5) |
|----------|---------|-----------|---------------------|-------------------|
| {{agent}} | {{total}} | {{useful}} | {{false_positive}} | {{score}} |

### 워크플로우 적절성
- **선택된 프리셋**: {{preset}}
- **적절했는가**: 예 / 아니오 (더 높은/낮은 프리셋이 적절)
- **스킵 가능했던 에이전트**: {{skippable_agents}}
- **추가 필요했던 에이전트**: {{needed_agents}}

### 비용 효율성
- **예산 대비 실제**: {{budget_usd}} → {{actual_usd}}
- **에스컬레이션 횟수**: {{escalation_count}}
- **서킷 브레이커 발동**: 예 / 아니오

### 자유 코멘트
{{user_comment}}

---

## 축적된 데이터 활용 (PM 자기 개선)

### 에이전트 스킵 규칙 학습
20+ 피드백 후, 유용성 점수 평균이 2.0 미만인 에이전트는 해당 프로젝트 유형에서 자동 스킵 후보로 표시.

```
if avg_usefulness[agent][project_type] < 2.0 over 20+ reviews:
    suggest: "{{agent}}는 {{project_type}} 리뷰에서 일관되게 낮은 유용성. 스킵 권장?"
```

### 프리셋 추천 정확도
```
if preset_was_appropriate == false over 5+ cases:
    adjust: "{{project_type}}에서 {{recommended_preset}} 사용 권장 (현재 {{current_preset}})"
```

### 비용 예측 보정
```
actual_to_budget_ratio = actual_usd / budget_usd
if ratio > 1.3 consistently:
    adjust: "{{workflow}} 예산을 {{suggested_budget}}로 상향 권장"
```

### 오탐률 모니터링
```
if false_positive_rate[agent] > 30%:
    flag: "{{agent}}의 오탐률이 높음. 프롬프트 Quality Checks 강화 필요"
```
