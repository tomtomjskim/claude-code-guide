---
name: check-spec
description: "설계문서(spec) 검수. 3단계 프리셋(quick/standard/thorough) + 팀 검수(--team) 지원. docs/spec/ 문서의 규칙/코드베이스 일관성 검토."
---

너는 능숙한 프로젝트 설계문서 검수 전문가야.

설계문서(spec)가 프로젝트 규칙과 코드베이스에 일관성 있게 작성되었는지 최종 검토합니다.

## 설계 검수 프리셋

### 깊이(depth)와 실행(mode) 2축 체계

**깊이 (depth)** — 검수의 범위와 상세도:

| 깊이 | 시간 | 내용 |
|------|------|------|
| `--quick` | ~2분 | 문서 구조 + 필수 섹션 존재 여부만 |
| (기본) standard | ~5분 | 구조 + 코드베이스 대조 + 규칙 검증 (Phase 1~3) |
| `--thorough` | ~10분 | 전체 Phase + 요구사항 완전성 심층 + 대안 검토 |

**실행 (mode)** — 단일 에이전트 vs 팀:

| 모드 | 설명 |
|------|------|
| (기본) 단일 | 1명이 순차 검수 |
| `--team` | Architect+DBA+Explorer 다관점 검수 |

### 조합 사용

```
/check-spec {모듈}                    # standard + 단일 (기본)
/check-spec --quick {모듈}            # quick + 단일
/check-spec --thorough {모듈}         # thorough + 단일
/check-spec --team {모듈}             # thorough + 팀 (기본 최대 깊이)
/check-spec --team --quick {모듈}     # quick + 팀 (빠른 구조 확인)
```

**`--team` 단독 사용 시 기본 깊이 = thorough** (최대 성능)

### --quick 깊이
1. 문서 파일 존재 여부 (architecture.md, api_design.md, database_schema.md)
2. 필수 섹션 헤더 존재 여부
3. 명백한 누락 항목 식별

### --thorough 깊이
standard + 추가:
1. **요구사항 완전성 심층** (0절 전체): 비즈니스 로직, 엣지 케이스, 상태 전이
2. **대안 검토**: 설계 대안의 장단점이 충분히 비교되었는지
3. **보안/성능 설계**: 공격 벡터, N+1, 인덱스 계획이 명세에 포함되었는지
4. **마이그레이션 리스크**: 기존 데이터 영향, 롤백 전략 유무

### --team 모드 (Agent Teams)
```
팀 구성:
┌─ PM (Lead): 검수 조율, 결과 종합
├─ Architect: 설계 일관성, 레이어 분리, 패턴 준수
├─ DBA: DB 스키마 정합성, 인덱스 계획, 쿼리 최적화 전략
└─ Explorer: 코드베이스 대조, 유사 패턴 비교, 영향 범위 확인
```

---

## 검수 대상

$ARGUMENTS 로 전달받은 설계문서 경로 또는 모듈명을 검수합니다.
- 경로 예시: `docs/spec/moduleName/architecture.md`
- 모듈명 예시: `moduleName`

## 검수 체크리스트

### 0. 요구사항 및 로직 완전성 검토 (CRITICAL)

**목적:** 설계 시 놓친 로직이나 요구사항이 없는지 검토

#### 0.1 요구사항 완전성
- [ ] 원래 요구사항 대비 누락된 기능 없음
- [ ] 모든 사용자 시나리오 커버됨
- [ ] 예외 케이스/엣지 케이스 처리 명시됨

#### 0.2 비즈니스 로직 검토
- [ ] 상태 변경 로직 완전성
- [ ] 권한/조건 체크 로직 명시
- [ ] 데이터 유효성 검증 로직 포함
- [ ] 실패 시 롤백/에러 처리 명시

#### 0.3 후처리/연동 로직 검토
- [ ] callback 처리 시나리오 완전성
- [ ] 다양한 호출 위치별 후처리 분기
- [ ] 연속 작업 시 버튼 비활성화/중복 방지
- [ ] 성공/실패 시 사용자 피드백 명시

#### 0.4 사용자 시나리오 검토
- [ ] 정상 플로우 (Happy Path) 명시
- [ ] 예외 플로우 (Error Path) 명시
- [ ] 직접 URL 접근 시 동작
- [ ] 권한 없는 사용자 접근 시 동작

#### 0.5 데이터 바인딩 검토
- [ ] 필요한 모든 필드 쿼리에 포함
- [ ] 표시해야 할 모든 데이터 UI에 바인딩
- [ ] 누락 필드 목록 명시 (있는 경우)

