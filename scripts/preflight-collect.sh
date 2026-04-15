#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# preflight-collect.sh — 서브에이전트 위임 전 프로젝트 사전 수집
# 사용법: bash scripts/preflight-collect.sh [프로젝트경로]
# 출력  : 에이전트 prompt에 즉시 붙여넣기 가능한 마크다운
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

TARGET_DIR="${1:-.}"

# 절대경로 정규화
TARGET_DIR="$(cd "$TARGET_DIR" 2>/dev/null && pwd)" || {
    printf "ERROR: 디렉토리를 찾을 수 없습니다: %s\n" "${1:-.}" >&2
    exit 1
}

COLLECTED_AT="$(date '+%Y-%m-%d %H:%M:%S')"

# ─── 헬퍼 ────────────────────────────────────────────────────

# 소스 파일 확장자 여부 (바이너리·빌드 산출물 제외)
is_source_ext() {
    case "${1##*.}" in
        # 웹·스크립트
        js|jsx|ts|tsx|vue|svelte|mjs|cjs) return 0 ;;
        html|htm|css|scss|sass|less)       return 0 ;;
        # 백엔드
        php|py|rb|go|rs|java|kt|swift)    return 0 ;;
        c|cpp|cc|h|hpp)                   return 0 ;;
        # 설정·데이터
        json|yaml|yml|toml|ini)           return 0 ;;
        # 셸·쿼리·기타
        sh|bash|zsh|sql|graphql|proto|md) return 0 ;;
        *) return 1 ;;
    esac
}

# 무시할 최상단 디렉토리
should_skip_dir() {
    case "$1" in
        node_modules|vendor|.git|.svn|dist|build|out) return 0 ;;
        __pycache__|.next|.nuxt|.cache|coverage)       return 0 ;;
        target|.gradle|.idea|.vscode)                  return 0 ;;
        *) return 1 ;;
    esac
}

# ─── 마크다운 헤더 ───────────────────────────────────────────

cat <<HEADER
# Preflight Collect — 서브에이전트 컨텍스트 패킷

> 수집 시각: ${COLLECTED_AT}
> 대상 경로: \`${TARGET_DIR}\`

---

HEADER

# ═══════════════════════════════════════════════════════════════
# [1/5] 소스 파일 목록 (최대 30개)
# ═══════════════════════════════════════════════════════════════

echo "## 1. 소스 파일 목록 (최대 30개)"
echo ""

FILE_LIST=()

while IFS= read -r -d '' filepath; do
    rel="${filepath#"$TARGET_DIR"/}"
    top_dir="${rel%%/*}"

    # 무시 디렉토리 스킵
    if should_skip_dir "$top_dir"; then
        continue
    fi

    if is_source_ext "$filepath"; then
        FILE_LIST+=("$rel")
    fi
done < <(find "$TARGET_DIR" -type f -print0 2>/dev/null | sort -z)

TOTAL_FILES="${#FILE_LIST[@]}"
OVERFLOW=$(( TOTAL_FILES > 30 ? TOTAL_FILES - 30 : 0 ))

echo '```'
for f in "${FILE_LIST[@]:0:30}"; do
    echo "$f"
done
echo '```'
echo ""
echo "- 총 소스 파일: **${TOTAL_FILES}개** (빌드/의존성 디렉토리 제외)"
if [ "$OVERFLOW" -gt 0 ]; then
    echo "- 30개 초과: 나머지 **${OVERFLOW}개** 생략 — 필요하면 경로를 좁혀 재실행"
fi
echo ""

# ═══════════════════════════════════════════════════════════════
# [2/5] 주요 패턴 검색 (function / class / interface 키워드)
# ═══════════════════════════════════════════════════════════════

echo "## 2. 주요 패턴 검색"
echo ""

# grep -rl: 해당 키워드가 등장하는 파일 수를 세는 함수
# grep이 매칭 없을 때 exit 1을 반환하므로 || true로 안전하게 처리
count_keyword_files() {
    local kw="$1"
    { grep -rl \
        --include="*.php" --include="*.js" --include="*.ts" \
        --include="*.py"  --include="*.go" --include="*.rb" \
        --include="*.java" --include="*.swift" --include="*.kt" \
        --exclude-dir=node_modules --exclude-dir=vendor \
        --exclude-dir=dist        --exclude-dir=build \
        --exclude-dir=__pycache__ \
        "$kw" "$TARGET_DIR" 2>/dev/null || true; } | wc -l | tr -d ' '
}

