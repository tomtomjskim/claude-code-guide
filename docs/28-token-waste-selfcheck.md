# 토큰 낭비 자가진단 가이드

## 개요

Claude Code 세션에서 토큰이 어디서 낭비되는지 진단하고 개선하는 종합 가이드입니다. Cloud AI MCP 자동 활성화, Deferred Tools 오버헤드, 스킬/메모리/CLAUDE.md 비대화, 비최적 settings.json 설정 등 **실제 비용에 영향을 미치는 7대 낭비 요소**를 다룹니다.

---

**관련 문서**:
- [스킬 경량화 가이드](27-skill-lightweight-guide.md)
- [토큰 가격 및 비용 최적화](15-token-pricing-optimization.md)
- [서브에이전트 효율성 가이드](33-subagent-efficiency.md) — 에이전트 오버헤드 상세
- [Fast Mode 가이드](18-fast-mode.md)
- [환경 변수 레퍼런스](17-environment-variables.md)
- [Settings 스키마 레퍼런스](20-settings-schema-reference.md)
- [컨텍스트 윈도우 내부 동작](19-context-window-internals.md)

---

## 1. 7대 토큰 낭비 요소

| # | 낭비 요소 | 영향 범위 | 심각도 | 절감 가능성 |
|---|----------|----------|--------|-----------|
| 1 | Cloud AI MCP 자동 활성화 | 매 턴 시스템 프롬프트 | 🔴 높음 | 80%+ |
| 2 | Deferred Tools 목록 주입 | 매 턴 시스템 프롬프트 | 🟠 중간 | 50~70% |
| 3 | 스킬 비대화 | 스킬 호출 시 | 🟠 중간 | 60%+ |
| 4 | CLAUDE.md 비대화 | 매 턴 | 🟠 중간 | 40~60% |
| 5 | 메모리 과다 주입 | 매 턴 | 🟡 낮~중 | 30~50% |
| 6 | Fast Mode 미차단 | 매 턴 비용 6x | 🔴 높음 | 100% |
| 7 | 서브에이전트 모델 미지정 | 서브에이전트 호출 시 | 🟠 중간 | 40% |

---

## 2. Cloud AI MCP 자동 활성화 문제

### 2.1 문제 설명

Claude Code를 claude.ai 웹/데스크탑 앱에서 사용하거나, Claude Cloud AI 기능이 활성화된 환경에서는 **Anthropic이 제공하는 MCP 서버들이 자동으로 연결**됩니다.

현재 자동 활성화되는 Cloud AI MCP 서버:

| MCP 서버 | 도구 수 | 설명 |
|----------|--------|------|
| **Canva** | 30+ | 디자인 생성/편집/검색/내보내기 |
| **Figma** | 17+ | 디자인 읽기/Code Connect/다이어그램 |
| **Gmail** | 1+ | 이메일 인증/조작 |
| **Google Calendar** | 1+ | 캘린더 인증/조작 |
| **Magic Patterns** | 15+ | 디자인 시스템/아티팩트 관리 |

### 2.2 토큰 영향

자동 활성화된 MCP 서버는 두 가지 방식으로 토큰을 소비합니다:

```
영향 1: Deferred Tools 목록
  → 매 턴 system-reminder에 80+ tool 이름이 주입됨
  → 추정 ~1,500~2,000 토큰/턴

영향 2: MCP Server Instructions
  → 서버별 사용법 안내가 system-reminder로 주입됨
  → Figma만 ~2,000 토큰 (URL 파싱 규칙, 워크플로우 등)
  → 전체 합산 ~3,000~5,000 토큰/턴

합산: 매 턴 ~4,500~7,000 토큰이 MCP 관련으로 소비
10턴 Sonnet 세션: $0.135~$0.21 (MCP만으로)
```

### 2.3 진단 방법

```bash
# 현재 활성화된 MCP 서버 확인
claude mcp list

# settings.json에서 MCP 설정 확인
cat ~/.claude/settings.json | grep -A 5 "mcpServers"

# 프로젝트 settings에서도 확인
cat .claude/settings.json | grep -A 5 "mcpServers" 2>/dev/null
```

세션 내에서 확인:
```
/mcp
# → 연결된 MCP 서버 목록과 상태 표시
```

### 2.4 해결 방법

#### 방법 1: 사용하지 않는 Cloud AI MCP 비활성화

`~/.claude/settings.json`에서 불필요한 MCP 서버를 `disabled: true`로 설정합니다.

