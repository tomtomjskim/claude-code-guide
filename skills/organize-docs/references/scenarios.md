# organize-docs 상세 가이드

이 문서는 `/organize-docs` 커맨드의 상세 템플릿, 예시, 체크리스트, 옵션 조합표, 트러블슈팅을 포함한다.
핵심 규칙과 실행 흐름은 SKILL.md 참조.

---

## 옵션 처리 로직

### $ARGUMENTS 파싱

```bash
# 예: /organize-docs 2025-11-15 --dry-run --backup
TARGET=""       # 2025-11-15
DRY_RUN=false   # true
BACKUP=false    # true
AUTO=false
MERGE=false
VERBOSE=false

for arg in $ARGUMENTS; do
  case $arg in
    --dry-run) DRY_RUN=true ;;
    --backup) BACKUP=true ;;
    --auto) AUTO=true ;;
    --merge) MERGE=true ;;
    --verbose) VERBOSE=true ;;
    *) TARGET="$arg" ;;
  esac
done
```

### 옵션별 상세 동작

**--dry-run**: 분석 및 브리핑만 실행. 생성될 파일 목록과 summary.md 변경 사항 미리보기 출력.

**--backup**: 원본을 `.backup-YYYYMMDD-HHMMSS/`로 복사. summary.md도 별도 백업.

```bash
BACKUP_DIR=".backup-$(date +%Y%m%d-%H%M%S)"
cp -r [원본 디렉토리] "$BACKUP_DIR"
cp docs/complete/summary.md "docs/complete/summary.md.backup-$(date +%Y%m%d-%H%M%S)"
```

**--auto**: 사용자 승인 없이 자동 진행. 중요 작업에는 비권장.

**--merge**: 기존 파일이 있으면 덮어쓰지 않고 `---` 구분자 뒤에 내용 추가.

**--verbose**: Git 명령어 실행 결과, 파일 분석 과정 상세 출력.

### 옵션 조합표

| 조합 | 사용 상황 | 안전성 | 속도 |
|------|----------|--------|------|
| `--dry-run` | 처음 사용 시 | 최고 | 보통 |
| `--backup` | 중요 작업 | 높음 | 낮음 |
| `--auto` | 빠른 처리 | 낮음 | 최고 |
| `--merge` | 중복 방지 | 높음 | 보통 |
| `--dry-run --verbose` | 완전 검증 | 최고 | 낮음 |
| `--backup --merge` | 안전 + 병합 | 최고 | 낮음 |
| `--auto --merge` | 빠른 병합 | 보통 | 높음 |

### 옵션 주의사항

- `--dry-run`: 실제 실행은 별도로 필요
- `--backup`: 디스크 공간 필요, 백업 파일 수동 삭제 필요
- `--auto`: 검증 없이 실행되므로 중요 작업에는 비권장
- `--merge`: 파일이 길어질 수 있어 수동 정리 필요할 수 있음
- `--verbose`: 로그 출력이 많아 가독성 저하 가능

---

## 시나리오 A 상세: 문서화 누락 보완

### Phase 0: 문서화 누락 탐지

#### 0.1 Git 분석

```bash
# 최근 7일간 커밋 로그
git log --since="7 days ago" --pretty=format:"%h - %an, %ar : %s" --no-merges

# 최근 수정된 파일 목록
git diff HEAD~20 --name-only | grep -E "\.(php|js|scss|ts|py)$"

# 날짜별 변경 파일
git log --since="7 days ago" --name-only --pretty=format:"=== %cd ===" --date=short
```

분석 내용: 수정된 파일, 커밋 메시지에서 작업 내용 파악, 도메인/모듈 식별

#### 0.2 최근 수정 파일 확인

```bash
find . -type f \( -name "*.php" -o -name "*.js" -o -name "*.ts" -o -name "*.py" -o -name "*.scss" \) -mtime -7 \
  ! -path "./vendor/*" ! -path "./node_modules/*" \
  -exec ls -lh {} \; | sort -k6,7
```

