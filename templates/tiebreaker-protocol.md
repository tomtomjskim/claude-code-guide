# Tiebreaker Protocol v1.0

리뷰어 의견이 충돌할 때 PM이 실행하는 4단계 중재 프로토콜.
`/check-code --thorough` 또는 `--team` 모드에서 여러 Specialist Reviewer의 판단이 상충할 때 적용.

---

## 적용 조건

2명 이상의 리뷰어가 동일 코드에 대해 상반된 판단을 내린 경우:
- Security Sentinel이 "CRITICAL" vs Performance Prophet가 "수정 불필요"
- Code Reviewer가 "리팩토링 필요" vs API Arbiter가 "하위호환 우선"

---

## 4단계 중재 프로세스

### Step 1: 심각도 우선 (CRITICAL first)

CRITICAL 판정이 하나라도 있으면 무조건 우선 처리.
성능/가독성보다 보안/안정성이 우선.

### Step 2: 도메인 전문성 가중치

해당 이슈의 도메인에 가장 전문적인 리뷰어의 의견에 가중치 부여:

```
SQL Injection 관련    → Security Sentinel 우선
N+1 쿼리 관련        → Performance Prophet 우선
코드 구조 관련       → Code Reviewer 우선
API 스펙 관련        → API Arbiter 우선
권한 체크 관련       → Access Advocate 우선
UI 패턴 관련         → UX Harmonizer 우선
테스트 커버리지 관련  → Test Guardian 우선
```

### Step 3: 증거 기반 판정

도메인 전문성으로도 해결 안 되면 객관적 증거로 판정:

| 증거 유형 | 예시 |
|-----------|------|
| 표준/규격 | OWASP Top 10, RFC, 언어 공식 문서 |
| 프로젝트 규칙 | CLAUDE.md, 코딩 가이드라인 |
| 측정 데이터 | EXPLAIN 결과, 벤치마크, 린터 출력 |
| 기존 패턴 | 동일 프로젝트 내 유사 코드의 처리 방식 |

증거가 있는 쪽의 의견을 채택.

### Step 4: 사용자 에스컬레이션

위 3단계로도 해결되지 않으면 사용자에게 판단 요청:

```markdown
## 리뷰어 의견 충돌 발생

**대상**: {파일}:{라인}
**충돌 내용**:
- {Reviewer A}: {판정} — {근거}
- {Reviewer B}: {판정} — {근거}

**PM 분석**: {Step 1~3 시도 결과}

**선택지**:
1. {Reviewer A} 의견 채택 → {예상 영향}
2. {Reviewer B} 의견 채택 → {예상 영향}
3. 양측 절충안 → {절충안 설명}
4. 무시하고 진행 (비권장)
```

---

## 판정 기록

Tiebreaker 판정은 검수 결과 문서에 기록:

| 대상 | 충돌 리뷰어 | 판정 | 근거 | 단계 |
|------|-----------|------|------|------|
| {file}:{line} | Security vs Performance | Security 채택 | OWASP A03 | Step 1 |
| {file}:{line} | Code vs API | 절충안 | 사용자 판단 | Step 4 |

---

## 주의사항

- Tiebreaker는 PM만 실행 가능
- Step 1~3은 자동 실행, Step 4는 사용자 확인 필요
- 판정 결과는 Handoff의 residual_risk에 기록하여 다음 Phase에 전파