CNT_FUNCTION=$(count_keyword_files '\bfunction\b')
CNT_CLASS=$(count_keyword_files '\bclass\b')
CNT_INTERFACE=$(count_keyword_files '\binterface\b')

echo "| 키워드 | 등장 파일 수 |"
echo "|--------|-------------|"
echo "| \`function\`  | ${CNT_FUNCTION}개 파일 |"
echo "| \`class\`     | ${CNT_CLASS}개 파일 |"
echo "| \`interface\` | ${CNT_INTERFACE}개 파일 |"
echo ""

# class 포함 파일 목록 (최대 10개)
CLASS_FILES=$({ grep -rl '\bclass\b' \
    --include="*.php" --include="*.js" --include="*.ts" \
    --include="*.py"  --include="*.go" --include="*.java" \
    --exclude-dir=node_modules --exclude-dir=vendor \
    --exclude-dir=dist        --exclude-dir=build \
    "$TARGET_DIR" 2>/dev/null || true; } \
    | head -10 \
    | sed "s|${TARGET_DIR}/||")

if [ -n "$CLASS_FILES" ]; then
    echo "**\`class\` 포함 주요 파일 (최대 10개):**"
    echo '```'
    echo "$CLASS_FILES"
    echo '```'
    echo ""
fi

# interface 포함 파일 목록 (TypeScript / Go 한정, 최대 10개)
IFACE_FILES=$({ grep -rl '\binterface\b' \
    --include="*.ts" --include="*.tsx" --include="*.go" --include="*.java" \
    --exclude-dir=node_modules --exclude-dir=dist --exclude-dir=build \
    "$TARGET_DIR" 2>/dev/null || true; } \
    | head -10 \
    | sed "s|${TARGET_DIR}/||")

if [ -n "$IFACE_FILES" ]; then
    echo "**\`interface\` 포함 주요 파일 (최대 10개):**"
    echo '```'
    echo "$IFACE_FILES"
    echo '```'
    echo ""
fi

# ═══════════════════════════════════════════════════════════════
# [3/5] 최근 git 변경 이력 (최근 3커밋)
# ═══════════════════════════════════════════════════════════════

echo "## 3. 최근 Git 변경 이력"
echo ""

if ! git -C "$TARGET_DIR" rev-parse --git-dir &>/dev/null; then
    echo "> git 저장소가 아님 — 건너뜀"
    echo ""
else
    COMMIT_COUNT=$(git -C "$TARGET_DIR" rev-list --count HEAD 2>/dev/null || echo 0)

    echo "**최근 3 커밋:**"
    echo '```'
    git -C "$TARGET_DIR" log --oneline -3 --no-color 2>/dev/null || echo "(커밋 없음)"
    echo '```'
    echo ""

    # 마지막 커밋 변경 파일
    if [ "$COMMIT_COUNT" -ge 2 ]; then
        LAST_CHANGED=$(git -C "$TARGET_DIR" diff --name-only HEAD~1 HEAD 2>/dev/null | head -20 || true)
        if [ -n "$LAST_CHANGED" ]; then
            echo "**마지막 커밋 변경 파일 (최대 20개):**"
            echo '```'
            echo "$LAST_CHANGED"
            echo '```'
            echo ""
        fi
    fi

    # 미커밋 변경사항
    UNSTAGED=$(git -C "$TARGET_DIR" status --short 2>/dev/null | head -15 || true)
    if [ -n "$UNSTAGED" ]; then
        echo "**현재 미커밋 변경사항:**"
        echo '```'
        echo "$UNSTAGED"
        echo '```'
    else
        echo "> 미커밋 변경사항 없음 (워킹트리 클린)"
    fi
    echo ""
fi

# ═══════════════════════════════════════════════════════════════
# [4/5] 기술 스택 감지
# ═══════════════════════════════════════════════════════════════

echo "## 4. 기술 스택 감지"
echo ""

echo "| 파일 | 감지 | 비고 |"
echo "|------|:----:|------|"

stack_row() {
    local file="$1"
    local note="$2"
    if [ -f "$TARGET_DIR/$file" ]; then
        echo "| \`$file\` | O | $note |"
    else
        echo "| \`$file\` | - | $note |"
    fi
}

