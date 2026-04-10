#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# Claude Code 토큰 낭비 자가진단 스크립트 v3.3
# 사용법: bash scripts/selfcheck-token-waste.sh [프로젝트경로]
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# 카운터
PASS=0
WARN=0
FAIL=0
TOTAL_WASTE_TOKENS=0

PROJECT_DIR="${1:-.}"
GLOBAL_SETTINGS="$HOME/.claude/settings.json"
PROJECT_SETTINGS="$PROJECT_DIR/.claude/settings.json"
GLOBAL_CLAUDE_MD="$HOME/.claude/CLAUDE.md"
PROJECT_CLAUDE_MD_1="$PROJECT_DIR/CLAUDE.md"
PROJECT_CLAUDE_MD_2="$PROJECT_DIR/.claude/CLAUDE.md"
SKILLS_DIR="$PROJECT_DIR/.claude/skills"
MEMORY_DIR="$HOME/.claude/projects"

echo ""
echo -e "${BOLD}═══════════════════════════════════════════════${NC}"
echo -e "${BOLD}  Claude Code 토큰 낭비 자가진단 (v3.3)${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════${NC}"
echo ""
echo -e "프로젝트: ${CYAN}$PROJECT_DIR${NC}"
echo ""

# ─── Helper ───
result_pass() {
    echo -e "${GREEN}✅ PASS${NC} $1"
    PASS=$((PASS + 1))
}
result_warn() {
    echo -e "${YELLOW}⚠️  WARN${NC} $1"
    WARN=$((WARN + 1))
    TOTAL_WASTE_TOKENS=$((TOTAL_WASTE_TOKENS + $2))
}
result_fail() {
    echo -e "${RED}❌ FAIL${NC} $1"
    FAIL=$((FAIL + 1))
    TOTAL_WASTE_TOKENS=$((TOTAL_WASTE_TOKENS + $2))
}

# JSON 값 읽기 (jq 없는 환경 대응)
json_get() {
    local file="$1" key="$2"
    if command -v jq &>/dev/null; then
        jq -r "$key // empty" "$file" 2>/dev/null || echo ""
    else
        python3 -c "
import json, sys
try:
    with open('$file') as f:
        d = json.load(f)
    keys = '$key'.strip('.').split('.')
    v = d
    for k in keys:
        if isinstance(v, dict):
            v = v.get(k)
        else:
            v = None
            break
    if v is not None:
        print(v)
except:
    pass
" 2>/dev/null || echo ""
    fi
}

# ═══════════════════════════════════════════════
# [1/7] Fast Mode 차단
# ═══════════════════════════════════════════════
echo -e "${BOLD}[1/7] Fast Mode 차단${NC}"

FAST_MODE_ENV="${CLAUDE_CODE_DISABLE_FAST_MODE:-}"
FAST_MODE_SETTING=""
FAST_MODE_ENV_SETTING=""
# Check both global and project settings (project overrides global)
for _sf in "$GLOBAL_SETTINGS" "$PROJECT_SETTINGS"; do
    if [ -f "$_sf" ]; then
        _val=$(json_get "$_sf" ".fastMode")
        [ -n "$_val" ] && FAST_MODE_SETTING="$_val"
        _val=$(json_get "$_sf" ".env.CLAUDE_CODE_DISABLE_FAST_MODE")
        [ -n "$_val" ] && FAST_MODE_ENV_SETTING="$_val"
    fi
done

if [ "$FAST_MODE_ENV" = "1" ] || [ "$FAST_MODE_ENV_SETTING" = "1" ]; then
    if [ "$FAST_MODE_SETTING" = "false" ] || [ "$FAST_MODE_SETTING" = "False" ]; then
        result_pass "환경변수 + settings.json 이중 차단"
    else
        result_warn "환경변수로 차단됨, settings.json에 fastMode:false 추가 권장" 0
    fi
elif [ "$FAST_MODE_SETTING" = "false" ] || [ "$FAST_MODE_SETTING" = "False" ]; then
    result_warn "settings.json만 차단 — 환경변수 CLAUDE_CODE_DISABLE_FAST_MODE=1 추가 권장" 0
else
    result_fail "Fast Mode 미차단 — 비용 6x 위험" 5000
fi
echo ""

# ═══════════════════════════════════════════════
# [2/7] 서브에이전트 모델
# ═══════════════════════════════════════════════
echo -e "${BOLD}[2/7] 서브에이전트 모델${NC}"

