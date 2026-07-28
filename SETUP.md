# Setup Guide — Claude Code가 읽고 수행하는 대화형 설치 지침

<!-- CLAUDE-SETUP-GUIDE v1 -->

**저장소**: https://github.com/tomtomjskim/claude-code-guide  
**이 파일 raw URL 형식**: https://raw.githubusercontent.com/tomtomjskim/claude-code-guide/<reviewed-full-commit>/SETUP.md
**원라이너 raw URL 형식**: https://raw.githubusercontent.com/tomtomjskim/claude-code-guide/<reviewed-full-commit>/scripts/quick-setup.sh

---

## 이 파일의 목적

`claude-code-guide`를 어떤 프로젝트에든 **자연어 한 줄로 도입**하기 위한 머신 가독(machine-readable) 설치 가이드. Claude Code가 이 파일을 읽으면 아래 Wizard를 대화형으로 실행한다.

---

## Zero-context Bootstrap (새 프로젝트에서 첫 호출)

사용자가 claude-code-guide가 전혀 설치돼 있지 않은 프로젝트에서 Claude Code 세션을 시작했다면, 아래 3가지 진입 경로 중 하나를 택한다.

### 진입 1: 검토된 ref 원라이너

터미널에서:
```bash
CCG_REF="<reviewed-full-40-character-commit>"
curl -fsSL "https://raw.githubusercontent.com/tomtomjskim/claude-code-guide/$CCG_REF/scripts/quick-setup.sh" \
  | bash -s -- --ref "$CCG_REF" --dry-run
# 출력 검토 후 --dry-run을 제거해 적용
```

### 진입 2: Claude Code에 복사-붙여넣기 (대화형)

Claude Code 세션에서 아래를 그대로 붙여넣기:

```
다음 GitHub 저장소의 자동 셋업 스크립트로 이 프로젝트를 셋업해줘:
https://github.com/tomtomjskim/claude-code-guide

실행 방법:
CCG_REF="<reviewed-full-40-character-commit>"
curl -fsSL "https://raw.githubusercontent.com/tomtomjskim/claude-code-guide/$CCG_REF/scripts/quick-setup.sh" | bash -s -- --ref "$CCG_REF" --dry-run

SETUP.md wizard에 따라 프로젝트 분석 → profile 추천 → dry-run 검토 → 확인 후 실행.
```

Claude가 SETUP.md(또는 quick-setup.sh)를 WebFetch/실행하여 아래 Wizard Steps 진행.

### 진입 3: 전역 `/setup-wizard` 스킬 선설치 (한 번만)

검토된 checkout에서 한 번 실행:
```bash
git clone https://github.com/tomtomjskim/claude-code-guide <local-guide-path>
git -C <local-guide-path> checkout --detach <reviewed-tag-or-full-commit>
bash <local-guide-path>/scripts/install-skills.sh --skills setup-wizard ~/
```

이후 모든 프로젝트에서:
```
/setup-wizard
```

---

## 사용자 진입 (자연어 — 이미 설치됨 또는 저장소 지식 보유 시)

사용자가 Claude Code 세션에서 다음 중 하나를 타이핑:

- "claude-code-guide 설치해줘"
- "claude-code-guide setup"
- "이 프로젝트에 PDARR 워크플로우 적용"
- "@claude-code-guide 적용"

Claude Code는 이 `SETUP.md`(또는 `scripts/quick-setup.sh`)를 읽고 **아래 Wizard**를 진행한다.

**Claude가 저장소 위치를 모르는 경우**: 사용자에게 GitHub URL을 요청하거나, `~/.claude/CLAUDE.md` memory에 등록된 저장소 링크 활용 (README.md의 "Claude Code Memory에 북마크" 섹션 참조).

---

## Wizard Steps

### Step 1: 프로젝트 분석 (Claude가 자동 수행)

```bash
# (a) 스택 감지
[ -f package.json ] && echo "Node.js"
[ -f tsconfig.json ] && echo "TypeScript"
[ -f pyproject.toml ] && echo "Python"
[ -f go.mod ] && echo "Go"
[ -f composer.json ] && echo "PHP"
[ -f Cargo.toml ] && echo "Rust"

# (b) 규모 감지
CONTRIB=$(git log --format='%an' 2>/dev/null | sort -u | wc -l)
SRC_COUNT=$(find . -type f \( -name "*.ts" -o -name "*.py" -o -name "*.go" \
  -o -name "*.php" -o -name "*.js" -o -name "*.rs" \) \
  -not -path "*/node_modules/*" -not -path "*/.git/*" | wc -l)

# (c) 기존 설치 체크
[ -d .claude/skills ] && ls .claude/skills/ | wc -l
```

### Step 2: 프로파일 자동 추천

