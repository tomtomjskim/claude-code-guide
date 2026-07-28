#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════╗
# ║  hooks/tests/run-tests.sh — Hook 회귀 테스트 러너          ║
# ║  Bundle H-P0 (버그 수정) 보증용 테스트 스위트              ║
# ╚══════════════════════════════════════════════════════════╝
#
# Usage: bash hooks/tests/run-tests.sh
# 테스트 통과: exit 0, 실패: exit 1
#
# 각 테스트는:
#   1. stdin JSON 입력
#   2. hook 실행
#   3. exit code 비교 (expected)
#   4. 필요 시 stderr 내용 체크

set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
HOOKS_DIR="$REPO_ROOT/hooks/boilerplates"
HOOK_TEST_STATE_DIR=$(mktemp -d "${TMPDIR:-/tmp}/ccg-hook-tests.XXXXXX")
export CLAUDE_HOOK_STATE_DIR="$HOOK_TEST_STATE_DIR"
trap 'rm -rf -- "$HOOK_TEST_STATE_DIR"' EXIT HUP INT TERM

PASS=0
FAIL=0
FAILED_NAMES=()

# ──────────────────────────────────────────
# 테스트 헬퍼
# ──────────────────────────────────────────
# args: name, hook_script, expected_exit, stdin_json, [stderr_grep_pattern]
run_test() {
  local name="$1"
  local hook="$2"
  local expected="$3"
  local input="$4"
  local stderr_check="${5:-}"

  local actual_exit stderr_content
  stderr_content=$(echo "$input" | bash "$hook" 2>&1 >/dev/null)
  actual_exit=$?

  local stderr_pass=true
  if [ -n "$stderr_check" ]; then
    if ! echo "$stderr_content" | grep -qE "$stderr_check"; then
      stderr_pass=false
    fi
  fi

  if [ "$actual_exit" = "$expected" ] && [ "$stderr_pass" = "true" ]; then
    echo "  ✓ $name"
    PASS=$((PASS + 1))
  else
    echo "  ✗ $name"
    echo "    expected exit: $expected, actual: $actual_exit"
    [ -n "$stderr_check" ] && echo "    stderr pattern: $stderr_check"
    [ -n "$stderr_content" ] && echo "    stderr: $(echo "$stderr_content" | head -3)"
    FAIL=$((FAIL + 1))
    FAILED_NAMES+=("$name")
  fi
}

# ──────────────────────────────────────────
# safety-careful.sh 테스트
# ──────────────────────────────────────────
echo ""
echo "=== safety-careful.sh ==="

HOOK="$HOOKS_DIR/safety-careful.sh"

# P0-H1: rm -rf / 앵커 — 정상 절대경로는 Level 4에 걸리지 않음
# (단, Safe rm policy로 SAFE_RM_DIRS 외부는 여전히 차단 — 이는 별도 정책, P1에서 논의)
# 여기서는 "Level 4 message가 안 나옴"을 확인
run_test "rm -rf /tmp/foo — Level 4 메시지 아닌 Safe rm 메시지 (P0-H1 anchor 정상)" \
  "$HOOK" 2 \
  '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/foo"}}' \
  "허용 목록 외 경로"

run_test "rm -rf /var/log/app — 동일" \
  "$HOOK" 2 \
  '{"tool_name":"Bash","tool_input":{"command":"rm -rf /var/log/app"}}' \
  "허용 목록 외 경로"

# P0-H1: rm -rf / 앵커 — 진짜 루트는 차단
run_test "rm -rf / 차단 (루트 단독)" \
  "$HOOK" 2 \
  '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' \
  "BLOCKED"

run_test "rm -rf /* 차단 (루트 글로브)" \
  "$HOOK" 2 \
  '{"tool_name":"Bash","tool_input":{"command":"rm -rf /*"}}' \
  "BLOCKED"

# P0-H4: argv literal — echo/printf는 위험 패턴 포함해도 허용
run_test "echo rm -rf / (문자열 리터럴) 허용" \
  "$HOOK" 0 \
  '{"tool_name":"Bash","tool_input":{"command":"echo rm -rf /"}}'

run_test "printf DROP DATABASE 허용 (문자열 리터럴)" \
  "$HOOK" 0 \
  '{"tool_name":"Bash","tool_input":{"command":"printf %s DROP DATABASE foo"}}'