```json
{
  "mcpServers": {
    "claude_ai_Canva": {
      "disabled": true
    },
    "claude_ai_Gmail": {
      "disabled": true
    },
    "claude_ai_Google_Calendar": {
      "disabled": true
    },
    "claude_ai_Magic_Patterns": {
      "disabled": true
    }
  }
}
```

> **Figma를 사용하는 경우**: Figma만 활성화하고 나머지는 비활성화합니다.

#### 방법 2: 프로젝트 레벨에서 MCP 최소화

`.claude/settings.json`(프로젝트 레벨)에서 프로젝트에 필요한 MCP만 명시합니다.

```json
{
  "mcpServers": {
    "serena": {
      "command": "uvx",
      "args": ["--from", "serena-mcp", "serena", "--project", "."]
    }
  }
}
```

#### 방법 3: CLI 전용 사용 시

터미널 CLI(`claude` 명령)로만 사용하면 Cloud AI MCP가 로드되지 않습니다. 웹/데스크탑 앱 대신 CLI를 기본 환경으로 사용하는 것이 가장 깔끔한 방법입니다.

### 2.5 절감 효과

| 시나리오 | 턴당 토큰 절감 | 10턴 Sonnet 비용 절감 |
|----------|-------------|---------------------|
| 전체 Cloud AI MCP 비활성화 | ~5,000~7,000 | $0.15~$0.21 |
| Figma만 유지 | ~3,000~5,000 | $0.09~$0.15 |
| CLI 전용 사용 | ~5,000~7,000 | $0.15~$0.21 |

---

## 3. Deferred Tools 오버헤드

### 3.1 문제 설명

Claude Code는 즉시 로드하지 않는 도구들을 **Deferred Tools**로 관리합니다. 이 도구들의 이름 목록이 매 턴 `<system-reminder>` 태그로 주입되어 모델이 필요할 때 `ToolSearch`로 스키마를 로드할 수 있게 합니다.

```
현재 Deferred Tools 수: 80~100+
  - AskUserQuestion, CronCreate/Delete/List, EnterPlanMode, ...
  - mcp__claude_ai_Canva__* (30+)
  - mcp__claude_ai_Figma__* (17+)
  - mcp__claude_ai_Gmail__* (1+)
  - mcp__claude_ai_Magic_Patterns__* (15+)
  - TaskCreate/Get/List/Update, WebFetch/Search, ...
```

### 3.2 토큰 영향

```
Deferred Tools 목록 자체: ~1,500~2,000 토큰/턴
ToolSearch 호출 시 추가: ~500~1,000 토큰/호출
MCP Instructions 주입: ~2,000~5,000 토큰/턴 (서버 수에 비례)
```

### 3.3 해결 방법

Deferred Tools 목록 자체는 사용자가 직접 제어하기 어렵습니다. **MCP 서버를 비활성화하면 해당 서버의 Deferred Tools도 제거**됩니다.

```
Cloud AI MCP 5개 비활성화 시:
  Canva 도구 30+ 제거
  Figma 도구 17+ 제거
  Gmail 도구 1+ 제거
  Google Calendar 도구 1+ 제거
  Magic Patterns 도구 15+ 제거
  ─────────────────────────
  총 ~65+ Deferred Tools 제거
  절감: ~1,000~1,500 토큰/턴
```

---

## 4. CLAUDE.md 비대화

### 4.1 문제 설명

CLAUDE.md는 매 턴 시스템 프롬프트에 주입됩니다. 글로벌(`~/.claude/CLAUDE.md`) + 프로젝트(`.claude/CLAUDE.md` 또는 루트 `CLAUDE.md`)가 모두 로드됩니다.

### 4.2 크기 기준

| CLAUDE.md 크기 | 토큰 수 (추정) | 판정 |
|---------------|--------------|------|
| ≤ 2KB | ~600 | 🟢 최적 |
| 2~5KB | 600~1,500 | 🟡 양호 |
| 5~10KB | 1,500~3,000 | 🟠 비대 — 축소 권장 |
| > 10KB | > 3,000 | 🔴 과대 — 즉시 축소 |

### 4.3 진단

```bash
# 글로벌 CLAUDE.md 크기
wc -c ~/.claude/CLAUDE.md

# 프로젝트 CLAUDE.md 크기
wc -c CLAUDE.md .claude/CLAUDE.md 2>/dev/null

# 토큰 추정 (한국어: 1KB ≈ 250토큰)
echo "글로벌: $(( $(wc -c < ~/.claude/CLAUDE.md) / 4 )) 토큰 (추정)"
```

