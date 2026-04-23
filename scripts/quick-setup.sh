#!/bin/bash
# ============================================================================
# claude-code-guide Quick Setup
# ----------------------------------------------------------------------------
# Claude Code 세션에서 자연어 호출 대상.
#
# 사용법:
#   curl -fsSL https://raw.githubusercontent.com/tomtomjskim/claude-code-guide/main/scripts/quick-setup.sh \
#     | bash -s -- [--profile <name>] [--target <path>] [--dry-run] [--force]
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

set -e

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
    --help|-h)
      sed -n '/^# =\{70,\}$/,/^# =\{70,\}$/p' "$0" | head -25 | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) echo "❌ Unknown arg: $1. Use --help." >&2; exit 1 ;;
  esac
done

# -----------------------------
# 유틸
# -----------------------------
log() { echo "$@" >&2; }
run() {
  if [ "$DRY_RUN" = "1" ]; then
    echo "[DRY-RUN] $*"
  else
    eval "$@"
  fi
}

cleanup() {
  [ -n "$TMPDIR" ] && [ -d "$TMPDIR" ] && rm -rf "$TMPDIR"
}
trap cleanup EXIT

# -----------------------------
# 타겟 경로 검증
# -----------------------------
if [ ! -d "$TARGET" ]; then
  echo "❌ Target directory not found: $TARGET" >&2
  echo "   Hint: --target /path/to/project 또는 해당 디렉토리에서 실행" >&2
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

  [ -f "$TARGET/package.json" ] && stacks+=("nodejs")
  if [ -f "$TARGET/tsconfig.json" ] || grep -q '"typescript"' "$TARGET/package.json" 2>/dev/null; then
    stacks+=("typescript")
  fi
  [ -f "$TARGET/pyproject.toml" ] || [ -f "$TARGET/requirements.txt" ] || [ -f "$TARGET/setup.py" ] && stacks+=("python")
  [ -f "$TARGET/go.mod" ] && stacks+=("go")
  [ -f "$TARGET/composer.json" ] && stacks+=("php")
  [ -f "$TARGET/Cargo.toml" ] && stacks+=("rust")
  [ -f "$TARGET/pom.xml" ] || [ -f "$TARGET/build.gradle" ] && stacks+=("java")

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
log "📦 Cloning claude-code-guide..."
run "git clone --depth 1 \"$REPO_URL\" \"$TMPDIR/ccg\" 2>&1 | tail -3"

if [ "$DRY_RUN" = "0" ] && [ ! -d "$TMPDIR/ccg" ]; then
  echo "❌ Clone 실패. 네트워크 확인." >&2
  exit 1
fi

CCG="$TMPDIR/ccg"

# -----------------------------
# 프로파일별 스킬/훅 설치
# -----------------------------
SKILLS_FLAGS=""
HOOKS_FLAGS=""
INSTALL_TEAM=0
VALIDATE_AFTER=0

case "$PROFILE" in
  solo)
    SKILLS_FLAGS="--skills dispatch,stage,check-code,reflect,flow"
    HOOKS_FLAGS="--preset minimal"
    ;;
  team)
    # 전체 설치 (기본)
    HOOKS_FLAGS=""
    ;;
  enterprise)
    SKILLS_FLAGS="--team"
    HOOKS_FLAGS=""
    INSTALL_TEAM=1
    VALIDATE_AFTER=1
    ;;
  review-only)
    SKILLS_FLAGS="--skills check-code,check-spec,qa-test"
    HOOKS_FLAGS="--preset minimal"
    ;;
  *)
    echo "❌ Unknown profile: $PROFILE" >&2
    echo "   Available: solo, team, enterprise, review-only, auto" >&2
    exit 1
    ;;
esac

[ "$FORCE" = "1" ] && SKILLS_FLAGS="$SKILLS_FLAGS --force"
[ "$FORCE" = "1" ] && HOOKS_FLAGS="$HOOKS_FLAGS --force"

log ""
log "⚙️  Installing skills ($PROFILE profile)..."
run "bash \"$CCG/scripts/install-skills.sh\" $SKILLS_FLAGS \"$TARGET\""

log ""
log "🔒 Installing hooks..."
run "bash \"$CCG/scripts/install-hooks.sh\" $HOOKS_FLAGS \"$TARGET\""

# -----------------------------
# enterprise: 팀 시스템 검증
# -----------------------------
if [ "$VALIDATE_AFTER" = "1" ] && [ "$DRY_RUN" = "0" ]; then
  log ""
  log "🔍 Validating team system..."
  bash "$CCG/scripts/validate-system.sh" 2>&1 | tail -5 || true
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