#### 0.3 기존 문서 확인

```bash
ls -lt docs/history/ | head -10
ls -lt docs/complete/*.md | head -10

for date in $(git log --since="7 days ago" --pretty=format:"%cd" --date=short | sort -u); do
  echo "=== $date ==="
  ls docs/history/*$date* 2>/dev/null || echo "  history 없음"
  ls docs/complete/*$date* 2>/dev/null || echo "  complete 없음"
done
```

#### 0.4 Memory 확인 (선택)

```bash
mcp__serena__list_memories
mcp__serena__read_memory("[관련 memory 파일]")
```

#### 0.5 문서화 갭(Gap) 분석 - 사용자 브리핑 형식

```markdown
## 문서화 누락 분석 결과

### 최근 7일간 작업 내역

| 날짜 | 변경 파일 | 도메인/모듈 | 추정 작업 | history | complete |
|------|----------|------------|----------|---------|----------|
| 2025-11-15 | modules/feature/xxx.php (3개) | Feature | 기능 구현 | X | X |
| 2025-11-16 | views/admin/list.php (2개) | Admin UI | 관리 개선 | O | X |

### 문서화 필요 작업 (N건)

#### 1. YYYY-MM-DD: [작업명]
**변경 파일**: [목록]
**Git 커밋 메시지**: [목록]
**생성 필요**: history / complete

**진행 방식 선택**:
1. 자동 생성 (Git/파일 분석 기반, 빠름)
2. 상세 입력 (추가 정보 질문 후 생성, 정확함)
3. 선택 생성 (특정 작업만 선택)
```

### Phase 2-Doc: 누락 문서 생성

#### 작업 내역 재구성

```bash
DATE="2025-11-15"
git log --since="$DATE 00:00:00" --until="$DATE 23:59:59" \
  --pretty=format:"%h - %s" --name-status
```

#### history 문서 템플릿

파일: `docs/history/YYYY-MM-DD_[task_name].md`

```markdown
# [작업명]

**작업일**: YYYY-MM-DD
**도메인**: [domain]

## 작업 내용

[Git 커밋 메시지 기반 요약]

## 주요 변경사항

### Backend
[변경 파일 목록 및 설명]

### Frontend
[변경 파일 목록]

### Database
[스키마 변경 내역]

## 수정 파일 목록

| 파일 | 변경 유형 | 설명 |
|------|----------|------|
| [파일경로] | [추가/수정/삭제] | [Git diff 기반 설명] |

## 참고
- 관련 Spec: docs/spec/[domain]/
- 완료 보고: docs/complete/YYYY-MM-DD_[task].md
```

#### complete 문서 템플릿

파일: `docs/complete/YYYY-MM-DD_[task_name].md`

```markdown
# [작업명] 완료

**완료일**: YYYY-MM-DD
**소요 시간**: [추정 또는 사용자 입력]

---

## 작업 요약
[한 줄 요약]

---

## 주요 구현 내용

### 1. [기능 1]
[파일 분석 기반 자동 생성]

### 2. [기능 2]
[파일 분석 기반 자동 생성]

---

## 수정 파일

**Backend (N개)**:
- `[파일경로]` - [설명]

**Frontend (M개)**:
- `[파일경로]` - [설명]

**총 변경**: [총 라인 수] lines

---

## 참고 문서
- 작업 이력: docs/history/YYYY-MM-DD_[task].md
- 기술 스펙: docs/spec/[domain]/ (있으면)

---

## 후속 작업
- [ ] [사용자 확인 필요 사항]
- [ ] [테스트 필요 사항]
```

#### 관련 todo/spec 문서 complete로 통합

