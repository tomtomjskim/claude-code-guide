#!/bin/bash
# ============================================================================
# claude-code-guide Quick Setup
# ----------------------------------------------------------------------------
# Claude Code 세션에서 자연어 호출 대상.
#
# 사용법:
#   CCG_REF="<reviewed-full-40-character-commit>"
#   curl -fsSL "https://raw.githubusercontent.com/tomtomjskim/claude-code-guide/$CCG_REF/scripts/quick-setup.sh" \
#     | bash -s -- --ref "$CCG_REF" [--profile <name>] [--target <path>] [--dry-run] [--force]
#
#   로컬 clone 후:
#   bash scripts/quick-setup.sh --profile team --target /path/to/project
#
# 프로파일:
#   solo         1인 개발, 핵심 5 스킬 + minimal hooks
#   team         2-5인 팀, 전체 18 스킬 + 전체 hooks (기본값 — auto 감지 시)
#   enterprise   대형/프로덕션, team + 팀 시스템(--team) + validate
#   review-only  리뷰 도입용, check-code/check-spec/qa-test 3 스킬만
#   auto         프로젝트 분석 후 자동 추천 (기본값)
#
# ============================================================================

set -Eeo pipefail
# pipefail: pipe 안 어떤 명령이라도 fail 하면 전체 fail (P2-H4)
# 예: `git clone ... | tail -3` 에서 git clone 실패 시 tail이 0 반환해도 잡힘

# -----------------------------
# 기본값
# -----------------------------
PROFILE="auto"
TARGET="${CLAUDE_PROJECT_PATH:-$PWD}"
DRY_RUN=0
FORCE=0
SKIP_STACK_CUSTOMIZE=0
REPO_URL="https://github.com/tomtomjskim/claude-code-guide"
TMPDIR=""
PRESERVE_TMPDIR=0
INSTALL_TRANSACTION_ACTIVE=0
INSTALL_LOCK_HELD=0
INSTALL_LOCK_DIR=""
ROLLBACK_ATTEMPTED=0
SOURCE_OVERRIDE="${CLAUDE_CODE_GUIDE_SOURCE:-}"
SOURCE_REF="${CLAUDE_CODE_GUIDE_REF:-main}"
SOURCE_REVISION=""

if [ -z "$SOURCE_OVERRIDE" ] \
  && [ -n "${BASH_SOURCE[0]:-}" ] \
  && [ -f "${BASH_SOURCE[0]}" ]; then
  LOCAL_SOURCE_CANDIDATE="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/.." 2>/dev/null && pwd || true
  )"
  if [ -n "$LOCAL_SOURCE_CANDIDATE" ] \
    && [ -f "$LOCAL_SOURCE_CANDIDATE/scripts/install_state.py" ]; then
    SOURCE_OVERRIDE="$LOCAL_SOURCE_CANDIDATE"
  fi
fi

# -----------------------------
# 인자 파싱
# -----------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile) PROFILE="$2"; shift 2 ;;
    --target)  TARGET="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --force)   FORCE=1; shift ;;
    --skip-stack) SKIP_STACK_CUSTOMIZE=1; shift ;;
    --ref) SOURCE_REF="$2"; shift 2 ;;
    --help|-h)
      # P2-L1: 헤더 sed 의존 제거 — 직접 inline 출력
      cat <<'HELP'
claude-code-guide Quick Setup

Usage:
  CCG_REF="<reviewed-full-40-character-commit>"
  curl -fsSL "https://raw.githubusercontent.com/tomtomjskim/claude-code-guide/$CCG_REF/scripts/quick-setup.sh" \
    | bash -s -- --ref "$CCG_REF" [--profile <name>] [--target <path>] [--dry-run] [--force] [--skip-stack]

  로컬 clone 후:
    bash scripts/quick-setup.sh --profile team --target /path/to/project

Profiles:
  solo         1인 개발, 핵심 5 스킬 + minimal hooks (guard+careful=2)
  team         2-5인 팀, 19 스킬 + standard hooks (4개) — auto 감지 기본
  enterprise   대형/프로덕션, team + 팀 시스템(--team) + validate
  review-only  리뷰 도입용, check-code/check-spec/qa-test 3 스킬만
  auto         프로젝트 분석 후 자동 추천 (default)

