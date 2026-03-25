# Code Digest Format v1.0

Explorer 에이전트가 리뷰 대상 코드를 사전 분석하여 생성하는 구조화된 요약.
6명의 리뷰어가 동일 파일을 중복 분석하는 것을 방지하고, 각 리뷰어에게 도메인 관련 섹션만 전달.

## Digest 구조

```yaml
digest:
  generated_at: "{{timestamp}}"
  generated_by: explorer
  change_summary:
    total_files: N
    total_lines_added: N
    total_lines_removed: N
    services_affected: [list]
    schemas_affected: [list]

  files:
    - path: "path/to/file.ts"
      purpose: "한 줄 요약 (이 파일이 하는 일)"
      change_type: "modified | added | deleted"
      key_changes:
        - "함수 X를 추가하여 Y 기능 구현"
        - "에러 핸들링 로직 변경"
      dependencies:
        imports: ["module_a", "module_b"]
        imported_by: ["consumer_1", "consumer_2"]
      domain_tags:
        security: true    # 인증/인가/입력검증 관련 코드 포함
        performance: true # 쿼리/캐시/반복문 관련 코드 포함
        api: false        # API 엔드포인트 변경 없음
        accessibility: false
        ux: true          # UI 컴포넌트 변경 포함
        test: false
      complexity:
        cyclomatic: 12
        lines: 250
        nesting_depth: 4
```

## 리뷰어별 필터링 규칙

| 리뷰어 | 받는 정보 | domain_tag 필터 |
|--------|----------|----------------|
| Security Reviewer | security=true 파일의 전체 코드 + 나머지 요약 | security |
| Performance Reviewer | performance=true 파일의 전체 코드 + 나머지 요약 | performance |
| API Reviewer | api=true 파일의 전체 코드 + 나머지 요약 | api |
| Accessibility Reviewer | accessibility=true 파일의 전체 코드 + 나머지 요약 | accessibility |
| UX Reviewer | ux=true 파일의 전체 코드 + 나머지 요약 | ux |
| Test Coverage Reviewer | test=true 파일의 전체 코드 + 나머지 요약 | test |
| Code Reviewer | 모든 파일 (제한 없음) | all |
| Architect | 모든 파일 요약 + complexity 높은 파일 전체 | all (complexity > 15) |

## PM 사용 방법

1. Explorer에게 digest 생성 요청
2. Digest의 domain_tags 기반으로 관련 리뷰어만 스폰
3. 각 리뷰어에게 해당 domain의 파일만 전체 코드 전달
4. 비관련 파일은 digest 요약만 전달 (토큰 절약)

## 예상 효과
- 6명 리뷰어 × 10파일 = 60회 파일 읽기 → digest 기반 ~20회로 감소
- 토큰 사용량 40-60% 절감
- 비관련 리뷰어 자동 스킵 (domain_tag 기반)
