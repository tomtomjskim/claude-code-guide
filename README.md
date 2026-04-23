# Claude Code 셋업 가이드

**Claude Code를 효과적으로 사용하기 위한 종합 가이드 및 템플릿**

> **처음이신가요?** → `/tutorial` 명령으로 인터랙티브 튜토리얼을 시작하세요. [튜토리얼 상세 보기](#-튜토리얼-시스템)

---

## 개요

이 레포지토리는 Claude Code 초기 설정부터 팀 워크플로우까지 모든 것을 다룹니다.
비개발자부터 전문가까지, 수준별 학습 경로와 실습 환경을 제공합니다.

### 주요 내용
- PDARR 워크플로우 커맨드 시스템 (/dispatch, /prd, /run, /workflow 등)
- 2단계 복잡도 판단 → 최적 실행 전략 자동 선택
- 멀티 Agent 팀 구성 (단일/병렬/팀 Agent 3전략)
- MCP 서버 설정 (Serena 등)
- 에이전트 페르소나 정의 (9 Core + 7 Specialist Reviewers)
- 문서화 규칙 및 템플릿
- 체크리스트 기반 워크플로우
- **v3.0 신규**: 5-section 표준 프롬프트 템플릿 (Opening/Working Mode/Focus On/Quality Checks/Return/Boundary)
- **v3.0 신규**: Handoff Protocol (에이전트 간 구조화된 컨텍스트 전달)
- **v3.0 신규**: Failure Recovery (retry/escalate/rollback/circuit-breaker)
- **v3.0 신규**: Model Routing (opus/sonnet/haiku 동적 선택)
- **v3.0 신규**: Tiebreaker Protocol (리뷰어 충돌 시 4단계 중재)
- **v3.1 신규**: Cognitive Operations, Confidence Scoring, Token Budget, Event-Driven Hooks, Progressive Escalation, Adversarial Pair Review
- **v3.2 신규**: Safety Hooks 실체화 (careful/freeze/event-trigger → settings.json 등록)
- **v3.2 신규**: Completion Status Protocol (4상태 핸드오프 v2.0)
- **v3.2 신규**: Autonomy Levels (5단계 L0~L4, NightOps trusted context)
- **v3.2 신규**: Blast-Radius Classification (4단계) + Diff-Aware Phase 0
- **v3.2 신규**: Session Resume (파일 기반 워크플로우 상태 관리)
- **v3.2 참조**: [gstack](https://github.com/garrytan/gstack) (Garry Tan's AI workflow platform) 실체화 패턴
- **v3.2 신규**: **18개 Custom Skills** — PDARR 워크플로우를 실제 슬래시 커맨드(`.claude/skills/`)로 제공. 설치 스크립트로 프로젝트에 즉시 적용.
- **v3.3 신규**: 스킬 경량화 가이드 — 스킬 크기 기준, 본체/참조 분리 전략, 경량 템플릿
- **v3.3 신규**: 토큰 낭비 자가진단 — Cloud AI MCP 자동 활성화 감지, 7대 낭비 요소, 시나리오별 프로필
- **v3.3 신규**: `selfcheck-token-waste.sh` 자동 진단 스크립트 — 7항목 자동 점검
- **v3.3 신규**: 하네스 엔지니어링 가이드 — settings/hooks/CLAUDE.md/skills/memory 5컴포넌트 통합 설계
- **v3.3 신규**: Advisor Strategy 가이드 — executor+advisor 모델 패턴, API 구현, PDARR 연계
- **v3.3 신규**: 듀얼 모드 디자인 전략 — SYSTEMATIC/CREATIVE 모드 자동 판별, design-gate.sh 자동 검사, `/design-creative` 스킬
- **v3.3 신규**: 디자인 시스템 확장 규칙 — 토큰 추가/변경 절차, 폰트 수정 규칙, 체크리스트
- **v3.3 신규**: Hook 보일러플레이트 시스템 — 4종 커스터마이징 가능 템플릿 + `install-hooks.sh` 인스톨러
- **v3.3 신규**: 서브에이전트 효율성 가이드 — 12가지 전략, A/B 벤치마크(55% 토큰 절감), Tiered Dispatch, Result Pipe, Bash 프리플라이트
- **v3.3 신규**: `preflight-collect.sh` 사전 수집 스크립트 — 서브에이전트 탐색 턴 제거용
- **v3.3 수정**: docs 넘버링 충돌 해소 (15 → 15/15a), settings.local.json 개인 설정 분리 권장
> v3.2부터 이 레포가 [claude-code-team-system](https://github.com/tomtomjskim/claude-code-team-system)을 통합한 **단일 소스**입니다.

---

## 레포 구조

```
claude-code-guide/
├── skills/               # 🆕 18개 PDARR 워크플로우 커스텀 스킬 (.claude/skills/ 호환)
│   ├── dispatch/         # 스마트 라우터
│   ├── prd/              # PRD 작성
│   ├── analyze/          # 코드베이스 분석
│   ├── spec/             # 기술 명세서
│   ├── run/              # 구현 (Orchestrator-Worker)
│   ├── check-code/       # 코드 검수 (6단계)
│   ├── workflow/         # PDARR 오케스트레이터
│   ├── design-creative/  # 🆕 CREATIVE 모드 디자인 스킬
│   └── ...               # + 10개 더 (test, reflect, stage 등)
├── agents.yaml           # 16 에이전트 설정 (모델 라우팅, 토큰 예산, blast-radius)
├── agents/               # 15 서브에이전트 frontmatter 정의 (.md)
├── prompts/              # 16 에이전트 상세 프롬프트 (v3.2, 200줄+)
├── workflows/            # 9 워크플로우 (standard, quick-fix, code-review 등)
├── context/              # 핸드오프 v2.0, 세션 스키마, digest 포맷
├── .claude/rules/        # 🆕 경로 기반 규칙 (design-mode.md 등)
├── hooks/                # Safety hooks + event-driven-review
│   ├── boilerplates/     # 🆕 커스터마이징 가능 Hook 템플릿 4종
│   ├── event-driven-review.yaml
│   └── scripts/          # v3.2 레퍼런스 구현
├── scripts/              # validate-system.sh + install-skills.sh + selfcheck-token-waste.sh + preflight-collect.sh
├── docs/                 # 33편 가이드 문서 (v3.3: 서브에이전트 효율성, 디자인 전략, 스킬 경량화 등)
├── templates/            # 프로젝트 구조, 체크리스트, CLAUDE.md 템플릿
├── QUICKSTART.md
└── README.md
```

---

## 빠른 시작

### 1. 스킬 설치 (프로젝트별)

```bash
# 클론
git clone https://github.com/tomtomjskim/claude-code-guide.git
cd claude-code-guide

# 대상 프로젝트에 스킬 설치 (한 줄)
bash scripts/install-skills.sh /path/to/your-project

# 확인: 프로젝트에서 /dispatch, /run, /check-code 등 즉시 사용 가능
```

스킬만 설치하면 PDARR 워크플로우를 바로 쓸 수 있습니다.
Hook(안전장치)과 팀 에이전트까지 사용하려면 아래 단계도 진행하세요.

### 2. Hook 설치 (권장)

```bash
# 전체 Hook 설치 — 서브에이전트 제어, 파괴적 명령 차단, 보호 파일 보호, 감사 로그
bash scripts/install-hooks.sh /path/to/your-project

# 필수 안전장치만 빠르게
bash scripts/install-hooks.sh --preset minimal /path/to/your-project
```

설치 후 각 Hook 파일의 `🔧 커스터마이징 영역`을 프로젝트에 맞게 수정하세요.
상세 가이드: [hooks/README.md](hooks/README.md)

### 3. 팀 시스템 설치 (선택)

```bash
# 스킬 + 팀 시스템 한 번에 설치
bash scripts/install-skills.sh --team /path/to/your-project

# 또는 팀 시스템만 수동 설치
mkdir -p ~/.claude/team
cp agents.yaml ~/.claude/team/
cp -r prompts/ ~/.claude/team/prompts/
cp -r workflows/ ~/.claude/team/workflows/
cp -r context/ ~/.claude/team/context/
cp -r hooks/ ~/.claude/team/hooks/
cp -r scripts/ ~/.claude/team/scripts/
cp -r agents/ ~/.claude/agents/
chmod +x ~/.claude/team/hooks/scripts/*.sh
chmod +x ~/.claude/team/scripts/*.sh
```

### 4. settings.json 설정 (팀 시스템 사용 시)

```json
{
  "alwaysThinkingEnabled": true,
  "hooks": {
    "PreToolUse": [
      { "matcher": "Bash", "hooks": [{ "type": "command", "command": "~/.claude/team/hooks/scripts/safety-careful.reference.sh" }] },
      { "matcher": "Edit|Write", "hooks": [{ "type": "command", "command": "~/.claude/team/hooks/scripts/safety-freeze.reference.sh" }] }
    ],
    "PostToolUse": [
      { "matcher": "Edit|Write", "hooks": [{ "type": "command", "command": "~/.claude/team/hooks/scripts/event-review-trigger.reference.sh" }] }
    ]
  },
  "mcpServers": {
    "serena": { "command": "uvx", "args": ["--from", "serena-mcp", "serena", "--project", "."] }
  }
}
```

### 5. 검증 (팀 시스템 사용 시)

```bash
bash ~/.claude/team/scripts/validate-system.sh
# 18 categories, 0 errors expected
```

### 5. 프로젝트 초기화

```bash
cp -r templates/project-structure/* /your/project/
cp templates/CLAUDE.md /your/project/.claude/CLAUDE.md
```

---

## 문서 목록

| # | 문서 | 설명 |
|---|------|------|
| 00 | [셋업 체크리스트](docs/00-setup-checklist.md) | 초기 설정 체크리스트 |
| 01 | [MCP 설정](docs/01-mcp-configuration.md) | Serena 등 MCP 설정 |
| 02 | [커맨드/스킬](docs/02-commands-skills.md) | 기본 슬래시 커맨드 및 스킬 구조 |
| 03 | [개발 파이프라인](docs/03-development-pipeline.md) | 기본 파이프라인 (요구사항 → 설계 → 검수 → 구현) |
| 04 | [문서화 규칙](docs/04-documentation-rules.md) | 세션 독립적 문서화 |
| 05 | [에이전트 페르소나](docs/05-agent-personas.md) | PM, Architect, Developer, QA 등 15개 Agent |
| 06 | [프로젝트 구조](docs/06-project-structure.md) | 표준 프로젝트 구조 |
| 07 | [CLAUDE.md 템플릿](docs/07-claude-md-template.md) | 프로젝트 설정 템플릿 |
| 08 | [관련 프로젝트](docs/08-related-projects.md) | Serena MCP, Agent Monitor 등 |
| 09 | [추천 플러그인](docs/09-recommended-plugins.md) | Superpowers, Context7 등 |
| 10 | [코드 리뷰 시스템](docs/10-code-review-system.md) | 전문 리뷰어 6명, 6단계, 3프리셋 |
| 11 | [Workflow Commands](docs/11-workflow-commands.md) | PDARR 워크플로우 커맨드 요약 |
| 12 | [v3.0 아키텍처](docs/12-v3-architecture.md) | v3.0 시스템 아키텍처 (핸드오프, 실패 복구, 모델 라우팅) |
| 13 | [핸드오프 & 실패 복구](docs/13-handoff-and-failure.md) | 실전 가이드 (설정, 예시, 템플릿) |
| **14** | **[프리셋 시스템](docs/14-preset-system.md)** | **깊이(depth) x 실행(mode) 2축 체계. analyze/spec/check-code 프리셋** |
| -- | [Workflow Guide (상세)](.claude/workflow-commands-guide.md) | 커맨드 구축 종합 가이드 |
| -- | **[Skills README](skills/README.md)** | **18개 커스텀 스킬 설치/커스터마이징 가이드** |
| -- | **[Quick Start Guide](QUICKSTART.md)** | **실전 활용 패턴, 프리셋 선택, 안티패턴** |
| -- | **[v3 Changelog](docs/v3-changelog.md)** | **v3.0→v3.2 전체 변경 이력 (릴리즈 노트)** |

### 소스 분석 기반 심화 가이드 (v2.1.88)

Claude Code v2.1.88 소스 분석에서 확인된 내부 동작과 최적화 전략입니다.

| # | 문서 | 설명 |
|---|------|------|
| 15 | [토큰 가격표 & 비용 최적화](docs/15-token-pricing-optimization.md) | 모델별 단가, 서브에이전트 전략, 플랜 예산 |
| 16 | [사용량 한도 & Rate Limit](docs/16-usage-limits-ratelimit.md) | 5h/7d 윈도우, Early Warning, Overage |
| 17 | [환경변수 레퍼런스](docs/17-environment-variables.md) | 비공개 포함 15+ 환경변수 |
| 18 | [Fast Mode 상세 & 비활성화](docs/18-fast-mode.md) | 6x 비용, 비활성화 방법, 권장 설정 |
| 19 | [컨텍스트 윈도우 내부](docs/19-context-window-internals.md) | auto-compact, 압축 구조, 재주입 |
| 20 | [Settings 전체 스키마](docs/20-settings-schema-reference.md) | 60+ 키, 4단계 병합, 권장 조합 |
| 21 | [Memory 시스템 내부](docs/21-memory-system-internals.md) | 한도, 랭킹, frontmatter 최적화 |
| 22 | [Agent Frontmatter 스키마](docs/22-agent-frontmatter-schema.md) | 15개 필드 완전 레퍼런스 |
| 23 | [도구 동시성 모델](docs/23-tool-concurrency-model.md) | 병렬/직렬 분류, 성능 팁 |
| 24 | [Retry & 에러 복구](docs/24-retry-error-recovery.md) | 재시도 상수, 에러 분류, 에스컬레이션 |
| 25 | [Permission 결정 트리](docs/25-permission-system.md) | 5모드, AST 파싱, ML 분류기 |
| 26 | [Coordinator Mode](docs/26-coordinator-mode.md) | 멀티에이전트 오케스트레이션 |

### v3.3 가이드

| # | 문서 | 설명 |
|---|------|------|
| 15a | [Codex 플러그인](docs/15a-codex-plugin.md) | Codex CLI 통합 — 리뷰/디버깅/태스크 핸드오프 |
| 27 | [스킬 경량화](docs/27-skill-lightweight-guide.md) | 스킬 크기 기준, 본체/참조 분리 전략 |
| 28 | [토큰 낭비 자가진단](docs/28-token-waste-selfcheck.md) | 7대 낭비 요소, 자동 진단 스크립트 |
| 29 | [하네스 엔지니어링](docs/29-harness-engineering.md) | settings/hooks/CLAUDE.md/skills/memory 5컴포넌트 통합 설계 |
| 30 | [Advisor Strategy](docs/30-advisor-strategy.md) | executor+advisor 모델 패턴, API 구현 |
| 31 | [듀얼 모드 디자인 전략](docs/31-design-strategy.md) | SYSTEMATIC/CREATIVE 모드 판별, 프로젝트별 커스텀 게이트 가이드 |
| 32 | [디자인 시스템 확장 규칙](docs/32-design-system-extension.md) | 토큰 추가/변경 절차, 폰트 수정 규칙 |
| 33 | [서브에이전트 효율성](docs/33-subagent-efficiency.md) | 12가지 전략, A/B 벤치마크, Tiered Dispatch, Result Pipe |

---

## 튜토리얼 시스템

비개발자부터 전문가까지, **실습 중심**의 단계별 학습 코스.

### 시작하기
```
/tutorial              # 레벨 자동 판별 (3가지 질문)
/tutorial beginner     # 초보자 코스 직행
/tutorial developer    # 개발자 코스 직행
/tutorial expert       # 전문가 코스 직행
```

### 학습 경로

| 코스 | 대상 | 미션 수 | 소요 시간 | 실습 프로젝트 |
|------|------|--------|----------|-------------|
| **초보자** | 비개발자, Claude Code 처음 | 5개 | ~15분 | `hello-world` (HTML) |
| **개발자** | 개발 경험 있음, 워크플로우 학습 | 5개 | ~35분 | `todo-app` (JS) |
| **전문가** | PDARR 숙지, 고급 활용 | 3개 | ~50분 | `api-service` (Node.js) |

### 초보자 코스 미리보기
```
1. 첫 대화       — "이 파일이 뭐예요?" (파일 읽기)
2. CSS 버그 수정  — "이거 왜 안 보여요?" (문제 설명 → 자동 수정)
3. 내용 바꿔보기  — "내 걸로 만들기" (여러 파일 수정)
4. 새 파일 만들기 — "이런 페이지 만들어줘" (파일 생성)
5. Git 저장      — "작업 기록 남기기" (버전 관리)
```

### 추가 도구
```
/tutorial cheatsheet   # 수준별 치트시트
/tutorial glossary     # 용어 사전 (일상 비유)
/tutorial status       # 전체 학습 경로 보기
/tutorial next         # 다음 미션 안내
```

### 튜토리얼 구조
```
tutorial/
├── sandbox/              # 실습 프로젝트 (안전하게 실험 가능)
│   ├── hello-world/      # 초보자: HTML 페이지 (의도적 버그 포함)
│   ├── todo-app/         # 개발자: 할 일 관리 앱
│   └── api-service/      # 전문가: REST API 서버
├── missions/             # 단계별 미션 가이드
│   ├── beginner/         # 5개 미션
│   ├── developer/        # 5개 미션
│   └── expert/           # 3개 미션
├── cheatsheets/          # 수준별 한 장 요약
│   ├── beginner-cheatsheet.md
│   ├── developer-cheatsheet.md
│   └── expert-cheatsheet.md
└── glossary.md           # 용어 사전
```

### 소스 분석 기반 심화 가이드 (v2.1.88)

Claude Code v2.1.88 소스 분석에서 확인된 내부 동작과 최적화 전략입니다.

| # | 문서 | 설명 |
|---|------|------|
| 15 | [토큰 가격표 & 비용 최적화](docs/15-token-pricing-optimization.md) | 모델별 단가, 서브에이전트 전략, 플랜 예산 |
| 16 | [사용량 한도 & Rate Limit](docs/16-usage-limits-ratelimit.md) | 5h/7d 윈도우, Early Warning, Overage |
| 17 | [환경변수 레퍼런스](docs/17-environment-variables.md) | 비공개 포함 15+ 환경변수 |
| 18 | [Fast Mode 상세 & 비활성화](docs/18-fast-mode.md) | 6x 비용, 비활성화 방법, 권장 설정 |
| 19 | [컨텍스트 윈도우 내부](docs/19-context-window-internals.md) | auto-compact, 압축 구조, 재주입 |
| 20 | [Settings 전체 스키마](docs/20-settings-schema-reference.md) | 60+ 키, 4단계 병합, 권장 조합 |
| 21 | [Memory 시스템 내부](docs/21-memory-system-internals.md) | 한도, 랭킹, frontmatter 최적화 |
| 22 | [Agent Frontmatter 스키마](docs/22-agent-frontmatter-schema.md) | 15개 필드 완전 레퍼런스 |
| 23 | [도구 동시성 모델](docs/23-tool-concurrency-model.md) | 병렬/직렬 분류, 성능 팁 |
| 24 | [Retry & 에러 복구](docs/24-retry-error-recovery.md) | 재시도 상수, 에러 분류, 에스컬레이션 |
| 25 | [Permission 결정 트리](docs/25-permission-system.md) | 5모드, AST 파싱, ML 분류기 |
| 26 | [Coordinator Mode](docs/26-coordinator-mode.md) | 멀티에이전트 오케스트레이션 |

---

## 핵심 개념

### PDARR 워크플로우

**Plan → Document → Act → Review → Reflect**

> Canonical 순차: [`CLAUDE.md` §PDARR + preset system](CLAUDE.md#pdarr--preset-system) `Flow` bullet. 아래 다이어그램은 분기 시각화 보조.

모든 작업은 복잡도에 따라 이 사이클의 전체 또는 일부를 거친다.
`/dispatch`가 작업 크기에 맞는 사이클 범위를 자동 결정한다.

```
사용자 요청
    │
    ▼
[/dispatch] ← 30초 이내 판단
    │
    ├─ Trivial ─→ 직접 수정
    ├─ Simple ──→ /run → /check-code → /stage
    ├─ Medium ──→ /analyze → /run → /check-code → /stage
    ├─ Complex ─→ /prd → /analyze → /workflow (팀 Agent)
    └─ Review ──→ /check-spec 또는 /check-code
```

### 커맨드 전체 맵

```
[시작점]    /dispatch ─── 스마트 라우터

[계획]      /prd ─── /analyze ─── /spec

[실행]      /test ─── /run

[검증]      /check-spec ─── /check-code ─── /qa-test

[회고]      /reflect ─── /complete

[유틸]      /stage ─── /flow ─── /workflow
```

### 2단계 판단 시스템

| 단계 | 커맨드 | 판단 기반 | 출력 |
|------|--------|----------|------|
| 1차 | `/prd` | 요구사항 텍스트 | 복잡도 추정, 병렬화 가능성 |
| 2차 | `/analyze` | 코드베이스 실제 분석 | 1차 보정, 팀 구성 추천 |

### 실행 전략 3가지

| 전략 | 조건 | 도구 | 파일 규모 |
|------|------|------|----------|
| A: 단일 Agent | Simple~Medium | 커스텀 커맨드만 | ~3개 |
| B: 병렬 Task | Medium | Task() | 4-6개 |
| C: 팀 Agent | Complex | TeamCreate + Task + SendMessage | 7개+ |

> 상세 가이드: [`.claude/workflow-commands-guide.md`](.claude/workflow-commands-guide.md)

---

### 문서 구조

```
docs/
├── prd/               # PRD 문서 (요구사항 + 1차 판단)
├── spec/              # 기술 설계
│   ├── architecture/  # 아키텍처
│   ├── api/           # API
│   └── ui/            # UI/UX
├── todo/              # 대기중
├── history/           # 세션 히스토리
├── qa-reports/        # QA 리포트
└── complete/          # 완료 (통합 정리)
    └── summary.md     # 전체 요약
```

### 에이전트 페르소나

#### Core Agents (9개)
| 에이전트 | 역할 | 산출물 |
|---------|------|--------|
| PM | 요구사항 분석, 태스크 분해, 리뷰 판정 | REQ-XXX.md |
| Explorer | 코드 탐색, 영향도 분석 | 분석 리포트 |
| Architect | 시스템 설계 | spec/*.md |
| Developer | 구현 | 코드, 테스트 |
| QA | 검수 | 검수 리포트 |
| DBA | DB 스키마, 마이그레이션 | schema.sql |
| Designer | UI/UX 설계 (SYSTEMATIC/CREATIVE 듀얼 모드) | component-spec.md |
| Publisher | 빌드/배포 | deployment-log.md |
| Documenter | 문서화 | DONE-XXX.md |

#### Specialist Reviewers (7개, v3.0)
| 리뷰어 | 페르소나 | 핵심 관점 |
|--------|---------|----------|
| Security Reviewer | Security Sentinel | "공격자에게 노출되면?" |
| Performance Reviewer | Performance Prophet | "트래픽 10배면?" |
| Test Coverage Reviewer | Test Guardian | "이 테스트가 진짜 검증하나?" |
| Accessibility Reviewer | Access Advocate | "장애인도 쓸 수 있나?" |
| UX Reviewer | UX Harmonizer | "사용자가 혼란스럽지 않나?" |
| API Reviewer | API Arbiter | "1년 후에도 호환되나?" |
| Code Reviewer | Code Craftsman | "코드 품질과 유지보수성이 충분한가?" |

> v3.0부터 각 페르소나는 5-section 표준 템플릿(Opening/Working Mode/Focus On/Quality Checks/Return/Boundary)을 따릅니다.

### 프리셋 시스템

**깊이(depth) × 실행(mode) 2축 독립 제어.** canonical 규칙은 [`CLAUDE.md` §PDARR + preset system](CLAUDE.md#pdarr--preset-system), 상세 체계는 [`docs/14-preset-system.md`](docs/14-preset-system.md).

**6개 스킬에 공통 적용** (`analyze`, `spec`, `check-spec`, `check-code`, `qa-test`, `qa-e2e`):

```
깊이:  --quick ← standard → --thorough
실행:  단일    ← 기본    → --team

--team 단독 = thorough + 팀 (기본 최대 성능, qa-test는 --full)
qa-e2e는 depth 축 미적용 — --tc TC-N으로 범위 제어
```

```
/analyze --team {기능}              # 팀 분석
/check-code --team --quick {모듈}   # 팀 + 빠른 스캔 조합
/qa-e2e --team {모듈}               # 팀 E2E (전 TC 또는 --tc 필터)
```

6단계 코드 리뷰 Phase 매핑 상세: [코드 리뷰 시스템](docs/10-code-review-system.md).

---

## 템플릿

### 프로젝트 템플릿
- [프로젝트 구조](templates/project-structure/) - 표준 디렉토리 구조
- [CLAUDE.md](templates/CLAUDE.md) - 프로젝트 설정 파일
- [체크리스트](templates/checklists/) - 워크플로우 체크리스트

### 에이전트 템플릿 (v3.0)
- [agents-v3.yaml](templates/agents-v3.yaml) - 16개 에이전트 정의 + Model Routing + Team Templates
- [5-Section 프롬프트 템플릿](templates/prompts/TEMPLATE.md) - 새 에이전트 작성용
- [16개 구체적 프롬프트](templates/prompts/) - Core 9개 + Specialist 7개 즉시 사용 가능
- [Handoff Protocol](templates/handoff-protocol.yaml) - 에이전트 간 컨텍스트 전달
- [Failure Policy](templates/failure-policy.yaml) - 실패 복구 정책
- [Tiebreaker Protocol](templates/tiebreaker-protocol.md) - 리뷰어 의견 충돌 중재

### 문서 템플릿
- [요구사항 (REQ-XXX)](templates/docs/REQ-template.md)
- [설계 문서](templates/docs/SPEC-template.md)
- [태스크 (TASK-XXX)](templates/docs/TASK-template.md)
- [완료 (DONE-XXX)](templates/docs/DONE-template.md)
- [세션 히스토리](templates/docs/SESSION-template.md)

---

## MCP 권장 설정

### 필수
- **Serena MCP** - 시맨틱 코드 분석/편집

> 멀티 에이전트 오케스트레이션은 Claude Code 네이티브 도구(Task, Agent, TeamCreate, SendMessage)로 처리합니다. Team Orchestrator MCP는 더 이상 권장하지 않습니다.

### 설정 예시
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

---

## 추천 플러그인

### 필수
- **[Superpowers](https://github.com/obra/superpowers)** - TDD, 체계적 디버깅, 서브에이전트 개발 워크플로우 (14개 스킬)
  - 설치: `claude plugin marketplace add obra/superpowers-marketplace && claude plugin install superpowers@superpowers-marketplace`
  - 주요 기능: brainstorming, writing-plans, executing-plans, TDD, systematic-debugging, dispatching-parallel-agents 등
- **Skill Creator** (Anthropic 공식) - 스킬 생성/테스트/개선/벤치마크
  - 설치: `claude plugin install skill-creator@claude-plugins-official`
  - 4가지 모드: Create, Eval, Improve, Benchmark
  - 슬래시 커맨드: `/skill-creator`

### 추천 (추가 검토)
- **[Context7](https://github.com/upstash/context7)** - 최신 문서 검색/참조
- **[Superpowers Lab](https://github.com/obra/superpowers-lab)** - 실험적 스킬 확장
- **[Superpowers Chrome](https://github.com/obra/superpowers-chrome)** - 브라우저 직접 제어

자세한 내용은 [추천 플러그인 가이드](docs/09-recommended-plugins.md)를 참조하세요.

---

## 사용 예시

### PDARR 워크플로우로 새 기능 개발

```
사용자: "수수료 정산 시스템 구현해줘"

/dispatch "수수료 정산 시스템"
→ Complex 판정 → /prd 경로 추천

/prd 수수료 정산
→ 요구사항 구조화
→ 1차 판단: Complex (파일 8개+, 3레이어)
→ docs/prd/commission/prd.md 생성

/analyze commission
→ 코드베이스 분석
→ 2차 판단: 팀 Agent 추천 (백엔드/프론트 병렬)
→ 팀 구성: analyzer, backend-dev, frontend-dev, reviewer

/workflow
→ TeamCreate → TaskCreate → 병렬 Agent 실행
→ 백엔드/프론트엔드 동시 구현
→ /check-code 자동 검수
→ /reflect → /complete → /stage
```

### 간단한 버그 수정

```
사용자: "상품 목록 정렬 버그 수정해줘"

/dispatch "정렬 버그"
→ Simple 판정 → /run 직행

/run
→ 직접 수정 → 테스트

/check-code → /stage
```

---

## 관련 프로젝트

### MCP 서버

| 프로젝트 | 설명 | 용도 |
|---------|------|------|
| [Serena MCP](https://github.com/serena-ai/serena-mcp) | 시맨틱 코드 분석/편집 | 필수 - 코드 탐색, 심볼 분석, 리팩토링 |

### 모니터링

| 프로젝트 | 설명 | 용도 |
|---------|------|------|
| [Agent Orchestra Monitor](https://github.com/tomtomjskim/agent-orchestra-monitor) | 실시간 에이전트 모니터링 대시보드 | 에이전트 활동 시각화, 태스크 추적 |

### 팀 시스템 (Production-Ready)

| 프로젝트 | 설명 | 용도 |
|---------|------|------|
| **[claude-code-team-system](https://github.com/tomtomjskim/claude-code-team-system)** | **16 에이전트 + 8 워크플로우 프로덕션 오케스트레이션 (v3.1)** | **이 가이드의 에이전트/워크플로우를 즉시 사용 가능한 설정 파일로 제공. Token Budget, Adversarial Review, Cognitive Ops 포함** |

### 참조 자료

| 프로젝트 | 설명 | 용도 |
|---------|------|------|
| [awesome-codex-subagents](https://github.com/awesome-codex-subagents/awesome-codex-subagents) | 에이전트 프롬프트 설계 참조 (136 agents, 5-section template 원본) | v3.0 5-section 표준 템플릿 설계 기반 |

### 에코시스템 구성도

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Claude Code                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐    ┌─────────────────────────────────────────────┐   │
│  │  Serena MCP  │    │  Claude Code Native Multi-Agent Tools        │   │
│  │              │    │                                              │   │
│  │ - 코드 분석  │    │  Task()        - 서브에이전트 스폰           │   │
│  │ - 심볼 탐색  │    │  Agent()       - 에이전트 실행              │   │
│  │ - 리팩토링   │    │  TeamCreate()  - 팀 생성                    │   │
│  │              │    │  SendMessage() - 에이전트 간 통신           │   │
│  └──────────────┘    └──────────────────────┬──────────────────────┘   │
│                                             │                            │
│                                             ▼                            │
│                              ┌───────────────────────┐                  │
│                              │  Agent Orchestra      │                  │
│                              │  Monitor              │                  │
│                              │  - 실시간 대시보드    │                  │
│                              │  - 태스크 추적        │                  │
│                              │  - 이벤트 로그        │                  │
│                              └───────────────────────┘                  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  PDARR Workflow Commands (.claude/commands/)                      │  │
│  │  /dispatch → /prd → /analyze → /spec → /run → /check-code       │  │
│  │  → /reflect → /complete → /stage                                  │  │
│  │                                                                    │  │
│  │  + Superpowers Plugin (14 Skills)                                 │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  v3.0 Features                                                    │  │
│  │  Handoff Protocol  - 에이전트 간 구조화된 컨텍스트 전달           │  │
│  │  Failure Recovery  - retry/escalate/rollback/circuit-breaker     │  │
│  │  Model Routing     - opus/sonnet/haiku 동적 선택                  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  v3.1 (claude-code-team-system)                                  │  │
│  │  Cognitive Ops    - 에이전트별 고유 추론 전략                     │  │
│  │  Confidence Score - 신뢰도 기반 발견사항 필터링                   │  │
│  │  Token Budget     - 비용 한도 + 서킷 브레이커                    │  │
│  │  Adversarial Pair - 상충 관점 교차 검증                          │  │
│  │  Event Hooks      - 고위험 파일 변경 시 자동 리뷰                │  │
│  │  Retrospective    - PM 자기 개선 피드백 루프                     │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

자세한 내용은 [관련 프로젝트 가이드](docs/08-related-projects.md)를 참조하세요.

---

## License

MIT