Options:
  --profile <name>     프로파일 선택 (solo|team|enterprise|review-only|auto)
  --target <path>      설치 대상 (default: $PWD)
  --ref <value>        원격 apply는 검토된 full 40-character commit 필수
  --dry-run            실행 명령만 출력, 실제 변경 없음
  --force              기존 설치 덮어쓰기
  --skip-stack         스택별 CUSTOMIZE 안내 생략

GitHub: https://github.com/tomtomjskim/claude-code-guide
HELP
      exit 0 ;;
    *) echo "❌ Unknown arg: $1. Use --help." >&2; exit 1 ;;
  esac
done

# -----------------------------
# 유틸
# -----------------------------
log() { echo "$@" >&2; }
# run(): 실행 또는 dry-run 출력 (P2-H3 — eval 제거, 배열 처리)
# 사용: run cmd arg1 arg2 ...
#   - DRY_RUN=1: 명령 echo만 (한 줄)
#   - DRY_RUN=0: 명령 실제 실행 (eval 안 씀, 직접 invoke)
# 외부 사용자 ingress 안전성 확보 — 메타문자/공백 인자 안전
run() {
  if [ "$DRY_RUN" = "1" ]; then
    # 인자 표시용으로만 join
    echo "[DRY-RUN] $*"
  else
    "$@"
  fi
}

cleanup() {
  if [ "$INSTALL_LOCK_HELD" = "1" ] && [ -n "$INSTALL_LOCK_DIR" ]; then
    rm -f "$INSTALL_LOCK_DIR/pid"
    if ! rmdir "$INSTALL_LOCK_DIR" 2>/dev/null; then
      log "⚠️  Install lock could not be removed: $INSTALL_LOCK_DIR"
    fi
    INSTALL_LOCK_HELD=0
  fi
  if [ "$PRESERVE_TMPDIR" = "1" ]; then
    log "⚠️  Recovery snapshot preserved at: $TMPDIR"
  elif [ -n "$TMPDIR" ] && [ -d "$TMPDIR" ]; then
    rm -rf "$TMPDIR"
  fi
}

rollback_active_install() {
  local rollback_status=0
  if [ "$ROLLBACK_ATTEMPTED" = "1" ]; then
    return 0
  fi
  ROLLBACK_ATTEMPTED=1
  set +e
  if [ "$INSTALL_TRANSACTION_ACTIVE" = "1" ]; then
    log ""
    log "↩️  Install interrupted; restoring declared managed files..."
    python3 "$CCG/scripts/install_state.py" abort \
      --target "$TARGET" \
      --snapshot "$STATE_SNAPSHOT" \
      --claude-home "$CLAUDE_HOME" \
      "${STATE_HOME_FLAGS[@]}"
    rollback_status=$?
    if [ "$rollback_status" -ne 0 ]; then
      PRESERVE_TMPDIR=1
      log "❌ Automatic rollback failed (exit $rollback_status)."
    else
      log "✅ Partial install rolled back."
    fi
    INSTALL_TRANSACTION_ACTIVE=0
  fi
  return "$rollback_status"
}

finish_on_exit() {
  local original_status=$?
  trap - EXIT ERR HUP INT TERM
  if [ "$INSTALL_TRANSACTION_ACTIVE" = "1" ]; then
    rollback_active_install || true
    [ "$original_status" -eq 0 ] && original_status=1
  fi
  cleanup
  exit "$original_status"
}

trap finish_on_exit EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

# -----------------------------
# 타겟 경로 검증
# -----------------------------
if [ ! -d "$TARGET" ]; then
  echo "❌ Target directory not found: $TARGET" >&2
  echo "   Hint: --target /path/to/project 또는 해당 디렉토리에서 실행" >&2
  exit 1
fi
if [ -L "$TARGET" ]; then
  echo "❌ Target directory must not be a symlink: $TARGET" >&2
  exit 1
fi
TARGET="$(cd "$TARGET" && pwd)"

log "📂 Target project: $TARGET"

# -----------------------------
# 이미 설치돼 있는지 감지
# -----------------------------
if [ -d "$TARGET/.claude/skills" ] && [ "$FORCE" = "0" ]; then
  EXISTING=$(ls -d "$TARGET/.claude/skills/"*/ 2>/dev/null | wc -l | tr -d ' ')
  if [ "$EXISTING" -gt "0" ]; then
    log "ℹ️  기존 설치 감지 ($EXISTING 스킬 있음)."
    log "   덮어쓰려면 --force 추가, 추가 설치는 그대로 진행."
  fi
fi

