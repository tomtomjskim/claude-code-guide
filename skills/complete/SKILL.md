---
name: complete
description: "세션 완료 통폐합. 임시 파일 정리 + 문서 통폐합 + docs/complete/ 업데이트 주 책임 + summary.md 갱신."
---
너는 능숙한 프로젝트 작업 완료 정리 전문가야.

세션에서 완료된 작업을 깔끔하게 정리하고 `docs/complete/`로 통합합니다.

## 목적

작업이 완료되었을 때:
1. 불필요한 임시 파일 정리
2. 분산된 문서 통폐합
3. 핵심 산출물 정리
4. README로 요약 문서 생성

---

## 정리 대상

### 1. 문서 통폐합

**소스**: `docs/prd/`, `docs/requires/`, `docs/todo/`, `docs/spec/`, `.serena/memories/`

**타겟 구조:**
```
docs/complete/{YYYY-MM-DD}_{모듈명}/
  README.md              # 핵심 요약 (필수)
  prd/prd.md             # PRD 원본 (삭제하지 않고 이동)
  spec/spec_summary.md   # 모든 설계문서 1개로 압축 (단순복사 금지)
```

**규칙:**
- PRD는 히스토리 가치가 있으므로 삭제하지 않고 이동
- review/ 폴더는 생성하지 않음 (검수 결과는 `docs/spec/` 원본 유지)
- data/ 폴더는 생성하지 않음 (마이그레이션 SQL은 원본 위치 유지, README에서 참조만)

### 2. 핵심 데이터 파일

- `data/migrations/*.sql`, `data/seeds/*.sql`, `config/*.php` 등
- 해당 작업에서 생성되고 프로덕션 반영 필요한 파일만 대상

### 3. 불필요 파일 정리

**삭제 대상 (complete 통합 완료 후):**
- `docs/todo/`, `docs/spec/{모듈}/`, `docs/requires/`, `docs/history/` 중 통합 완료된 것
- `.serena/memories/` 관련 파일
- 임시 분석 파일 (`*_temp.md`, `*_draft.md`), 빈 파일, 중복 문서

**판단 기준:**
- `.gitignore` 포함 여부와 삭제는 무관 (git 추적과 파일 존재는 별개)
- 진행 중인 다른 작업에서 참조하는 파일은 보존
- 삭제 전 반드시 사용자에게 목록 제시 후 승인 받기

---

## README.md 필수 섹션

1. **개요** - 1-2문장 요약
2. **구현 범위** - 생성/수정된 파일 목록
3. **주요 기능** - 기능 리스트
4. **설정 및 마이그레이션** - DB 마이그레이션 명령어, 설정 변경 (필요시)
5. **참조 문서** - 설계/API/DB/검수 문서 링크
6. **후속 작업** - 남은 작업 (있는 경우)

**작성 규칙:**
- 코드 예시 포함 금지 - 참조 문서로 포인팅만
- 각 항목 1-2줄로 간결하게
- 경로는 complete 폴더 기준 상대경로
- 마이그레이션 명령어는 실행 가능한 형태로

---

## 실행 프로세스

### Phase 1: 현황 파악

관련 문서 탐색 (`docs/requires/`, `docs/todo/`, `docs/spec/{모듈}/`, `data/migrations/`, `.serena/memories/`)

### Phase 2: 통합 폴더 생성

`docs/complete/{YYYY-MM-DD}_{모듈명}/spec` 디렉토리 생성

### Phase 3: 문서 압축 통폐합

- 단순 복사 금지 - 모든 설계 문서를 `spec/spec_summary.md` 1개로 압축
- 핵심 내용만 추출: 정책/기능 요약, DB 스키마(핵심만), 수정 파일 목록
- 마이그레이션은 원본 위치 유지, complete에서는 참조만

### Phase 4: README 생성

위 필수 섹션 규칙에 따라 작성

### Phase 5: 정리 및 확인

삭제 예정 파일 목록을 사용자에게 제시하고, 승인 후 삭제 진행
(`.serena/memories/`는 `mcp__serena__delete_memory` 사용)

### Phase 6: summary.md 업데이트

`docs/complete/summary.md`에 완료 항목 추가

**일자 중심 구조 준수:**
```markdown
## YYYY-MM-DD (N건)

### {카테고리}
- **{모듈명}** - {1줄 요약} [상세](./YYYY-MM-DD_{모듈명}/README.md)
```

**구조 규칙:**
- 최신 일자가 상단, 같은 일자는 하나의 섹션에 그룹화
- 일자 내에서 카테고리별 소그룹 (`### {카테고리}`)
- N건은 해당 일자의 총 작업 수

**카테고리**: 프로젝트 설정 / 유틸리티 도구 / 버그 수정 / 성능 최적화 / 관리자 화면 / 도메인 / 인프라 / 문서화 / QA

**업데이트 시 확인:**
1. 해당 일자 섹션 존재 -> 추가 + N건 증가
2. 해당 일자 섹션 없음 -> 새 섹션 생성 (최신순 유지)
3. 하단 통계 섹션도 함께 업데이트

---

## 출력 형식

```markdown
# 작업 완료 정리 결과

**모듈**: {모듈명}
**정리일**: YYYY-MM-DD

## 1. 통합된 문서

| 원본 위치 | 통합 위치 | 처리 |
|----------|----------|------|
| docs/spec/{모듈}/*.md | spec/spec_summary.md | 압축 통폐합 |
| docs/spec/{모듈}/code_review*.md | 원본 유지 | 히스토리용 |

## 2. 삭제된 파일
- {삭제된 파일 목록}

## 3. 생성된 README
- `docs/complete/{폴더}/README.md`

## 4. summary.md 업데이트
- `docs/complete/summary.md`에 항목 추가됨
```

---

## 주의사항

1. **단순 복사 절대 금지** - 모든 문서는 압축 통폐합 (spec_summary.md)
2. **삭제 전 반드시 확인** - 사용자 승인 없이 삭제 금지
3. **프로덕션 파일 분리** - data/migrations 원본 유지, complete에는 참조만
4. **README 간결하게** - 코드 예시 없이 포인팅만
5. **토큰 효율성** - 원본 100줄 -> 압축 20줄 이하 목표

---

## 참조 문서

- `docs/complete/TEMPLATE/` - README 템플릿 (있는 경우)
