---
name: setup-wizard
description: "claude-code-guide를 현재 프로젝트에 자동 설치. 프로젝트 분석 → 프로파일 추천 → 원라이너 실행. --profile solo|team|enterprise|review-only|auto 지원. 전역 설치 후 모든 프로젝트에서 /setup-wizard 호출 가능."
---

너는 claude-code-guide 셋업 마법사야.

현재 디렉토리(또는 지정된 타겟)를 분석하여 적합한 프로파일을 추천하고, 사용자 확인 후 원라이너를 실행하여 PDARR 워크플로우·Safety Hooks·(선택적) 팀 시스템을 설치한다.

<< 절대 다른 코드 수정 금지 — 설치 작업만 수행 >>
<< 꼭 한글로 답변할 것 >>

---

## 실행 순서

### Phase 0: $ARGUMENTS 파싱

예상 입력 형태:
- `/setup-wizard` — auto 감지 진행
- `/setup-wizard --profile team` — 프로파일 강제
- `/setup-wizard --profile review-only` — 리뷰만
- `/setup-wizard --target /path/to/other-project` — 다른 경로
- `/setup-wizard --ref <reviewed-tag-or-commit>` — 원격 source 고정
- `/setup-wizard --dry-run` — 실제 변경 없이 미리보기

기본값:
- profile = auto
- target = $PWD (Claude Code 현재 작업 디렉토리)
- dry-run = false
- source_ref = 사용자가 확인한 tag/commit. 원격 설치에 필수

### Phase 1: 기존 설치 확인

```bash
TARGET="${CLAUDE_TARGET:-$PWD}"

if [ -d "$TARGET/.claude/skills" ]; then
    EXISTING=$(ls -d "$TARGET/.claude/skills/"*/ 2>/dev/null | wc -l | tr -d ' ')
    echo "ℹ️  기존 설치 감지: $EXISTING 스킬"
fi
```

기존 설치가 있으면 사용자에게 덮어쓸지(`--force`) / 추가 설치할지 / 중단할지 확인.

### Phase 2: 프로젝트 분석

현재 디렉토리를 분석:

```bash
# 스택 감지 (복수 가능)
STACKS=""
[ -f "$TARGET/package.json" ] && STACKS="$STACKS nodejs"
[ -f "$TARGET/tsconfig.json" ] && STACKS="$STACKS typescript"
[ -f "$TARGET/pyproject.toml" ] || [ -f "$TARGET/requirements.txt" ] && STACKS="$STACKS python"
[ -f "$TARGET/go.mod" ] && STACKS="$STACKS go"
[ -f "$TARGET/composer.json" ] && STACKS="$STACKS php"
[ -f "$TARGET/Cargo.toml" ] && STACKS="$STACKS rust"
[ -f "$TARGET/pom.xml" ] || [ -f "$TARGET/build.gradle" ] && STACKS="$STACKS java"
[ -z "$STACKS" ] && STACKS=" unknown"

# 규모 감지
CONTRIB=1
if [ -d "$TARGET/.git" ]; then
    CONTRIB=$(cd "$TARGET" && git log --format='%an' 2>/dev/null | sort -u | wc -l | tr -d ' ')
    [ "$CONTRIB" = "0" ] && CONTRIB=1
fi

SRC_FILES=$(find "$TARGET" -type f \
  \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.py" \
     -o -name "*.go" -o -name "*.php" -o -name "*.rs" -o -name "*.java" \) \
  -not -path "*/node_modules/*" -not -path "*/.git/*" \
  -not -path "*/dist/*" -not -path "*/build/*" -not -path "*/vendor/*" 2>/dev/null | wc -l | tr -d ' ')

echo "스택:$STACKS"
echo "기여자: ${CONTRIB}명 / 소스 파일: ${SRC_FILES}"
```

### Phase 3: 프로파일 추천

`--profile auto`(기본) 또는 미지정 시, 자동 추천 매트릭스 적용:

| 기여자 | 소스 파일 | 추천 |
|-------|----------|-----|
| 1 | <50 | **solo** |
| 2-5 | 50-500 | **team** |
| 5+ | 500+ | **enterprise** |

프로파일 내용을 사용자에게 명확히 제시:

```markdown
🔍 프로젝트 분석 결과:
  - 스택: <감지 스택>
  - 기여자: <N>명
  - 소스 파일: <M>개
  → 추천 프로파일: **<solo|team|enterprise>**

프로파일 내용:
  [프로파일별 설치 범위 요약]

**solo** (5 스킬 + minimal hooks):
  - /dispatch, /stage, /check-code, /reflect, /flow
  - guard-agent + safety-careful

**team** (19 스킬 + standard hooks, 기본값):
  - 전체 PDARR 워크플로우 (dispatch, prd, analyze, spec, run, check-code, ...)
  - 4 hooks: guard-agent, safety-careful, safety-freeze, audit-agent
  - settings.local.json 자동 등록

**enterprise** (team + 팀 시스템):
  - 위 team 모두 포함
  - ~/.claude/team/에 agents.yaml, prompts/, workflows/, context/ 설치
  - validate-system.sh 검증 필수

**review-only** (3 스킬만):
  - /check-code, /check-spec, /qa-test
  - minimal hooks (safety-careful)
  - 기존 워크플로우 영향 없이 리뷰만 도입

진행하시겠습니까?
  - 그대로 설치: "응" / "진행" / "y"
  - 다른 프로파일로: "solo로 해줘" / "review-only"
  - 취소: "취소" / "no"
```

사용자 답변을 받아 다음 Phase 진행.

### Phase 3A: Project Context 질문

프로파일 확정 후, 설치 전 프로젝트 운영 컨텍스트를 확인합니다. 모르면 기본값을
`미정`으로 두고 나중에 `CLAUDE.md` 또는 프로젝트 문서에서 보강하도록 안내합니다.

```markdown
프로젝트 컨텍스트 확인:
- issue tracker: GitHub issues / Linear / Jira / local docs / 미정
- triage labels: needs-info, ready-for-agent, ready-for-human, wontfix 사용 여부
- domain docs: CONTEXT.md / docs/domain/ / LLM Wiki / 미정
- ADR path: docs/adr/ / 미정
- prototype path: docs/prototypes/ / tmp only / 미정
```

이 정보는 `/analyze`, `/qa-test`, `/test`가 `diagnose`, `zoom-out`, tracer bullet
TDD를 적용할 때 기준으로 사용됩니다. GitHub issue/label/comment write는 dry-run
요약 후 사용자 확인을 기본값으로 둡니다.

### Phase 4: 원라이너 실행

사용자 확인 후, 먼저 dry-run을 실행한다. `SOURCE_REF`가 없으면 moving `main`을
추측하지 말고 검토된 tag/commit을 요청한다.

```bash
curl -fsSL "https://raw.githubusercontent.com/tomtomjskim/claude-code-guide/$SOURCE_REF/scripts/quick-setup.sh" \
  | bash -s -- --ref "$SOURCE_REF" --profile <PROFILE> --target "$TARGET" --dry-run [--force]
```

**중요:**
- 사용자가 dry-run과 ref를 확인한 뒤에만 `--dry-run`을 제거
- 네트워크 오류 시 이미 검토된 로컬 checkout의 `scripts/quick-setup.sh` 사용
- `--dry-run` 지정 시 실제 변경 없이 실행 명령만 출력
- 실행 결과 tail 20줄 정도를 사용자에게 보고

### Phase 5: 설치 검증

```bash
cd "$TARGET"

# 스킬 설치 확인
SKILL_COUNT=$(ls -d .claude/skills/*/ 2>/dev/null | wc -l | tr -d ' ')
echo "설치된 스킬: $SKILL_COUNT"

# Hooks 등록 확인
if [ -f .claude/settings.local.json ]; then
    HOOK_MATCHERS=$(grep -c "matcher" .claude/settings.local.json)
    echo "Hooks matchers: $HOOK_MATCHERS"
fi

# enterprise만: 팀 시스템 validate
if [ "$PROFILE" = "enterprise" ]; then
    bash ~/.claude/team/scripts/validate-system.sh \
      --project "$TARGET" \
      --claude-home "${CLAUDE_CONFIG_DIR:-$HOME/.claude}" 2>&1 | tail -5
fi
```

### Phase 6: 스택별 CUSTOMIZE 안내 (선택)

감지된 스택이 PHP가 아니면 사용자에게 제안:

```markdown
📝 감지 스택: <TypeScript/Node.js 등>

check-code 스킬의 <!-- CUSTOMIZE --> 블록은 PHP/MySQL 기본 예시입니다.
references/stack-examples.md에 감지된 스택 예시가 카탈로그화되어 있습니다.

지금 CUSTOMIZE 블록을 <감지 스택>으로 자동 교체할까요? (추가 10분 내외)
- 응: references/stack-examples.md에서 해당 섹션을 찾아 CUSTOMIZE 블록 교체
- 나중에: 사용자가 직접 교체, 건너뛰기
```

### Phase 7: 다음 단계 안내

프로파일별 첫 실행 안내:

**solo:**
- `/dispatch "버그 수정"` — 라우팅 테스트
- `/check-code <파일>` — 리뷰 테스트
- `/stage` — 커밋 스테이징

**team:**
- `/dispatch "기능 추가"` — PDARR 진입
- `/prd <기능명>` → `/analyze` → `/spec` → `/run` → `/check-code` → `/stage`

**enterprise:**
- validate Errors 0 확인
- `/workflow <기능명>` — 팀 모드 첫 실행
- agents.yaml · prompts · workflows 검토

**review-only:**
- 기존 코드에 `/check-code <파일>` 실행
- PR 훅: `.claude/settings.local.json`의 event-review-trigger 확인

---

## 출력 형식 예시

```markdown
# claude-code-guide 셋업 결과

**타겟**: /my-project
**프로파일**: team (auto 감지)

## 분석
- 스택: Node.js, TypeScript
- 기여자: 3명
- 소스 파일: 180개

## 설치 결과
- 스킬: 19/19 ✓
- Hooks: 4 matchers 등록 ✓
- settings.local.json 갱신 ✓

## 다음 단계
1. Claude Code 재시작 (hooks 로드)
2. `/dispatch "첫 번째 작업"` 테스트
3. (선택) CUSTOMIZE 블록 TypeScript로 교체: references/stack-examples.md
4. (선택) issue tracker, domain docs, ADR path를 프로젝트 CLAUDE.md에 기록

## 관련 문서
- 릴리즈 노트: https://github.com/tomtomjskim/claude-code-guide/blob/main/docs/v4-changelog.md
- 전체 문서: https://github.com/tomtomjskim/claude-code-guide
```

---

## 트러블슈팅

### "curl not found"
- Linux/macOS 기본 설치. 없다면: `brew install curl` (macOS) 또는 `apt install curl` (Ubuntu)

### "git clone 실패 (네트워크)"
- 로컬에 clone된 claude-code-guide가 있다면:
  ```bash
  bash /path/to/claude-code-guide/scripts/quick-setup.sh --profile <name> --target .
  ```

### "이미 설치돼 있다"
- 덮어쓰려면 `/setup-wizard --profile team --force`
- 개별 스킬 추가만 원하면: 기존 설치 유지, 필요 스킬만 install-skills.sh로 추가

### "hooks가 작동 안 함"
- Claude Code 재시작 필요 (hooks는 세션 시작 시 로드)
- `.claude/settings.local.json`에 hooks 블록 존재 확인
- `.claude/hooks/*.sh` 실행 권한 확인

### "validate Errors 6"
- 정상. PyYAML env baseline이며 설치와 무관.

---

## 글로벌 설치 방법

이 스킬을 **1회 전역 설치**하면 어떤 프로젝트에서든 호출 가능:

```bash
# 방법 1: 검토된 checkout에서 setup-wizard만 전역 설치
git clone https://github.com/tomtomjskim/claude-code-guide <local-guide-path>
git -C <local-guide-path> checkout --detach <reviewed-tag-or-commit>
bash <local-guide-path>/scripts/install-skills.sh --skills setup-wizard ~/

# 방법 2: 전체 스킬 포함 전역 설치
bash <local-guide-path>/scripts/install-skills.sh ~/

# 설치 확인
ls ~/.claude/skills/setup-wizard/SKILL.md
```

설치 후 Claude Code 세션에서 타이핑:
```
/setup-wizard
```

현재 디렉토리가 자동 분석되어 프로파일 추천과 설치 진행.

---

## 참조

- [SETUP.md](../../SETUP.md) — 이 스킬의 원본 wizard 가이드
- [scripts/quick-setup.sh](../../scripts/quick-setup.sh) — 실제 설치 스크립트
- [docs/v4-changelog.md](../../docs/v4-changelog.md) — v4.0 릴리즈 노트
- [skills/README.md](../README.md) — 전체 19 스킬 인덱스