```bash
DOMAIN=$(echo $TASK_NAME | grep -oE "^[a-z_]+")

# complete 아카이브 디렉토리 생성
COMPLETE_DIR="docs/complete/YYYY-MM-DD_[task_name]"
mkdir -p "$COMPLETE_DIR/references/todo"
mkdir -p "$COMPLETE_DIR/references/spec"

# history 문서 복사
cp "docs/history/YYYY-MM-DD_[task].md" "$COMPLETE_DIR/history.md"

# 메인 complete 문서 복사
cp "docs/complete/YYYY-MM-DD_[task].md" "$COMPLETE_DIR/completion_report.md"

# 관련 todo/spec 문서 이동
for file in $(find docs/todo/ -name "*${DOMAIN}*"); do
    mv "$file" "$COMPLETE_DIR/references/todo/"
done
for file in $(find docs/spec/ -name "*${DOMAIN}*"); do
    mv "$file" "$COMPLETE_DIR/references/spec/"
done

# 빈 디렉토리 삭제
[ -d "docs/todo/${DOMAIN}" ] && [ -z "$(ls -A docs/todo/${DOMAIN})" ] && rmdir "docs/todo/${DOMAIN}"
[ -d "docs/spec/${DOMAIN}" ] && [ -z "$(ls -A docs/spec/${DOMAIN})" ] && rmdir "docs/spec/${DOMAIN}"
```

아카이브 최종 구조:
```
docs/complete/
  YYYY-MM-DD_[task_name].md           # 메인 완료 보고서
  YYYY-MM-DD_[task_name]/             # 관련 자료 통합
    completion_report.md
    history.md
    references/
      todo/                           # 관련 todo 문서 (이동)
      spec/                           # 관련 spec 문서 (이동)
```

아카이브 디렉토리에는 README.md를 생성하여 디렉토리 구조, 포함된 문서 목록, 연관 문서 링크를 기록한다.

#### summary.md 업데이트

추가 위치: Git 분석으로 도메인/카테고리 자동 분류

형식:
```markdown
#### [자동 분류된 카테고리]
**YYYY-MM-DD**:
- [작업명] - [한 줄 요약]
```

통계와 최근 완료 작업도 함께 업데이트한다.

---

## 시나리오 B 상세: 기존 문서 정리

### Phase 1: 대상 분석

```bash
ls -la {$ARGUMENTS}
find {$ARGUMENTS} -type f -name "*.md" | head -20

for file in {$ARGUMENTS}/*.md; do
    echo "=== $file ===" && head -30 "$file"
done
```

파일 분류 기준:

| 파일 유형 | 목적지 | 판단 기준 |
|----------|--------|----------|
| `*_prd.md`, `requirements.md`, `README.md` | `docs/todo/[domain]/` | 요구사항, PRD |
| `*_spec.md`, `*_design.md`, `architecture.md`, `api_design.md`, `database_schema.md`, `flowchart.md` | `docs/spec/[domain]/` | 기술 설계 |
| `implementation_history.md`, `work_log.md` | `docs/history/` | 작업 과정 |
| `FINAL_REPORT.md`, `completion_report.md` | `docs/complete/` | 완료 보고서 |
| `*_plan.md`, `*_checklist.md`, `task_*.md` | 삭제 또는 통합 | 완료된 계획서 |
| `*_analysis.md`, `*_review.md` | 삭제 또는 spec 통합 | 일회성 분석 |

사용자 브리핑 형식:
```markdown
## 문서 정리 계획

### 현재 파일 현황 (N개)

| 파일명 | 크기 | 분류 | 목적지 |
|--------|------|------|--------|
| xxx.md | XXkB | PRD | docs/todo/[domain]/ |

### 정리 후 최종 구조
...

### 작업 단계
1. 디렉토리 생성
2. 파일 이동 및 이름 변경
3. 중복 파일 삭제
4. 참조 경로 업데이트
5. summary.md 업데이트
6. 원본 디렉토리 정리
```

### Phase 2: 실행