### 4.4 경량화 전략

```
1. 에이전트 페르소나 상세 설명 → agents.yaml로 이동 (CLAUDE.md에서 제거)
2. 코딩 컨벤션 상세 → 별도 docs/ 파일로 분리, CLAUDE.md에 1줄 참조만
3. 체크리스트 상세 → skills/ 또는 docs/로 이동
4. 예시 코드 → 최소화 또는 제거
5. 주석/설명 → 테이블/리스트로 압축
```

**목표**: 글로벌 CLAUDE.md 1KB 이내, 프로젝트 CLAUDE.md 3KB 이내.

---

## 5. 메모리 과다 주입

### 5.1 문제 설명

메모리 시스템(`~/.claude/projects/*/memory/`)의 파일이 매 턴 주입됩니다. `MEMORY.md` 인덱스 + 관련 메모리 파일들이 로드됩니다.

### 5.2 설정으로 제어

```json
{
  "memory": {
    "enabled": true,
    "maxFiles": 3
  },
  "autoMemoryEnabled": false
}
```

| 설정 | 기본값 | 권장값 | 효과 |
|------|--------|--------|------|
| `memory.maxFiles` | `5` | `3` | 턴당 메모리 파일 주입 수 제한 |
| `autoMemoryEnabled` | `true` | `false` | 자동 메모리 저장 비활성화 → 불필요한 메모리 축적 방지 |

### 5.3 메모리 정리

```bash
# 메모리 파일 크기 확인
find ~/.claude/projects -name "*.md" -path "*/memory/*" -exec wc -c {} \; | sort -rn

# 오래된/불필요한 메모리 삭제
# (수동으로 확인 후 삭제)
```

---

## 6. settings.json 종합 점검

### 6.0 settings.json vs settings.local.json — 어디에 설정할 것인가

토큰 최적화 설정은 **개인 선호**이므로 `settings.local.json`에 넣는 것을 권장합니다.

| 파일 | 용도 | git 커밋 | 권장 설정 |
|------|------|---------|----------|
| `.claude/settings.json` | 프로젝트 공용 | ✅ 커밋 | hooks, allowedTools, MCP 서버 |
| `.claude/settings.local.json` | 개인 전용 | ❌ .gitignore | 토큰 최적화, Cloud AI MCP 비활성화 |
| `~/.claude/settings.json` | 글로벌 공용 | — | 공통 MCP, 테마 |
| `~/.claude/settings.local.json` | 글로벌 개인 | — | **토큰 최적화 (권장 위치)** |

> **핵심**: `settings.local.json`은 동일 레이어의 `settings.json`과 같은 우선순위이며 `.gitignore`에 포함됩니다. 팀원에게 영향을 주지 않으면서 개인 최적화를 적용할 수 있습니다.

### 6.1 토큰 절감 필수 설정

**권장 위치**: `~/.claude/settings.local.json` (글로벌 개인)

```json
{
  "env": {
    "CLAUDE_CODE_DISABLE_FAST_MODE": "1",
    "CLAUDE_CODE_SUBAGENT_MODEL": "sonnet",
    "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "150000"
  },
  "fastMode": false,
  "memory": {
    "enabled": true,
    "maxFiles": 3
  },
  "maxSkillsPerTurn": 3,
  "showTokenUsage": true,
  "autoCompact": true,
  "mcpServers": {
    "claude_ai_Canva": { "disabled": true },
    "claude_ai_Gmail": { "disabled": true },
    "claude_ai_Google_Calendar": { "disabled": true },
    "claude_ai_Magic_Patterns": { "disabled": true }
  }
}
```

### 6.2 위험 설정 체크리스트

다음 설정이 존재하면 토큰 낭비 위험이 있습니다.

| 설정 | 위험값 | 안전값 | 위험 |
|------|--------|--------|------|
| `fastMode` | `true` 또는 미설정 | `false` | 비용 6x |
| `DISABLE_FAST_MODE` env 없음 | — | `"1"` | Fast Mode 자동 활성화 |
| `SUBAGENT_MODEL` env 없음 | — | `"sonnet"` | 서브에이전트 고비용 모델 |
| `maxSkillsPerTurn` | `5+` | `2~3` | 스킬 과다 주입 |
| `memory.maxFiles` | `5+` | `3` | 메모리 과다 주입 |
| `alwaysThinkingEnabled` | `true` (haiku 사용 시) | 모델에 따라 | 경량 모델에서 thinking 오버헤드 |
| Cloud AI MCP 미비활성화 | — | `disabled: true` | 불필요한 도구 수십 개 주입 |