# -----------------------------
# 프로파일 자동 감지
# -----------------------------
detect_profile() {
  local contrib=1
  local src_files=0

  # git 기여자
  if [ -d "$TARGET/.git" ]; then
    contrib=$(cd "$TARGET" && git log --format='%an' 2>/dev/null | sort -u | wc -l | tr -d ' ')
    [ "$contrib" = "0" ] && contrib=1
  fi

  # 소스 파일 수 (주요 언어)
  src_files=$(find "$TARGET" -type f \
    \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.py" \
       -o -name "*.go" -o -name "*.php" -o -name "*.rs" -o -name "*.java" \
       -o -name "*.kt" -o -name "*.swift" \) \
    -not -path "*/node_modules/*" -not -path "*/.git/*" -not -path "*/dist/*" \
    -not -path "*/build/*" -not -path "*/vendor/*" 2>/dev/null | wc -l | tr -d ' ')

  log "  기여자: ${contrib}명 / 소스 파일: ${src_files}"

  if [ "$contrib" -le "1" ] && [ "$src_files" -lt "50" ]; then
    echo "solo"
  elif [ "$contrib" -le "5" ] && [ "$src_files" -lt "500" ]; then
    echo "team"
  else
    echo "enterprise"
  fi
}

# -----------------------------
# 스택 감지
# -----------------------------
detect_stack() {
  local stacks=()

  # 단순 시그널 (P2-L4 — 명시적 if/then 구조로 우선순위 모호성 제거)
  [ -f "$TARGET/package.json" ] && stacks+=("nodejs")
  if [ -f "$TARGET/tsconfig.json" ] || grep -q '"typescript"' "$TARGET/package.json" 2>/dev/null; then
    stacks+=("typescript")
  fi
  if [ -f "$TARGET/pyproject.toml" ] || [ -f "$TARGET/requirements.txt" ] || [ -f "$TARGET/setup.py" ]; then
    stacks+=("python")
  fi
  [ -f "$TARGET/go.mod" ] && stacks+=("go")
  [ -f "$TARGET/composer.json" ] && stacks+=("php")
  [ -f "$TARGET/Cargo.toml" ] && stacks+=("rust")
  if [ -f "$TARGET/pom.xml" ] || [ -f "$TARGET/build.gradle" ]; then
    stacks+=("java")
  fi

  if [ ${#stacks[@]} -eq 0 ]; then
    echo "unknown"
  else
    (IFS=,; echo "${stacks[*]}")
  fi
}

STACK=$(detect_stack)
log "  스택: $STACK"

if [ "$PROFILE" = "auto" ]; then
  PROFILE=$(detect_profile)
  log "🔍 Auto profile → $PROFILE"
else
  log "  Profile: $PROFILE (수동 지정)"
fi

# -----------------------------
# Repo clone
# -----------------------------
TMPDIR=$(mktemp -d)
log ""
if [ -n "$SOURCE_OVERRIDE" ]; then
  if [ ! -f "$SOURCE_OVERRIDE/scripts/install-skills.sh" ]; then
    echo "❌ Invalid CLAUDE_CODE_GUIDE_SOURCE: $SOURCE_OVERRIDE" >&2
    exit 1
  fi
  CCG="$(cd "$SOURCE_OVERRIDE" && pwd)"
  log "📦 Using local claude-code-guide source: $CCG"
else
  log "📦 Cloning claude-code-guide..."
  if [[ "$SOURCE_REF" == -* ]] || [[ "$SOURCE_REF" =~ [[:space:]] ]]; then
    echo "❌ Invalid source ref: $SOURCE_REF" >&2
    exit 1
  fi
  if [ "$DRY_RUN" = "0" ] && ! [[ "$SOURCE_REF" =~ ^[0-9a-fA-F]{40}$ ]]; then
    echo "❌ Remote apply requires a full 40-character commit SHA." >&2
    echo "   Branches, tags, and short SHAs are preview only; resolve and review the commit first." >&2
    exit 1
  fi
  if [ "$DRY_RUN" = "1" ] && ! [[ "$SOURCE_REF" =~ ^[0-9a-fA-F]{40}$ ]]; then
    log "⚠️  Named or short ref preview only: $SOURCE_REF"
  fi
  if [[ "$SOURCE_REF" =~ ^[0-9a-fA-F]{40}$ ]]; then
    if [ "$DRY_RUN" = "1" ]; then
      echo "[DRY-RUN] git clone --filter=blob:none --no-checkout \"$REPO_URL\" \"$TMPDIR/ccg\""
      echo "[DRY-RUN] git -C \"$TMPDIR/ccg\" fetch --depth 1 origin \"$SOURCE_REF\""
      echo "[DRY-RUN] git -C \"$TMPDIR/ccg\" checkout --detach FETCH_HEAD"
      echo "[DRY-RUN] verify checked-out HEAD equals $SOURCE_REF"
    else
      git clone --filter=blob:none --no-checkout "$REPO_URL" "$TMPDIR/ccg"
      git -C "$TMPDIR/ccg" fetch --depth 1 origin "$SOURCE_REF"
      git -C "$TMPDIR/ccg" checkout --detach FETCH_HEAD
      SOURCE_REVISION="$(git -C "$TMPDIR/ccg" rev-parse --verify HEAD)"
      REQUESTED_REVISION="$(printf '%s' "$SOURCE_REF" | tr '[:upper:]' '[:lower:]')"
      RESOLVED_REVISION="$(printf '%s' "$SOURCE_REVISION" | tr '[:upper:]' '[:lower:]')"
      if [ "$RESOLVED_REVISION" != "$REQUESTED_REVISION" ]; then
        echo "❌ Checked-out commit does not match requested SHA." >&2
        exit 1
      fi
    fi
  else
    echo "[DRY-RUN] git clone --depth 1 --branch $SOURCE_REF \"$REPO_URL\" \"$TMPDIR/ccg\""
  fi

  if [ "$DRY_RUN" = "0" ] && [ ! -d "$TMPDIR/ccg" ]; then
    echo "❌ Clone 실패. 네트워크 확인." >&2
    exit 1
  fi

  CCG="$TMPDIR/ccg"
fi

if [ -z "$SOURCE_REVISION" ] && [ "$DRY_RUN" = "0" ]; then
  if git -C "$CCG" rev-parse --verify HEAD >/dev/null 2>&1; then
    SOURCE_REVISION="$(git -C "$CCG" rev-parse --verify HEAD)"
    if [ -n "$(GIT_OPTIONAL_LOCKS=0 git -C "$CCG" status --porcelain --untracked-files=normal)" ]; then
      SOURCE_REVISION="${SOURCE_REVISION}+dirty"
    fi
  else
    SOURCE_REVISION="local-unversioned"
  fi
fi

# -----------------------------
# 프로파일별 스킬/훅 설치 (P2-H3 — 배열 기반, eval 제거)
# -----------------------------
SKILLS_FLAGS=()
HOOKS_FLAGS=()
INSTALL_TEAM=0
VALIDATE_AFTER=0

case "$PROFILE" in
  solo)
    SKILLS_FLAGS=(--skills dispatch,stage,check-code,reflect,flow)
    HOOKS_FLAGS=(--preset minimal)
    ;;
  team)
    # 전체 설치 (기본 — 빈 플래그)
    ;;
  enterprise)
    SKILLS_FLAGS=(--team)
    INSTALL_TEAM=1
    VALIDATE_AFTER=1
    ;;
  review-only)
    SKILLS_FLAGS=(--skills check-code,check-spec,qa-test)
    HOOKS_FLAGS=(--preset minimal)
    ;;
  *)
    echo "❌ Unknown profile: $PROFILE" >&2
    echo "   Available: solo, team, enterprise, review-only, auto" >&2
    exit 1
    ;;
esac

[ "$FORCE" = "1" ] && SKILLS_FLAGS+=(--force)
[ "$FORCE" = "1" ] && HOOKS_FLAGS+=(--force)

STATE_SNAPSHOT="$TMPDIR/install-state-before"
CLAUDE_HOME="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
STATE_HOME_FLAGS=()
[ "$INSTALL_TEAM" = "1" ] && STATE_HOME_FLAGS+=(--include-home)
STATE_SOURCE_FLAGS=(--source-revision "$SOURCE_REVISION")
[ "$FORCE" = "1" ] && STATE_SOURCE_FLAGS+=(--allow-source-change)

if [ "$DRY_RUN" = "0" ]; then
  if [ -L "$TARGET/.claude" ]; then
    echo "❌ Managed root is a symlink: $TARGET/.claude" >&2
    exit 1
  fi
  mkdir -p "$TARGET/.claude"
  INSTALL_LOCK_DIR="$TARGET/.claude/.claude-code-guide-install.lock"
  if ! mkdir "$INSTALL_LOCK_DIR" 2>/dev/null; then
    echo "❌ Existing install lock blocks this operation: $INSTALL_LOCK_DIR" >&2
    exit 1
  fi
  printf '%s\n' "$$" > "$INSTALL_LOCK_DIR/pid"
  INSTALL_LOCK_HELD=1

  python3 "$CCG/scripts/install_state.py" begin \
    --target "$TARGET" \
    --output "$STATE_SNAPSHOT" \
    --source "$CCG" \
    --profile "$PROFILE" \
    "${STATE_SOURCE_FLAGS[@]}" \
    --claude-home "$CLAUDE_HOME" \
    "${STATE_HOME_FLAGS[@]}"
  INSTALL_TRANSACTION_ACTIVE=1
fi

log ""
log "⚙️  Installing skills ($PROFILE profile)..."
run bash "$CCG/scripts/install-skills.sh" "${SKILLS_FLAGS[@]}" "$TARGET"

log ""
log "🔒 Installing hooks..."
if [ "$DRY_RUN" = "0" ]; then
  export CLAUDE_CODE_GUIDE_TRANSACTION="$STATE_SNAPSHOT"
fi
run bash "$CCG/scripts/install-hooks.sh" "${HOOKS_FLAGS[@]}" "$TARGET"
unset CLAUDE_CODE_GUIDE_TRANSACTION

if [ "$DRY_RUN" = "0" ]; then
  python3 "$CCG/scripts/install_state.py" finalize \
    --target "$TARGET" \
    --snapshot "$STATE_SNAPSHOT" \
    --profile "$PROFILE" \
    --source-revision "$SOURCE_REVISION" \
    --claude-home "$CLAUDE_HOME" \
    "${STATE_HOME_FLAGS[@]}"
  INSTALL_TRANSACTION_ACTIVE=0
fi

# -----------------------------
# enterprise: 팀 시스템 검증
# 상태를 먼저 확정해 검증 실패 시에도 doctor/uninstall이 가능하게 한다.
# -----------------------------
if [ "$VALIDATE_AFTER" = "1" ] && [ "$DRY_RUN" = "0" ]; then
  log ""
  log "🔍 Validating team system..."
  bash "$CCG/scripts/validate-system.sh" \
    --project "$TARGET" \
    --claude-home "$CLAUDE_HOME" 2>&1 | tail -5
fi

# -----------------------------
# 스택별 CUSTOMIZE 안내
# -----------------------------
if [ "$SKIP_STACK_CUSTOMIZE" = "0" ] && [ "$STACK" != "unknown" ]; then
  log ""
  log "📝 Stack customization hint"
  log "   감지 스택: $STACK"
  log "   check-code/SKILL.md의 <!-- CUSTOMIZE --> 블록은 PHP/MySQL 기본 예시입니다."
  log "   다른 스택 예시 카탈로그: skills/check-code/references/stack-examples.md"
  log "   → 관련 섹션을 복사하여 CUSTOMIZE 블록의 PHP 예시와 교체하세요."
fi

# -----------------------------
# 설치 완료 안내
# -----------------------------
log ""
log "✅ Setup complete — profile: $PROFILE"
log ""
log "다음 단계:"
case "$PROFILE" in
  solo)
    log "  • /dispatch \"버그 수정\" 으로 라우팅 테스트"
    log "  • /check-code <파일경로> 로 리뷰 실행"
    log "  • /stage 로 커밋 스테이징"
    ;;
  team)
    log "  • /dispatch \"기능 추가\" 로 PDARR 진입"
    log "  • /prd <기능명> → /analyze → /spec → /run → /check-code → /stage"
    log "  • 스택 CUSTOMIZE 블록 교체 (30분-1시간)"
    ;;
  enterprise)
    log "  • 팀 시스템 validate 확인 (위 출력 참조, Errors 0 기대)"
    log "  • agents.yaml, prompts/, workflows/ 검토"
    log "  • /workflow <기능명> 으로 팀 모드 테스트"
    ;;
  review-only)
    log "  • 기존 코드에 /check-code <파일경로> 실행"
    log "  • PR 리뷰 통합: /check-spec <모듈> / /qa-test <기능>"
    ;;
esac
log ""
log "전체 문서: $REPO_URL"
log "릴리즈 노트: $REPO_URL/blob/main/docs/v4-changelog.md"