```bash
# 디렉토리 생성
mkdir -p docs/todo/[domain]
mkdir -p docs/spec/[domain]

# PRD 문서 복사
cp [source]/xxx_prd.md docs/todo/[domain]/

# 설계 문서 복사 (이름 표준화)
cp [source]/xxx_spec.md docs/spec/[domain]/

# 불필요한 파일 삭제
cd [source] && rm -f "implementation_checklist.md" "task_execution_plan.md"

# 원본 디렉토리 삭제 (복사 완료 확인 후)
ls -la docs/todo/[domain]/
ls -la docs/spec/[domain]/
rm -rf [source]
```

### Phase 3: summary.md 업데이트

```markdown
#### 문서화 시스템
**YYYY-MM-DD**:
- [작업명] - [source] -> docs/ 4-tier 구조 이관 (N->M개 파일, PRD/spec/complete 분류)
```

---

## 시나리오 C 상세: todo 기간별 통폐합

### Phase C-1: todo 문서 현황 분석

```bash
ls -la docs/todo/*.md
find docs/todo/ -maxdepth 1 -name "*.md" -type f

for file in docs/todo/*.md; do
    echo "=== $file ==="
    echo "크기: $(wc -c < "$file") bytes"
    echo "체크박스: $(grep -c '\[x\]' "$file") 완료 / $(grep -c '\[ \]' "$file") 미완료"
done
```

### Phase C-2: 완료 여부 판단

| 조건 | 상태 | 처리 방법 |
|------|------|----------|
| 모든 체크박스 `[x]` 완료 | 완료 | 아카이브 |
| `docs/complete/`에 동일 작업 존재 | 완료 | 아카이브 |
| 미완료 체크박스 `[ ]` 존재 | 진행중 | 유지 |
| 오늘 날짜 파일 | 진행중 | 유지 |

```bash
TODO_FILE="docs/todo/2025-11-15.md"
COMPLETED=$(grep -c '\[x\]' "$TODO_FILE")
PENDING=$(grep -c '\[ \]' "$TODO_FILE")

if [ "$PENDING" -eq 0 ]; then
    echo "완료됨 - 아카이브 대상"
else
    echo "진행중 ($PENDING건 미완료) - 유지"
fi

TASK_NAME=$(basename "$TODO_FILE" .md)
ls docs/complete/ | grep "$TASK_NAME"
```

### Phase C-3: 아카이브 구조

Before:
```
docs/todo/
  2025-11-15.md (5KB)
  2025-12-03.md (4KB)
  featureModule.md (4KB)
  2026-01-13.md (오늘)
```

After:
```
docs/todo/
  _archive/
    2025-11.md (참조만)
    2025-12.md (참조만)
  featureModule.md (진행중이면 유지)
  2026-01-13.md (오늘, 유지)
```

### Phase C-4: 월별 아카이브 템플릿

파일: `docs/todo/_archive/YYYY-MM.md`

```markdown
# YYYY년 MM월 작업 아카이브

**생성일**: YYYY-MM-DD
**원본 파일 수**: N개
**상태**: 완료 -> complete로 이관됨

---

## 작업 목록

### YYYY-MM-DD: [작업명]
- **상태**: 완료
- **완료 보고**: [`docs/complete/YYYY-MM-DD_xxx.md`](../../complete/YYYY-MM-DD_xxx.md)
- **원본**: 삭제됨 (상세 내용은 complete 참조)

---

## 통계
- **총 작업**: N건
- **완료**: N건 (100%)
- **complete 이관**: N건
```

### Phase C-5: 도메인별 todo 정리

완료된 경우 - 참조 링크만 남김:
```markdown
# feature_module

**상태**: 완료
**완료 보고**: [docs/complete/2025-12-16_feature.md](../complete/2025-12-16_feature.md)

> 상세 구현 내용은 complete 문서 참조
```

진행중인 경우 - 완료된 섹션만 참조로 전환:
```markdown
# feature_module

## 완료된 작업
- 인증 개선 -> [complete 참조](../complete/2025-12-15_auth.md)

## 진행중
- [ ] 결제 프로세스 개선
- [ ] 에러 핸들링 강화
```

### Phase C-6: 사용자 브리핑 형식