| 기여자 | 소스 파일 | 추천 프로파일 | 스킬 수 | 설치 시간 |
|-------|----------|--------------|--------|----------|
| 1 | <50 | **`solo`** | 5 (dispatch/stage/check-code/reflect/flow) | 1분 |
| 2-5 | 50-500 | **`team`** | 19 (전체 PDARR) | 2분 |
| 5+ | 500+ | **`enterprise`** | 19 + 팀 시스템(`--team`) | 3분 + validate |
| 기존 프로젝트 리뷰 도입만 | - | **`review-only`** | 3 (check-code/check-spec/qa-test) | 1분 |

### Step 3: 사용자 확인 (Claude가 대화로)

예시 대화:

```
Claude: 🔍 프로젝트 분석 결과:
  - 스택: Node.js + TypeScript
  - 기여자: 3명
  - 소스 파일: 180개
  → 추천 프로파일: **team**

  설치 내용:
  - 19개 PDARR 스킬 (/dispatch, /prd, /analyze, /spec, /run, /check-code 등)
  - 4개 Safety hooks (guard-agent, safety-careful, safety-freeze, audit-agent)
  - settings.local.json에 hooks 등록

  진행할까요? (y/n/other)
  - y: 그대로 실행
  - n: 프로파일 직접 선택 (solo/team/enterprise/review-only)
  - other: 개별 스킬 선택

User: y
```

### Step 4: 설치 실행 (`scripts/quick-setup.sh` 호출)

**원라이너 (원격):**
```bash
CCG_REF="<reviewed-full-40-character-commit>"
curl -fsSL "https://raw.githubusercontent.com/tomtomjskim/claude-code-guide/$CCG_REF/scripts/quick-setup.sh" \
  | bash -s -- --ref "$CCG_REF" --profile team --dry-run
```

dry-run 출력과 source ref를 확인한 뒤에만 `--dry-run`을 제거한다. 원격 apply는
full 40-character commit SHA만 허용하며 branch, tag, short SHA는 preview only다.

**옵션:**
- `--profile <solo|team|enterprise|review-only|auto>` — 프로파일 명시 (기본: auto)
- `--target <path>` — 설치 대상 프로젝트 경로 (기본: `$PWD` 또는 `$CLAUDE_PROJECT_PATH`)
- `--ref <full-commit>` — 원격 apply source를 검토된 40자 commit SHA로 고정
- `--dry-run` — 실제 변경 없이 실행 명령만 출력
- `--force` — 기존 설치 덮어쓰기
- `--skip-stack` — 스택별 CUSTOMIZE 안내 생략

**Bash -x 로 실제 수행 명령 확인:**
```bash
# 예: team profile로 /my-project에 설치
curl ... | bash -s -- --profile team --target /my-project
```

### Step 5: 스택별 CUSTOMIZE 자동 교체 (선택)

감지된 스택이 PHP/MySQL이 아니면 Claude가 다음 제안:

```
Claude: 감지 스택 "TypeScript/Node.js".
  skills/check-code/SKILL.md의 <!-- CUSTOMIZE --> 블록은 PHP/MySQL 기본 예시입니다.
  references/stack-examples.md의 TypeScript 섹션으로 교체할까요? (y/n)

User: y

Claude: [9개 CUSTOMIZE 블록의 PHP 예시를 TypeScript 예시로 치환]
```

**references/stack-examples.md 사용 가능 섹션:**
- File Discovery / Syntax Check Commands / Required Structure
- Language Version Compatibility / Security Patterns / API Call Patterns
- UI Dialog Patterns / Style Rules / SQL Security Pattern / Reference Documents

각 섹션은 PHP/MySQL(기본)·React/TypeScript·Python/Django·Node.js/TypeScript 예시를 포함.

### Step 6: 설치 검증

```bash
# 공통
ls .claude/skills/ | wc -l
cat .claude/settings.local.json

CLAUDE_HOME="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
# enterprise만
bash "$CLAUDE_HOME/team/scripts/validate-system.sh" \
  --project <target> \
  --claude-home "$CLAUDE_HOME"
# 기대: Errors 0, Warnings 0, Checks 19 categories

# quick-setup 설치 상태
bash scripts/manage-install.sh doctor --target <target> --json
```

### Step 7: 다음 단계 안내

프로파일별 첫 실행 안내:

**solo:**
- `/dispatch "버그 수정"` → 라우팅 확인
- `/check-code <파일>` → 리뷰 테스트
- `/stage` → 커밋 스테이징

**team:**
- `/dispatch "기능 추가"` → PDARR 진입
- `/prd <기능명>` → `/analyze` → `/spec` → `/run` → `/check-code` → `/stage` 풀 플로우
- CUSTOMIZE 블록 교체 완료했으면 바로 프로덕션 사용 가능

**enterprise:**
- validate Errors 0 확인
- `agents.yaml`, `prompts/`, `workflows/` 검토
- `/workflow <기능명>` → 팀 모드 첫 실행