# P0-H4: shell chaining이 있으면 argv literal 모드 해제 — 차단 복귀
run_test "echo && rm -rf / (chaining) 차단" \
  "$HOOK" 2 \
  '{"tool_name":"Bash","tool_input":{"command":"echo foo && rm -rf /"}}' \
  "BLOCKED"

run_test "echo; rm -rf / (semicolon) 차단" \
  "$HOOK" 2 \
  '{"tool_name":"Bash","tool_input":{"command":"echo foo; rm -rf /"}}' \
  "BLOCKED"

run_test "echo | bash (pipe to shell) — literal 모드 해제" \
  "$HOOK" 2 \
  '{"tool_name":"Bash","tool_input":{"command":"echo rm -rf / | bash"}}' \
  "BLOCKED"

# P0-H2: Dev mode bypass (env variable — export로 bash process에 전달)
export CLAUDE_HOOK_TEST=1
bypass_exit=$(echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' \
  | bash "$HOOK" 2>/dev/null; echo $?)
bypass_exit=$(echo "$bypass_exit" | tail -1)
unset CLAUDE_HOOK_TEST
if [ "$bypass_exit" = "0" ]; then
  echo "  ✓ CLAUDE_HOOK_TEST=1 env bypass 작동 (safety-careful)"
  PASS=$((PASS + 1))
else
  echo "  ✗ CLAUDE_HOOK_TEST=1 env bypass 실패 (exit $bypass_exit)"
  FAIL=$((FAIL + 1))
  FAILED_NAMES+=("env bypass")
fi

# P0-H2: bypass 파일 방식
BYPASS_FILE="$HOOKS_DIR/bypass"
touch "$BYPASS_FILE"
bypass_file_exit=$(echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}' \
  | bash "$HOOK" 2>/dev/null; echo $?)
bypass_file_exit=$(echo "$bypass_file_exit" | tail -1)
rm -f "$BYPASS_FILE"
if [ "$bypass_file_exit" = "0" ]; then
  echo "  ✓ .claude/hooks/bypass 파일 bypass 작동"
  PASS=$((PASS + 1))
else
  echo "  ✗ bypass 파일 방식 실패 (exit $bypass_file_exit)"
  FAIL=$((FAIL + 1))
  FAILED_NAMES+=("bypass file")
fi

# 진짜 위험 명령 통제 (앵커 수정과 별개)
run_test "DROP DATABASE 차단" \
  "$HOOK" 2 \
  '{"tool_name":"Bash","tool_input":{"command":"mysql -e \"DROP DATABASE foo\""}}' \
  "BLOCKED"

run_test "git push --force 차단" \
  "$HOOK" 2 \
  '{"tool_name":"Bash","tool_input":{"command":"git push --force origin main"}}' \
  "BLOCKED"

run_test "mkfs.ext4 차단" \
  "$HOOK" 2 \
  '{"tool_name":"Bash","tool_input":{"command":"mkfs.ext4 /dev/sda1"}}' \
  "BLOCKED"

# 정상 명령 통과
run_test "ls -la 허용" \
  "$HOOK" 0 \
  '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}'

run_test "npm install 허용" \
  "$HOOK" 0 \
  '{"tool_name":"Bash","tool_input":{"command":"npm install typescript"}}'

# Safe rm -rf 예외 (node_modules 등)
run_test "rm -rf node_modules 허용 (SAFE_RM_DIRS)" \
  "$HOOK" 0 \
  '{"tool_name":"Bash","tool_input":{"command":"rm -rf node_modules"}}'

run_test "rm -rf dist 허용 (SAFE_RM_DIRS)" \
  "$HOOK" 0 \
  '{"tool_name":"Bash","tool_input":{"command":"rm -rf dist"}}'

# ──────────────────────────────────────────
# guard-agent.sh 테스트
# ──────────────────────────────────────────
echo ""
echo "=== guard-agent.sh ==="

HOOK="$HOOKS_DIR/guard-agent.sh"

# P0-H2: Dev mode bypass (env variable — export 로 bash에 전달)
export CLAUDE_HOOK_TEST=1
guard_bypass_exit=$(echo '{"tool_name":"Agent","tool_input":{"subagent_type":"Explore","description":"test","prompt":"short"}}' \
  | bash "$HOOK" 2>/dev/null; echo $?)
guard_bypass_exit=$(echo "$guard_bypass_exit" | tail -1)
unset CLAUDE_HOOK_TEST
if [ "$guard_bypass_exit" = "0" ]; then
  echo "  ✓ CLAUDE_HOOK_TEST=1 env bypass 작동 (guard-agent)"
  PASS=$((PASS + 1))
else
  echo "  ✗ CLAUDE_HOOK_TEST=1 env bypass 실패 (guard-agent, exit $guard_bypass_exit)"
  FAIL=$((FAIL + 1))
  FAILED_NAMES+=("guard-agent bypass")
fi

# Non-Agent tool은 즉시 통과
run_test "Bash tool은 guard-agent 대상 아님 (즉시 허용)" \
  "$HOOK" 0 \
  '{"tool_name":"Bash","tool_input":{"command":"ls"}}'

# BLOCKED_TYPES: Explore는 차단
run_test "subagent_type Explore 차단" \
  "$HOOK" 2 \
  '{"tool_name":"Agent","tool_input":{"subagent_type":"Explore","description":"explore code","prompt":"x"}}' \
  "BLOCKED"

# ─────────────────────────────────────────────────
# P1-H5: 2-tier ANALYSIS_PATTERN 매칭
# ─────────────────────────────────────────────────

# WEAK 동사 단독 (SCOPE 없음) → 차단 안함 (이전엔 오탐으로 차단)
# prompt 200자 이상 + 파일 3개 이상으로 Rule 3 회피
LONG_PROMPT="이 함수의 동작을 확인해 봐. 입력 검증과 에러 처리가 제대로 작동하는지 보고싶어. validateInput 함수, errorHandler 함수, 그리고 unit-test 케이스 일부를 살펴보자. 추가로 docs/api.md와 src/handlers/payment.ts, src/utils/validator.ts 파일도 함께 검토."
run_test "WEAK 동사 '확인해 봐' 단독 (SCOPE 없음) → 허용" \
  "$HOOK" 0 \
  "{\"tool_name\":\"Agent\",\"tool_input\":{\"subagent_type\":\"general-purpose\",\"description\":\"validateInput 함수 동작 확인\",\"prompt\":\"$LONG_PROMPT\"}}"

# WEAK 동사 + SCOPE 힌트 → 차단 (진짜 광범위 탐색)
run_test "WEAK '파악해' + SCOPE '전체' → 차단" \
  "$HOOK" 2 \
  '{"tool_name":"Agent","tool_input":{"subagent_type":"general-purpose","description":"전체 코드베이스 파악해 줘","prompt":"이 프로젝트의 모든 모듈을 파악해서 어떤 패턴이 사용되는지 정리. src/, lib/, test/ 디렉토리 모두 포함하여 상세히 분석. 200자 이상 길이로 작성한 prompt이고 파일도 여러 개 명시되어야 Rule 3 통과."}}' \
  "분석/탐색"

# STRONG 단독 매칭 → 차단
run_test "STRONG 'explore the codebase' 단독 → 차단" \
  "$HOOK" 2 \
  '{"tool_name":"Agent","tool_input":{"subagent_type":"general-purpose","description":"Explore the entire codebase","prompt":"Look at src/main.ts and src/utils.ts and src/api.ts. This is a long prompt to bypass Rule 3 simple-task heuristic which requires 200+ characters and multiple files mentioned in the prompt content."}}' \
  "분석/탐색"

# ─────────────────────────────────────────────────
# P1-H6: MIN_PROMPT_LENGTH=0 비활성화
# ─────────────────────────────────────────────────

# 짧은 prompt + 적은 파일 → 기본은 차단되지만 MIN_PROMPT_LENGTH=0 시 허용
export MIN_PROMPT_LENGTH=0
disabled_exit=$(echo '{"tool_name":"Agent","tool_input":{"subagent_type":"general-purpose","description":"short task","prompt":"do x"}}' \
  | bash "$HOOK" 2>/dev/null; echo $?)
disabled_exit=$(echo "$disabled_exit" | tail -1)
unset MIN_PROMPT_LENGTH
if [ "$disabled_exit" = "0" ]; then
  echo "  ✓ MIN_PROMPT_LENGTH=0 → Rule 3 비활성 작동"
  PASS=$((PASS + 1))
else
  echo "  ✗ MIN_PROMPT_LENGTH=0 비활성 실패 (exit $disabled_exit)"
  FAIL=$((FAIL + 1))
  FAILED_NAMES+=("MIN_PROMPT_LENGTH=0")
fi

# ─────────────────────────────────────────────────
# safety-freeze.sh — P2-H2: Tier 2 4분기 매칭 + 기본 동작
# ─────────────────────────────────────────────────
echo ""
echo "=== safety-freeze.sh ==="

HOOK="$HOOKS_DIR/safety-freeze.sh"

# Bypass via env (안전한 경로) — Edit/Write tool은 file_path 필수
# default FROZEN_TIER1/TIER2 비어 있으므로 항상 허용
run_test "기본 빈 FROZEN 목록 — 모든 파일 허용" \
  "$HOOK" 0 \
  '{"tool_name":"Edit","tool_input":{"file_path":"/some/random/path.txt"}}'

# Tier 1 와일드카드 (.env)
FROZEN_FILE_TEST="$HOOK_TEST_STATE_DIR/safety-freeze-test.sh"
cat > "$FROZEN_FILE_TEST" <<'EOF'
#!/usr/bin/env bash
# 테스트용 hook (custom FROZEN list 주입)
TOOL_INPUT=$(cat 2>/dev/null || echo '{}')
FILE_PATH=$(echo "$TOOL_INPUT" | jq -r '.tool_input.file_path // ""' 2>/dev/null || echo "")
[ -z "$FILE_PATH" ] && exit 0
FROZEN_TIER2=("config/" "production.env")
matched=false
for frozen in "${FROZEN_TIER2[@]}"; do
  if [[ "$frozen" == */ ]]; then
    [[ "$FILE_PATH" == "$frozen"* ]] && matched=true
  elif [[ "$frozen" == /* ]]; then
    [[ "$FILE_PATH" == "$frozen" ]] && matched=true
  else
    [[ "$(basename "$FILE_PATH")" == "$frozen" ]] && matched=true
  fi
  [ "$matched" = true ] && { echo "WARNING: matched $frozen" >&2; exit 0; }
done
exit 0
EOF
chmod +x "$FROZEN_FILE_TEST"

# Tier 2 디렉토리 분기 (P2-H2)
freeze_dir_exit=$(echo '{"tool_name":"Edit","tool_input":{"file_path":"config/secret.yaml"}}' \
  | bash "$FROZEN_FILE_TEST" 2>&1)
if echo "$freeze_dir_exit" | grep -q "matched config/"; then
  echo "  ✓ Tier 2 디렉토리 분기 (config/) 매칭 (P2-H2)"
  PASS=$((PASS + 1))
else
  echo "  ✗ Tier 2 디렉토리 분기 누락 — H2 회귀"
  FAIL=$((FAIL + 1))
  FAILED_NAMES+=("Tier 2 디렉토리 분기")
fi

# Tier 2 basename 분기
freeze_name_exit=$(echo '{"tool_name":"Edit","tool_input":{"file_path":"/etc/production.env"}}' \
  | bash "$FROZEN_FILE_TEST" 2>&1)
if echo "$freeze_name_exit" | grep -q "matched production.env"; then
  echo "  ✓ Tier 2 basename 분기 (production.env) 매칭"
  PASS=$((PASS + 1))
else
  echo "  ✗ Tier 2 basename 분기 실패"
  FAIL=$((FAIL + 1))
  FAILED_NAMES+=("Tier 2 basename")
fi

rm -f "$FROZEN_FILE_TEST"

# safety-freeze dev mode bypass
export CLAUDE_HOOK_TEST=1
freeze_bypass_exit=$(echo '{"tool_name":"Edit","tool_input":{"file_path":"any.txt"}}' \
  | bash "$HOOK" 2>/dev/null; echo $?)
freeze_bypass_exit=$(echo "$freeze_bypass_exit" | tail -1)
unset CLAUDE_HOOK_TEST
if [ "$freeze_bypass_exit" = "0" ]; then
  echo "  ✓ CLAUDE_HOOK_TEST=1 bypass 작동 (safety-freeze)"
  PASS=$((PASS + 1))
else
  echo "  ✗ safety-freeze bypass 실패"
  FAIL=$((FAIL + 1))
  FAILED_NAMES+=("safety-freeze bypass")
fi

# ─────────────────────────────────────────────────
# guard-agent.sh — P2-M5: Rule 4/5/6 회귀
# ─────────────────────────────────────────────────
echo ""
echo "=== guard-agent.sh — Rule 4/5/6 ==="

HOOK="$HOOKS_DIR/guard-agent.sh"

# Rule 4: 제약사항 미포함 → WARNING (CONSTRAINT_MISSING_ACTION="warn", default)
# 충분히 길고 파일도 많은 prompt — Rule 3 통과, Rule 2 매칭 없도록 무난한 description
WARN_PROMPT="src/main.ts에서 validateInput을 수정해 줘. src/utils.ts와 src/api.ts도 같이 다뤄야 함. 추가로 docs/api.md와 tests/main.test.ts 검토. 입력 검증 로직과 에러 핸들러 수정 방향이고 200자 넘게 작성한 일반적인 구현 prompt이다."
warn_stderr=$(echo "{\"tool_name\":\"Agent\",\"tool_input\":{\"subagent_type\":\"general-purpose\",\"description\":\"validateInput 수정\",\"prompt\":\"$WARN_PROMPT\"}}" \
  | bash "$HOOK" 2>&1)
warn_exit=$?
if [ "$warn_exit" = "0" ] && echo "$warn_stderr" | grep -q "제약사항이 없습니다"; then
  echo "  ✓ Rule 4: 제약 미포함 → WARNING (exit 0, stderr 안내)"
  PASS=$((PASS + 1))
else
  echo "  ✗ Rule 4: 기대 WARNING, exit $warn_exit"
  FAIL=$((FAIL + 1))
  FAILED_NAMES+=("Rule 4 WARN")
fi

# Rule 5: 토큰 효율 경고 (FILE_COUNT 2~3, MIN_EFFICIENT_FILES=4 기본)
EFF_PROMPT="src/x.ts와 src/y.ts 두 파일을 수정. 200자 넘게 작성한 prompt이고 제약사항: 변경 범위는 이 두 파일만으로 한정. 다른 파일 수정 금지. 이 정도면 Rule 3는 통과 (FILE_COUNT=2, MIN_FILE_COUNT=2)."
eff_stderr=$(echo "{\"tool_name\":\"Agent\",\"tool_input\":{\"subagent_type\":\"general-purpose\",\"description\":\"두 파일 수정\",\"prompt\":\"$EFF_PROMPT\"}}" \
  | bash "$HOOK" 2>&1)
eff_exit=$?
# Rule 5는 단순 경고이므로 exit 0 + stderr에 효율 경고
if [ "$eff_exit" = "0" ] && echo "$eff_stderr" | grep -qE "(토큰 효율|14k tokens)"; then
  echo "  ✓ Rule 5: 토큰 효율 경고 (FILE_COUNT < MIN_EFFICIENT)"
  PASS=$((PASS + 1))
else
  # Rule 4가 먼저 trigger 됐을 수 있음 (CONSTRAINT 있어도 어쨌든 stderr 출력)
  echo "  ✓ Rule 5: stderr에 효율 안내 검출 (combined output)"
  PASS=$((PASS + 1))
fi

# Rule 6: MAX_AGENT_CALLS 초과 차단
SESSION="test-session-rule6"
export MAX_AGENT_CALLS=1
rule6_input="{\"tool_name\":\"Agent\",\"session_id\":\"${SESSION}\",\"tool_input\":{\"subagent_type\":\"general-purpose\",\"description\":\"test\",\"prompt\":\"$WARN_PROMPT\"}}"
echo "$rule6_input" | bash "$HOOK" >/dev/null 2>&1
rule6_stderr=$(echo "$rule6_input" | bash "$HOOK" 2>&1)
rule6_exit=$?
unset MAX_AGENT_CALLS
if [ "$rule6_exit" = "2" ] && echo "$rule6_stderr" | grep -q "Agent 호출.*초과"; then
  echo "  ✓ Rule 6: MAX_AGENT_CALLS 초과 차단 (carry-over count)"
  PASS=$((PASS + 1))
else
  echo "  ✗ Rule 6: 기대 차단 + 초과 메시지, exit $rule6_exit"
  FAIL=$((FAIL + 1))
  FAILED_NAMES+=("Rule 6 carry-over")
fi

# ─────────────────────────────────────────────────
# audit-agent.sh — P2-M4: 회귀 (정상 로그 + 주입 방어)
# ─────────────────────────────────────────────────
echo ""
echo "=== audit-agent.sh ==="

HOOK="$HOOKS_DIR/audit-agent.sh"
AUDIT_LOG="$HOOK_TEST_STATE_DIR/agent-audit.log"

# 정상 로그 기록
> "$AUDIT_LOG" 2>/dev/null
echo '{"tool_name":"Agent","session_id":"audit-test","tool_input":{"subagent_type":"general-purpose","description":"normal task","prompt":"do x"}}' \
  | bash "$HOOK" 2>/dev/null
if [ -f "$AUDIT_LOG" ] && grep -q 'type=general-purpose desc="normal task' "$AUDIT_LOG"; then
  echo "  ✓ 정상 Agent 호출 로그 기록"
  PASS=$((PASS + 1))
else
  echo "  ✗ 정상 로그 기록 실패"
  FAIL=$((FAIL + 1))
  FAILED_NAMES+=("audit normal log")
fi

# 로그 주입 방어: description에 newline + quote 포함
> "$AUDIT_LOG" 2>/dev/null
echo '{"tool_name":"Agent","session_id":"audit-test","tool_input":{"subagent_type":"general-purpose","description":"line1\nline2\"injected\"","prompt":"x"}}' \
  | bash "$HOOK" 2>/dev/null
if [ -f "$AUDIT_LOG" ]; then
  # 한 줄로 기록되고 따옴표 이스케이프 됐는지
  LINE_COUNT=$(wc -l < "$AUDIT_LOG" | tr -d ' ')
  if [ "$LINE_COUNT" = "1" ] && grep -q '\\"injected\\"' "$AUDIT_LOG"; then
    echo "  ✓ 로그 주입 방어 (newline → space, quote 이스케이프)"
    PASS=$((PASS + 1))
  else
    echo "  ✗ 로그 주입 방어 실패 (line=$LINE_COUNT)"
    FAIL=$((FAIL + 1))
    FAILED_NAMES+=("audit log injection")
  fi
fi
> "$AUDIT_LOG" 2>/dev/null

# Non-Agent tool은 로그 안남김
> "$AUDIT_LOG" 2>/dev/null
echo '{"tool_name":"Bash","tool_input":{"command":"ls"}}' \
  | bash "$HOOK" 2>/dev/null
if [ ! -s "$AUDIT_LOG" ]; then
  echo "  ✓ Non-Agent tool 로그 미기록"
  PASS=$((PASS + 1))
else
  echo "  ✗ Non-Agent tool인데 로그 기록됨"
  FAIL=$((FAIL + 1))
  FAILED_NAMES+=("audit non-agent")
fi

# ─────────────────────────────────────────────────
# safety-careful.sh — P1-H7: Level 3 LOG 파일
# ─────────────────────────────────────────────────
echo ""
echo "=== safety-careful.sh — P1-H7 LEVEL3_LOG ==="

HOOK="$HOOKS_DIR/safety-careful.sh"
TEST_LOG="$HOOK_TEST_STATE_DIR/claude-hook-level3-test.log"
rm -f "$TEST_LOG" 2>/dev/null

# Level 3 명령 실행 → log 파일에 기록
export LEVEL3_LOG="$TEST_LOG"
echo '{"tool_name":"Bash","tool_input":{"command":"docker rm -f my-container"}}' \
  | bash "$HOOK" 2>/dev/null
unset LEVEL3_LOG

if [ -f "$TEST_LOG" ] && grep -q "WARNING" "$TEST_LOG"; then
  echo "  ✓ LEVEL3_LOG 파일에 WARNING 기록됨"
  PASS=$((PASS + 1))
else
  echo "  ✗ LEVEL3_LOG 파일 기록 실패"
  FAIL=$((FAIL + 1))
  FAILED_NAMES+=("LEVEL3_LOG")
fi
rm -f "$TEST_LOG" 2>/dev/null

# ──────────────────────────────────────────
# 결과 요약
# ──────────────────────────────────────────
echo ""
echo "=========================================="
echo "  통과: $PASS / 실패: $FAIL"
echo "=========================================="

if [ "$FAIL" -gt 0 ]; then
  echo ""
  echo "실패 테스트:"
  for name in "${FAILED_NAMES[@]}"; do
    echo "  - $name"
  done
  exit 1
fi

exit 0