### 6.3 현재 설정 빠른 진단

```bash
# Fast Mode 차단 확인
echo "DISABLE_FAST_MODE: ${CLAUDE_CODE_DISABLE_FAST_MODE:-❌ 미설정}"

# 서브에이전트 모델 확인
echo "SUBAGENT_MODEL: ${CLAUDE_CODE_SUBAGENT_MODEL:-❌ 미설정 (현재 모델과 동일)}"

# settings.json 핵심 설정 확인
python3 -c "
import json, os
for path in [os.path.expanduser('~/.claude/settings.json'), '.claude/settings.json']:
    try:
        with open(path) as f:
            s = json.load(f)
        print(f'\n=== {path} ===')
        print(f'fastMode: {s.get(\"fastMode\", \"❌ 미설정\")}')
        env = s.get('env', {})
        print(f'DISABLE_FAST_MODE: {env.get(\"CLAUDE_CODE_DISABLE_FAST_MODE\", \"❌ 미설정\")}')
        print(f'SUBAGENT_MODEL: {env.get(\"CLAUDE_CODE_SUBAGENT_MODEL\", \"❌ 미설정\")}')
        mem = s.get('memory', {})
        print(f'memory.maxFiles: {mem.get(\"maxFiles\", \"기본값(5)\")}')
        print(f'maxSkillsPerTurn: {s.get(\"maxSkillsPerTurn\", \"기본값(5)\")}')
        mcps = s.get('mcpServers', {})
        cloud_mcps = [k for k in mcps if 'claude_ai' in k and not mcps[k].get('disabled')]
        print(f'활성 Cloud AI MCP: {len(cloud_mcps)}개 {cloud_mcps if cloud_mcps else \"✅ 없음\"}')
    except FileNotFoundError:
        pass
"
```

---

## 7. 자동 진단 스크립트

### 7.1 빠른 진단

```bash
bash scripts/selfcheck-token-waste.sh
```

이 스크립트는 다음을 자동으로 점검합니다:
- [ ] Fast Mode 차단 설정
- [ ] 서브에이전트 모델 설정
- [ ] Cloud AI MCP 서버 활성화 상태
- [ ] 스킬 크기 감사 (12KB 초과 경고)
- [ ] CLAUDE.md 크기 감사
- [ ] 메모리 파일 수/크기
- [ ] settings.json 위험 설정

### 7.2 출력 예시

```
═══════════════════════════════════════════════
  Claude Code 토큰 낭비 자가진단
═══════════════════════════════════════════════

[1/7] Fast Mode 차단 ........................ ✅ PASS
[2/7] 서브에이전트 모델 ...................... ✅ sonnet
[3/7] Cloud AI MCP ........................... ⚠️  3개 활성 (Canva, Gmail, Calendar)
[4/7] 스킬 크기 ............................. ⚠️  2개 과대 (check-code: 15KB, qa-e2e: 16KB)
[5/7] CLAUDE.md 크기 ........................ ✅ 글로벌 0.8KB, 프로젝트 2.1KB
[6/7] 메모리 ................................ ✅ 파일 3개, 합산 4.2KB
[7/7] settings.json 위험 설정 ............... ⚠️  maxSkillsPerTurn 미설정

───────────────────────────────────────────────
결과: 5/7 PASS, 2/7 WARNING, 0/7 FAIL
예상 턴당 낭비: ~3,500 토큰 ($0.0105/턴 Sonnet)
권장 조치: Cloud AI MCP 비활성화, 스킬 경량화
═══════════════════════════════════════════════
```

---

## 8. 시나리오별 최적화 프로필

> 아래 프로필은 모두 `~/.claude/settings.local.json` 또는 `.claude/settings.local.json`에 넣는 것을 권장합니다. 팀 공유용 `.claude/settings.json`에는 hooks, allowedTools 등 프로젝트 규칙만 유지하세요.

### 8.1 Pro 사용자 (비용 민감)