```markdown
## todo 통폐합 분석 결과

### 현재 todo 파일 현황

| 파일명 | 크기 | 완료율 | 처리 방법 |
|--------|------|--------|----------|
| `2025-11-15.md` | 5KB | 100% | 아카이브 (`_archive/2025-11.md`) |
| `feature_module.md` | 16KB | 80% | 참조 전환 (완료 섹션만) |
| `2026-01-13.md` | 3KB | 80% | 유지 (오늘) |

### 예상 결과
**Before**: 10개 파일, 총 80KB
**After**: 5개 파일, 총 15KB (81% 감소)
```

### Phase C-7: 실행

```bash
mkdir -p docs/todo/_archive
# Write 도구로 월별 아카이브 파일 생성
# Edit 도구로 도메인별 파일 참조 전환
# 완료된 날짜별 파일 삭제
rm docs/todo/YYYY-MM-DD.md
```

---

## 검증 체크리스트

### 시나리오 A: 문서화 누락 보완

**Phase 0: 누락 탐지**
- [ ] Git log 최근 7일 분석 완료
- [ ] 변경 파일 목록 추출 완료
- [ ] 기존 docs/history/, docs/complete/ 확인 완료
- [ ] 문서화 갭(Gap) 식별 완료
- [ ] 사용자에게 브리핑 완료

**Phase 2-Doc: 문서 생성**
- [ ] `docs/history/YYYY-MM-DD_[task].md` 생성됨
- [ ] `docs/complete/YYYY-MM-DD_[task].md` 생성됨
- [ ] 관련 todo/spec 문서가 complete 디렉토리로 통합됨
- [ ] `docs/complete/YYYY-MM-DD_[task]/` 아카이브 디렉토리 생성됨
- [ ] `docs/complete/YYYY-MM-DD_[task]/README.md` 생성됨
- [ ] 원본 todo/spec 문서들이 이동됨 (복사 아님)
- [ ] 빈 todo/spec 디렉토리 정리됨
- [ ] `docs/complete/summary.md` 업데이트됨 (통계 포함)
- [ ] 최근 완료 작업에 추가됨
- [ ] 파일 내용 검증 (Git 정보 정확성)

**4-Tier 구조 준수**
- [ ] history 문서가 작업 과정 기록함
- [ ] complete 문서가 완료 보고서 형식임
- [ ] summary.md 카테고리 분류 정확함
- [ ] 날짜 형식 일관성 (YYYY-MM-DD)

### 시나리오 B: 기존 문서 정리

- [ ] `docs/todo/[domain]/` - PRD 문서 존재
- [ ] `docs/spec/[domain]/` - 설계 문서 존재
- [ ] `docs/complete/` - 완료 보고서 업데이트됨
- [ ] complete 문서의 참조 경로가 새 구조로 업데이트됨
- [ ] 계획서/일회성 분석 파일 삭제됨
- [ ] 중복 내용 통합됨
- [ ] 원본 디렉토리 삭제됨
- [ ] summary.md 업데이트됨

### 시나리오 C: todo 기간별 통폐합

- [ ] `docs/todo/_archive/` 디렉토리 생성됨
- [ ] 월별 아카이브 파일 생성됨 (`YYYY-MM.md`)
- [ ] 완료된 작업은 complete 참조 링크로 전환됨
- [ ] 진행중인 작업은 그대로 유지됨
- [ ] 오늘 날짜 파일은 유지됨
- [ ] 삭제된 원본 파일 목록 기록됨
- [ ] 참조 링크가 올바르게 연결됨 (상대 경로)
- [ ] complete 문서가 없는 작업은 삭제되지 않음

---

## 작업 결과 보고 형식