**review-only:**
- 기존 코드에 `/check-code <파일>` 실행
- PR 훅 연동: `.claude/settings.local.json`의 `event-review-trigger.reference.sh` 확인

---

## 프로파일 정의 (canonical)

### solo — 1인 개발 (5 스킬, minimal hooks = 2)

```bash
bash scripts/install-skills.sh --skills dispatch,stage,check-code,reflect,flow <target>
bash scripts/install-hooks.sh --preset minimal <target>
```

- **포함 hooks**: `guard-agent` + `safety-careful` (2개)
- **적합**: 개인 프로젝트, 사이드 프로젝트, 학습용
- **제외**: 팀 워크플로우(PRD, Spec, Workflow), E2E QA 자동화, `safety-freeze` + `audit-agent`

### team — 2-5인 팀 (19 스킬, standard hooks) **기본값**

```bash
bash scripts/install-skills.sh <target>
bash scripts/install-hooks.sh <target>
```

- **적합**: 일반 프로덕션, 중형 팀, PDARR 풀 워크플로우
- **포함**: 19 스킬 + guard-agent/safety-careful/safety-freeze/audit-agent hooks

### enterprise — 대형/프로덕션 (19 스킬 + 팀 시스템)

```bash
bash scripts/install-skills.sh --team <target>
bash scripts/install-hooks.sh <target>
CLAUDE_HOME="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
bash "$CLAUDE_HOME/team/scripts/validate-system.sh" \
  --project <target> \
  --claude-home "$CLAUDE_HOME"
```

- **추가**: `~/.claude/team/`에 agents.yaml, prompts/, workflows/, context/ 설치
- **적합**: 16 에이전트 병렬 팀 사용, Handoff Protocol, Tiebreaker, Model Routing
- **검증**: validate-system.sh 통과 필수

### review-only — 리뷰 도입 (3 스킬, minimal hooks = 2)

```bash
bash scripts/install-skills.sh --skills check-code,check-spec,qa-test <target>
bash scripts/install-hooks.sh --preset minimal <target>
```

- **포함 hooks**: `guard-agent` + `safety-careful` (2개)
- **적합**: 기존 프로젝트에 리뷰 시스템만 추가, 워크플로우는 기존 유지
- **제외**: dispatch/prd/analyze/spec/run 등 워크플로우 스킬

---

## Claude Code가 이 파일을 따라가는 방식

1. 사용자가 `claude-code-guide 설치해줘` 등 자연어 입력
2. Claude가 WebFetch 또는 로컬 clone된 `SETUP.md`를 읽음
3. **Step 1**의 Bash 명령을 실행하여 프로젝트 분석
4. **Step 2** 매트릭스로 프로파일 추천
5. **Step 3** 사용자 확인 대화
6. **Step 4** 검토된 ref의 `quick-setup.sh`를 dry-run 후 호출
7. **Step 5** 스택별 CUSTOMIZE 제안 (선택)
8. **Step 6-7** 검증 + 다음 단계 안내

**Claude Code는 위 단계를 기계적으로 수행하면 된다.** 각 Step의 Bash 블록을 그대로 실행, 결과를 해석하여 다음 Step으로 진행.

---

## 트러블슈팅

### "이미 설치돼 있다"고 나오는 경우
- `.claude/skills/` 스킬 파일이 존재. `--force`로 덮어쓰거나, 개별 스킬만 추가 설치

### validate에서 Errors 6 보고
- PyYAML env baseline (`agents.yaml`, `failure-policy.yaml` 등 기존 baseline). 이번 설치와 무관. **정상**

### Hooks가 작동 안 함
- `.claude/settings.local.json`에 `hooks` 블록 확인
- `hooks/*.sh` 실행 권한 확인 (`chmod +x`)
- Claude Code 재시작 (hooks는 세션 시작 시 로드)

### 스킬이 인식 안 됨
- Claude Code 설정에서 `.claude/skills/` 경로 확인
- 슬래시 커맨드 자동완성이 나오는지 테스트
- 필요 시 `bash scripts/install-skills.sh --force <target>` 재실행

---

## 관련 문서

- [`README.md`](README.md) — 전체 repo 개요
- [`docs/v4-changelog.md`](docs/v4-changelog.md) — v4.0 릴리즈 노트
- [`QUICKSTART.md`](QUICKSTART.md) — 실전 활용 패턴
- [`CLAUDE.md`](CLAUDE.md) — 본 레포의 Claude Code 규칙 (예시)
- [`skills/README.md`](skills/README.md) — 19 스킬 인덱스
- [`hooks/README.md`](hooks/README.md) — Hook 보일러플레이트 가이드

---

## 버전

이 `SETUP.md`는 claude-code-guide v4.5 이후 기준.
사용할 ref는 release note와 `git tag -l` 또는 명시 commit을 함께 검토해 선택한다.