```json
{
  "env": {
    "CLAUDE_CODE_DISABLE_FAST_MODE": "1",
    "CLAUDE_CODE_SUBAGENT_MODEL": "sonnet",
    "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "150000"
  },
  "fastMode": false,
  "memory": { "enabled": true, "maxFiles": 3 },
  "autoMemoryEnabled": false,
  "maxSkillsPerTurn": 2,
  "showTokenUsage": true,
  "autoCompact": true,
  "mcpServers": {
    "claude_ai_Canva": { "disabled": true },
    "claude_ai_Gmail": { "disabled": true },
    "claude_ai_Google_Calendar": { "disabled": true },
    "claude_ai_Magic_Patterns": { "disabled": true }
  }
}
```

**예상 절감**: 턴당 5,000~8,000 토큰, 세션당 $0.15~$0.24

### 8.2 Max 사용자 (균형)

```json
{
  "env": {
    "CLAUDE_CODE_DISABLE_FAST_MODE": "1",
    "CLAUDE_CODE_SUBAGENT_MODEL": "sonnet",
    "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "200000"
  },
  "fastMode": false,
  "memory": { "enabled": true, "maxFiles": 5 },
  "maxSkillsPerTurn": 3,
  "showTokenUsage": true,
  "mcpServers": {
    "claude_ai_Gmail": { "disabled": true },
    "claude_ai_Google_Calendar": { "disabled": true }
  }
}
```

### 8.3 자동화/NightOps (최소 비용)

```json
{
  "env": {
    "CLAUDE_CODE_DISABLE_FAST_MODE": "1",
    "CLAUDE_CODE_SUBAGENT_MODEL": "sonnet",
    "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1",
    "CLAUDE_CODE_AUTO_COMPACT_WINDOW": "120000"
  },
  "fastMode": false,
  "memory": { "enabled": false },
  "autoMemoryEnabled": false,
  "maxSkillsPerTurn": 1,
  "autoCompact": true,
  "mcpServers": {
    "claude_ai_Canva": { "disabled": true },
    "claude_ai_Figma": { "disabled": true },
    "claude_ai_Gmail": { "disabled": true },
    "claude_ai_Google_Calendar": { "disabled": true },
    "claude_ai_Magic_Patterns": { "disabled": true }
  }
}
```

**예상 절감**: 턴당 7,000~10,000 토큰

---

## 9. 정기 점검 일정

| 주기 | 점검 항목 | 방법 |
|------|----------|------|
| 세션 시작 시 | `/cost` 로 이전 세션 비용 확인 | 수동 |
| 주 1회 | `selfcheck-token-waste.sh` 실행 | 스크립트 |
| 월 1회 | 스킬 크기 감사 + 메모리 정리 | 수동 |
| 버전 업데이트 후 | settings.json 재점검 (새 기본값 확인) | 수동 |
| Cloud AI 서비스 추가 시 | 새 MCP 서버 자동 활성화 확인 | 수동 |

---

## 10. 종합 체크리스트

### 즉시 적용 (5분)

- [ ] `CLAUDE_CODE_DISABLE_FAST_MODE=1` 환경 변수 설정
- [ ] `CLAUDE_CODE_SUBAGENT_MODEL=sonnet` 환경 변수 설정
- [ ] `~/.claude/settings.json`에 `"fastMode": false` 추가
- [ ] `"showTokenUsage": true` 추가 (비용 인식 향상)

### 단기 적용 (30분)

- [ ] 불필요한 Cloud AI MCP `disabled: true` 처리
- [ ] `maxSkillsPerTurn: 3` 설정
- [ ] `memory.maxFiles: 3` 설정
- [ ] CLAUDE.md 크기 확인 및 5KB 초과 시 축소

### 중기 적용 (2시간)

- [ ] 12KB 초과 스킬 경량화 ([가이드](27-skill-lightweight-guide.md))
- [ ] `selfcheck-token-waste.sh` 스크립트 실행 및 결과 반영
- [ ] 메모리 파일 정리 (오래된/불필요 삭제)
- [ ] settings.json 시나리오별 프로필 적용

---

## 다음 단계

1. [스킬 경량화 가이드](27-skill-lightweight-guide.md)
2. [토큰 가격 및 비용 최적화](15-token-pricing-optimization.md)
3. [Fast Mode 가이드](18-fast-mode.md)
4. [Settings 스키마 레퍼런스](20-settings-schema-reference.md)
5. [컨텍스트 윈도우 내부 동작](19-context-window-internals.md)