stack_row "package.json"       "Node.js / npm 프로젝트"
stack_row "composer.json"      "PHP Composer 프로젝트"
stack_row "requirements.txt"   "Python pip 의존성"
stack_row "pyproject.toml"     "Python Poetry / PEP 517"
stack_row "go.mod"             "Go 모듈"
stack_row "Cargo.toml"         "Rust Cargo 프로젝트"
stack_row "Gemfile"            "Ruby Bundler"
stack_row "build.gradle"       "Java Gradle 빌드"
stack_row "pom.xml"            "Java Maven 빌드"
stack_row "tsconfig.json"      "TypeScript 설정"
stack_row "vite.config.ts"     "Vite 번들러"
stack_row "vite.config.js"     "Vite 번들러"
stack_row "next.config.js"     "Next.js 프레임워크"
stack_row "next.config.mjs"    "Next.js 프레임워크"
stack_row "artisan"            "Laravel PHP 프레임워크"
stack_row "Dockerfile"         "컨테이너화"
stack_row "docker-compose.yml" "멀티 컨테이너"
stack_row ".eslintrc.json"     "ESLint (JSON)"
stack_row ".eslintrc.js"       "ESLint (JS)"
stack_row ".env.example"       "환경 변수 예시"

echo ""

# package.json 의존성 요약
if [ -f "$TARGET_DIR/package.json" ]; then
    echo "**package.json 주요 의존성:**"
    echo '```'
    if command -v jq &>/dev/null; then
        jq '{
            name: .name,
            version: .version,
            dependencies:    (.dependencies    // {} | keys),
            devDependencies: (.devDependencies // {} | keys | .[0:10])
        }' "$TARGET_DIR/package.json" 2>/dev/null \
        || head -30 "$TARGET_DIR/package.json"
    else
        head -30 "$TARGET_DIR/package.json"
    fi
    echo '```'
    echo ""
fi

# composer.json 의존성 요약
if [ -f "$TARGET_DIR/composer.json" ]; then
    echo "**composer.json require:**"
    echo '```'
    if command -v jq &>/dev/null; then
        jq '{
            require:     (.require      // {}),
            "require-dev": (."require-dev" // {} | keys | .[0:5])
        }' "$TARGET_DIR/composer.json" 2>/dev/null \
        || head -20 "$TARGET_DIR/composer.json"
    else
        head -20 "$TARGET_DIR/composer.json"
    fi
    echo '```'
    echo ""
fi

# requirements.txt 패키지 목록
if [ -f "$TARGET_DIR/requirements.txt" ]; then
    echo "**requirements.txt (상위 10개):**"
    echo '```'
    grep -v '^#' "$TARGET_DIR/requirements.txt" \
        | grep -v '^[[:space:]]*$' \
        | head -10 || true
    echo '```'
    echo ""
fi

# ═══════════════════════════════════════════════════════════════
# [5/5] 에이전트 즉시 사용 지침
# ═══════════════════════════════════════════════════════════════

echo "## 5. 에이전트 위임 지침"
echo ""
echo "아래 블록을 서브에이전트 prompt에 그대로 첨부하세요."
echo ""

cat <<AGENT_BLOCK
\`\`\`
### [사전 수집 컨텍스트 — 읽기 전용]
- 대상 디렉토리: ${TARGET_DIR}
- 수집 시각    : ${COLLECTED_AT}
- 총 소스 파일 : ${TOTAL_FILES}개

#### 작업 범위 제한
- 위 [1/5] 파일 목록 외 파일은 탐색하지 않는다.
- node_modules, vendor, dist, build, __pycache__ 는 접근 금지.
- .env, keys/ 등 시크릿 파일은 절대 수정하지 않는다.

#### 반환 형식
1. 수정한 파일 목록 (절대 경로)
2. 변경 요약 (5줄 이내)
3. 검증 기준 충족 여부 (Yes / No + 이유)
\`\`\`
AGENT_BLOCK

echo ""

# ─── 푸터 ────────────────────────────────────────────────────

cat <<FOOTER
---

> **preflight-collect.sh** — Claude Code 서브에이전트 위임 전 사전 수집 도구
> 재실행: \`bash scripts/preflight-collect.sh ${TARGET_DIR}\`
FOOTER