---

<!-- CUSTOMIZE: Technology Stack Validation Rules
The sections below (1-6) contain example validation rules for a PHP/MySQL/SCSS project.
Replace each section with your project's technology-specific validation rules.
For example:
- TypeScript: ESLint rules, type safety checks
- Python: mypy type hints, PEP8 compliance
- React: Component structure, hooks rules
- Go: Interface compliance, error handling patterns
-->

### 1. 파일/경로 컨벤션 검증

**확인 명령:**
```bash
# 모듈 파일 패턴 확인 (프로젝트에 맞게 수정)
ls modules/{domain}/*.* 2>/dev/null || echo "모듈 없음"
ls views/{domain}/*.* 2>/dev/null || echo "뷰 없음"
```

**체크 항목:**
- [ ] 파일명이 기존 패턴과 일치
- [ ] 라우트 URL 패턴 일관성
- [ ] 스타일 파일명이 뷰와 동일

### 2. API 패턴 검증

**체크 항목:**
- [ ] API 등록 형식이 프로젝트 표준 준수
- [ ] 파라미터 정의에 이름, 타입, 설명, 필수여부 포함
- [ ] 반환값 구조가 프로젝트 표준 응답 포맷 준수
- [ ] API 호출 경로에 전체 경로 포함

### 3. DB 스키마 검증

**확인 방법:** db-mcp 사용
```sql
SHOW COLUMNS FROM {테이블명};
```

**체크 항목:**
- [ ] 컬럼명 실제 존재 확인
- [ ] 데이터 타입 일치
- [ ] SQL 예약어 적절히 처리
- [ ] soft delete 필드 존재 여부 확인

### 4. JavaScript 문법 검증

**체크 항목:**
- [ ] 변수 선언 확인
- [ ] API 응답 필드명 네이밍 컨벤션 일치
- [ ] 프로젝트 표준 다이얼로그/알림 사용
- [ ] 이벤트 핸들러 올바른 등록

### 5. 스타일 검증

**체크 항목:**
- [ ] 필수 import 존재
- [ ] 프로젝트 스타일 가이드 준수
- [ ] 하드코딩 값 미사용 (CSS 변수 사용)
- [ ] 불필요한 주석 미작성

### 6. i18n 검증

**체크 항목:**
- [ ] 모든 텍스트 i18n 함수 사용
- [ ] 하드코딩 텍스트 없음
- [ ] 새로운 키 목록 문서화

## 검수 프로세스

### Phase 1: 문서 구조 확인
1. 설계문서 읽기
2. 목차 및 섹션 구조 확인
3. 누락 섹션 파악

### Phase 2: 코드베이스 대조
1. 기존 유사 파일 패턴 확인
2. API 패턴 대조
3. DB 스키마 실제 확인 (db-mcp)

### Phase 3: 문법/규칙 검증
1. 코드 문법 검사
2. 스타일 규칙 검사
3. 린트 검사

### Phase 4: 검수 결과 기록
문서에 검수 이력 섹션 추가:
```markdown
## 검수 이력

| 날짜 | 검수 항목 | 결과 | 비고 |
|------|----------|------|------|
| YYYY-MM-DD | 전체 | PASS/FAIL | 발견 사항 |
```

## 출력 형식

```markdown
# 설계문서 검수 결과

**문서**: {문서 경로}
**검수일**: YYYY-MM-DD
**결과**: PASS / WARN / FAIL

---

## 0. 요구사항/로직 완전성 검토

| 항목 | 결과 | 비고 |
|------|------|------|
| 요구사항 완전성 | PASS/WARN/FAIL | |
| 비즈니스 로직 | PASS/WARN/FAIL | |
| 후처리/연동 로직 | PASS/WARN/FAIL | |
| 사용자 시나리오 | PASS/WARN/FAIL | |
| 데이터 바인딩 | PASS/WARN/FAIL | |

### 놓친 로직/요구사항
- WARN: {발견된 누락 사항}
- WARN: {추가 필요한 예외 처리}

---

## 1. 형식/컨벤션 검수

### 통과 항목
- PASS: 파일/경로 컨벤션
- PASS: API 패턴

### 수정 필요 항목
- WARN: [항목]: 발견 사항 및 수정 방안

---

## 개선 권장 사항
- 추가 고려사항
- 향후 확장 시 고려할 점
```

## 참조 문서

- `.claude/spec_review_checklist.md` - 상세 체크리스트
- `.claude/admin_ui_style_guide.md` - Admin UI 스타일 가이드
- `.claude/coding_guidelines.md` - 코딩 규칙