```markdown
## [도메인명] 문서 정리 완료

### 작업 결과

| 항목 | Before | After | 변화 |
|------|--------|-------|------|
| 파일 수 | N개 | M개 | -X개 (Y% 감소) |
| 디렉토리 | [source] | docs/{todo,spec,complete}/[domain]/ | 4-tier 구조 |
| 중복 제거 | Z개 | 0개 | 완료 |

### 주요 개선 사항
1. 4-Tier 구조 준수
2. 중복 파일 제거
3. 파일 이름 표준화
4. 참조 경로 업데이트

### 검증 완료
- docs/todo/[domain]/ - N개 파일
- docs/spec/[domain]/ - M개 파일
- docs/complete/ - 업데이트됨
- summary.md - 통계 업데이트
- [source] - 삭제 완료
```

---

## 사용 예시

### 금요일 주간 문서 정리 (가장 많이 사용)

```bash
/organize-docs --dry-run        # 1단계: 계획 확인
/organize-docs --backup         # 2단계: 백업 후 실행
```

### 작업 완료 직후 즉시 문서화

```bash
/organize-docs 2025-11-15 --auto    # 빠르게 자동 생성
/organize-docs 2025-11-15 --merge   # 기존 문서에 추가
```

### 과거 누락 작업 일괄 보완

```bash
/organize-docs 2025-11-01 to 2025-11-15 --dry-run    # 확인
/organize-docs 2025-11-01 to 2025-11-15 --backup      # 실행
```

### 기존 문서 아카이브 정리

```bash
/organize-docs docs/legacy-feature --dry-run   # 계획 확인
/organize-docs docs/legacy-feature --backup     # 백업 후 정리
```

### todo 통폐합

```bash
/organize-docs consolidate-todo --dry-run     # 계획 확인
/organize-docs consolidate-todo --backup      # 백업 후 실행
/organize-docs consolidate-todo 2025-11       # 특정 월만
```

### 권장 사용 패턴

**매주 금요일**: `--dry-run` -> `--backup`
**작업 완료 직후**: `$(date +%Y-%m-%d) --auto`
**월말 정리**: 기간 지정 `--dry-run` -> `--backup`

---

## 트러블슈팅

### 디렉토리가 이미 존재하는 경우
기존 파일과 비교하여 충돌 방지. 사용자에게 덮어쓰기 여부 확인.

### 파일이 이미 이동된 경우
중복 작업 방지. 원본 디렉토리만 정리.

### 참조 경로가 복잡한 경우
Grep으로 모든 참조 검색. 일괄 업데이트 후 검증.

---

## 성공 기준

### 시나리오 A
1. 누락 작업 100% 탐지
2. history/complete 문서 자동 생성 (템플릿 기반, Git 정보 정확 반영)
3. summary.md 카테고리 자동 분류 및 통계 정확
4. 4-Tier 구조 강제 준수

### 시나리오 B
1. 4-Tier 구조 완벽 준수
2. 중복 제거 100%
3. 파일명 표준화 (snake_case)
4. 참조 무결성
5. 원본 정리 완료

### 시나리오 C
1. 완료 판단 정확도 (체크박스 + complete 존재)
2. 월별 아카이브 생성
3. 참조 링크 정확성
4. 진행중 작업 보호
5. 용량 80%+ 감소

---

## 주의사항

### 시나리오 A
- Git 커밋 메시지와 실제 변경 내용 대조하여 정확성 검증
- Git 커밋 날짜와 실제 작업 날짜 일치 여부 확인
- Memory에 기록이 있으면 우선 참조
- 자동 생성 후 사용자에게 내용 확인 요청 권장

### 시나리오 B
- 삭제 전 반드시 복사 완료 확인
- 사용자 승인 후 삭제 실행 (CLAUDE.md 규칙 준수)
- 원본 디렉토리 경로 기록 (롤백 대비)

### 시나리오 C
- complete 없는 작업은 절대 삭제 금지
- 오늘 날짜 파일 항상 보호
- 삭제 전 아카이브 먼저 생성

### 공통
- 4-Tier 구조 절대 준수 (todo/spec/history/complete 외 디렉토리 생성 금지, _archive 제외)
- 날짜 형식: YYYY-MM-DD
- 파일명 규칙: `YYYY-MM-DD_[task_name].md`