SUBAGENT_ENV="${CLAUDE_CODE_SUBAGENT_MODEL:-}"
SUBAGENT_SETTING=""
# Check both global and project settings (project overrides global)
for _sf in "$GLOBAL_SETTINGS" "$PROJECT_SETTINGS"; do
    if [ -f "$_sf" ]; then
        _val=$(json_get "$_sf" ".env.CLAUDE_CODE_SUBAGENT_MODEL")
        [ -n "$_val" ] && SUBAGENT_SETTING="$_val"
    fi
done

if [ -n "$SUBAGENT_ENV" ]; then
    result_pass "환경변수: $SUBAGENT_ENV"
elif [ -n "$SUBAGENT_SETTING" ]; then
    result_pass "settings.json: $SUBAGENT_SETTING"
else
    result_warn "미설정 — 서브에이전트가 현재 모델과 동일하게 실행 (비용 증가)" 2000
fi
echo ""

# ═══════════════════════════════════════════════
# [3/7] Cloud AI MCP 서버
# ═══════════════════════════════════════════════
echo -e "${BOLD}[3/7] Cloud AI MCP 서버${NC}"

CLOUD_MCP_COUNT=0
CLOUD_MCP_LIST=""

check_cloud_mcp() {
    local file="$1"
    if [ ! -f "$file" ]; then return; fi

    if command -v jq &>/dev/null; then
        local mcps
        mcps=$(jq -r '.mcpServers // {} | keys[]' "$file" 2>/dev/null || echo "")
        for mcp in $mcps; do
            if echo "$mcp" | grep -qi "claude_ai\|canva\|figma\|gmail\|google_calendar\|magic_patterns"; then
                local disabled
                disabled=$(jq -r ".mcpServers.\"$mcp\".disabled // false" "$file" 2>/dev/null)
                if [ "$disabled" != "true" ]; then
                    CLOUD_MCP_COUNT=$((CLOUD_MCP_COUNT + 1))
                    CLOUD_MCP_LIST="$CLOUD_MCP_LIST $mcp"
                fi
            fi
        done
    else
        local _py_result
        _py_result=$(python3 -c "
import json
try:
    with open('$file') as f:
        d = json.load(f)
    mcps = d.get('mcpServers', {})
    cloud_keys = ['canva', 'figma', 'gmail', 'google_calendar', 'magic_patterns', 'claude_ai']
    for k, v in mcps.items():
        if any(ck in k.lower() for ck in cloud_keys):
            if not v.get('disabled', False):
                print(k)
except:
    pass
" 2>/dev/null)
        if [ -n "$_py_result" ]; then
            while IFS= read -r mcp; do
                CLOUD_MCP_COUNT=$((CLOUD_MCP_COUNT + 1))
                CLOUD_MCP_LIST="$CLOUD_MCP_LIST $mcp"
            done <<< "$_py_result"
        fi
    fi
}

check_cloud_mcp "$GLOBAL_SETTINGS"
check_cloud_mcp "$PROJECT_SETTINGS"

if [ "$CLOUD_MCP_COUNT" -eq 0 ]; then
    result_pass "Cloud AI MCP 없음 또는 전체 비활성화"
elif [ "$CLOUD_MCP_COUNT" -le 2 ]; then
    result_warn "${CLOUD_MCP_COUNT}개 활성:${CLOUD_MCP_LIST}" $((CLOUD_MCP_COUNT * 1500))
else
    result_fail "${CLOUD_MCP_COUNT}개 활성:${CLOUD_MCP_LIST}" $((CLOUD_MCP_COUNT * 1500))
fi

echo -e "  ${CYAN}참고: Cloud AI MCP는 claude.ai 웹/데스크탑 앱에서 자동 활성화될 수 있음${NC}"
echo -e "  ${CYAN}CLI 전용 사용 시 이 항목은 무시해도 됨${NC}"
echo ""

# ═══════════════════════════════════════════════
# [4/7] 스킬 크기
# ═══════════════════════════════════════════════
echo -e "${BOLD}[4/7] 스킬 크기${NC}"

SKILL_OVERSIZE=0
SKILL_OVERSIZE_LIST=""

if [ -d "$SKILLS_DIR" ]; then
    while IFS= read -r skill_file; do
        size=$(wc -c < "$skill_file" | tr -d ' ')
        skill_name=$(basename "$(dirname "$skill_file")")
        size_kb=$((size / 1024))

        if [ "$size" -gt 12288 ]; then  # 12KB
            SKILL_OVERSIZE=$((SKILL_OVERSIZE + 1))
            SKILL_OVERSIZE_LIST="$SKILL_OVERSIZE_LIST ${skill_name}(${size_kb}KB)"
        fi
    done < <(find "$SKILLS_DIR" -name "SKILL.md" 2>/dev/null)

    if [ "$SKILL_OVERSIZE" -eq 0 ]; then
        SKILL_COUNT=$(find "$SKILLS_DIR" -name "SKILL.md" 2>/dev/null | wc -l | tr -d ' ')
        result_pass "전체 ${SKILL_COUNT}개 스킬 12KB 이하"
    else
        result_warn "${SKILL_OVERSIZE}개 과대:${SKILL_OVERSIZE_LIST}" $((SKILL_OVERSIZE * 2000))
    fi
else
    echo -e "  ${CYAN}스킬 디렉토리 없음 ($SKILLS_DIR)${NC}"
    result_pass "스킬 미사용 (토큰 소비 없음)"
fi
echo ""

# ═══════════════════════════════════════════════
# [5/7] CLAUDE.md 크기
# ═══════════════════════════════════════════════
echo -e "${BOLD}[5/7] CLAUDE.md 크기${NC}"

CLAUDE_MD_WASTE=0

check_claude_md() {
    local file="$1" label="$2" threshold="$3"
    if [ -f "$file" ]; then
        local size
        size=$(wc -c < "$file" | tr -d ' ')
        local size_kb=$((size / 1024))
        if [ "$size" -gt "$threshold" ]; then
            echo -e "  ${YELLOW}⚠️  ${label}: ${size_kb}KB (${threshold}B 초과)${NC}"
            CLAUDE_MD_WASTE=$((CLAUDE_MD_WASTE + size / 4))
        else
            echo -e "  ${GREEN}✅ ${label}: ${size_kb}KB${NC}"
        fi
    else
        echo -e "  ${CYAN}── ${label}: 없음${NC}"
    fi
}

check_claude_md "$GLOBAL_CLAUDE_MD" "글로벌 ~/.claude/CLAUDE.md" 2048
check_claude_md "$PROJECT_CLAUDE_MD_1" "프로젝트 CLAUDE.md" 5120
check_claude_md "$PROJECT_CLAUDE_MD_2" "프로젝트 .claude/CLAUDE.md" 5120

if [ "$CLAUDE_MD_WASTE" -gt 0 ]; then
    result_warn "CLAUDE.md 비대화 — 축소 권장" "$CLAUDE_MD_WASTE"
else
    result_pass "CLAUDE.md 크기 적정"
fi
echo ""

# ═══════════════════════════════════════════════
# [6/7] 메모리
# ═══════════════════════════════════════════════
echo -e "${BOLD}[6/7] 메모리 파일${NC}"

if [ -d "$MEMORY_DIR" ]; then
    MEM_COUNT=$(find "$MEMORY_DIR" -name "*.md" -path "*/memory/*" 2>/dev/null | wc -l | tr -d ' ')
    MEM_TOTAL_SIZE=$(find "$MEMORY_DIR" -name "*.md" -path "*/memory/*" -exec wc -c {} + 2>/dev/null | tail -1 | awk '{print $1}')
    MEM_TOTAL_SIZE=${MEM_TOTAL_SIZE:-0}
    MEM_SIZE_KB=$((MEM_TOTAL_SIZE / 1024))

    if [ "$MEM_COUNT" -le 5 ] && [ "$MEM_TOTAL_SIZE" -lt 10240 ]; then
        result_pass "파일 ${MEM_COUNT}개, 합산 ${MEM_SIZE_KB}KB"
    elif [ "$MEM_COUNT" -le 15 ]; then
        result_warn "파일 ${MEM_COUNT}개, 합산 ${MEM_SIZE_KB}KB — maxFiles 설정 확인, 불필요 메모리 정리 권장" 1500
    else
        result_fail "파일 ${MEM_COUNT}개, 합산 ${MEM_SIZE_KB}KB — 정리 필요 (maxFiles=3 설정으로 주입 제한)" 2500
    fi
else
    result_pass "메모리 디렉토리 없음"
fi
echo ""

# ═══════════════════════════════════════════════
# [7/7] settings.json 위험 설정
# ═══════════════════════════════════════════════
echo -e "${BOLD}[7/7] settings.json 위험 설정${NC}"

RISK_COUNT=0

check_setting_risk() {
    local file="$1"
    if [ ! -f "$file" ]; then return; fi

    # maxSkillsPerTurn 체크
    local max_skills
    max_skills=$(json_get "$file" ".maxSkillsPerTurn")
    if [ -z "$max_skills" ]; then
        echo -e "  ${YELLOW}⚠️  maxSkillsPerTurn: 미설정 (기본 5 — 3 이하 권장)${NC}"
        RISK_COUNT=$((RISK_COUNT + 1))
    elif [ "$max_skills" -gt 3 ] 2>/dev/null; then
        echo -e "  ${YELLOW}⚠️  maxSkillsPerTurn: $max_skills (3 이하 권장)${NC}"
        RISK_COUNT=$((RISK_COUNT + 1))
    else
        echo -e "  ${GREEN}✅ maxSkillsPerTurn: $max_skills${NC}"
    fi

    # memory.maxFiles 체크
    local max_mem
    max_mem=$(json_get "$file" ".memory.maxFiles")
    if [ -z "$max_mem" ]; then
        echo -e "  ${YELLOW}⚠️  memory.maxFiles: 미설정 (기본 5 — 3 권장)${NC}"
        RISK_COUNT=$((RISK_COUNT + 1))
    elif [ "$max_mem" -gt 5 ] 2>/dev/null; then
        echo -e "  ${YELLOW}⚠️  memory.maxFiles: $max_mem (5 이하 권장)${NC}"
        RISK_COUNT=$((RISK_COUNT + 1))
    else
        echo -e "  ${GREEN}✅ memory.maxFiles: $max_mem${NC}"
    fi

    # showTokenUsage 체크
    local show_tokens
    show_tokens=$(json_get "$file" ".showTokenUsage")
    if [ "$show_tokens" = "true" ] || [ "$show_tokens" = "True" ]; then
        echo -e "  ${GREEN}✅ showTokenUsage: true${NC}"
    else
        echo -e "  ${YELLOW}⚠️  showTokenUsage: 미활성화 (비용 인식 향상 위해 활성화 권장)${NC}"
        RISK_COUNT=$((RISK_COUNT + 1))
    fi

    # autoCompact 체크
    local auto_compact
    auto_compact=$(json_get "$file" ".autoCompact")
    if [ "$auto_compact" = "false" ] || [ "$auto_compact" = "False" ]; then
        echo -e "  ${RED}❌ autoCompact: false (true 권장 — 컨텍스트 비용 증가)${NC}"
        RISK_COUNT=$((RISK_COUNT + 1))
    else
        echo -e "  ${GREEN}✅ autoCompact: 활성화${NC}"
    fi
}

if [ -f "$GLOBAL_SETTINGS" ]; then
    echo -e "  ${CYAN}── 글로벌 settings ──${NC}"
    check_setting_risk "$GLOBAL_SETTINGS"
fi
if [ -f "$PROJECT_SETTINGS" ]; then
    echo -e "  ${CYAN}── 프로젝트 settings ──${NC}"
    check_setting_risk "$PROJECT_SETTINGS"
fi

if [ "$RISK_COUNT" -eq 0 ]; then
    result_pass "위험 설정 없음"
else
    result_warn "${RISK_COUNT}개 위험 설정 발견" $((RISK_COUNT * 500))
fi
echo ""

# ═══════════════════════════════════════════════
# 종합 결과
# ═══════════════════════════════════════════════
TOTAL=$((PASS + WARN + FAIL))

echo -e "${BOLD}───────────────────────────────────────────────${NC}"
echo -e "${BOLD}결과${NC}: ${GREEN}${PASS}/${TOTAL} PASS${NC}, ${YELLOW}${WARN}/${TOTAL} WARN${NC}, ${RED}${FAIL}/${TOTAL} FAIL${NC}"

if [ "$TOTAL_WASTE_TOKENS" -gt 0 ]; then
    # Sonnet 기준 $3/1M input
    WASTE_COST_CENTS=$((TOTAL_WASTE_TOKENS * 3 / 10000))
    echo -e "예상 턴당 낭비: ${YELLOW}~${TOTAL_WASTE_TOKENS} 토큰${NC} (~\$0.${WASTE_COST_CENTS}/턴 Sonnet)"
fi

if [ "$FAIL" -gt 0 ]; then
    echo -e "${RED}즉시 조치 필요${NC}: docs/28-token-waste-selfcheck.md 참조"
elif [ "$WARN" -gt 0 ]; then
    echo -e "${YELLOW}개선 권장${NC}: docs/28-token-waste-selfcheck.md 참조"
else
    echo -e "${GREEN}최적화 상태 양호${NC}"
fi

echo -e "${BOLD}═══════════════════════════════════════════════${NC}"
echo ""

exit $FAIL
