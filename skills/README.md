# PDARR Workflow Skills

Claude Code 프로젝트에 즉시 적용 가능한 **PDARR(Plan-Document-Act-Review-Reflect)** 워크플로우 스킬 모음.

---

## 설치

```bash
# 레포 클론
git clone https://github.com/tomtomjskim/claude-code-guide.git
cd claude-code-guide

# 대상 프로젝트에 스킬 설치
bash scripts/install-skills.sh /path/to/your-project

# 특정 스킬만 설치
bash scripts/install-skills.sh --skills dispatch,run,check-code /path/to/your-project

# 팀 시스템(에이전트, 워크플로우)까지 포함
bash scripts/install-skills.sh --team /path/to/your-project

# 사용 가능한 스킬 목록
bash scripts/install-skills.sh --list
```

설치 후 프로젝트의 `.claude/skills/`에 스킬이 추가되며, Claude Code에서 슬래시 커맨드로 즉시 사용 가능합니다.

---

## 스킬 목록

### Plan 단계

| 스킬 | 커맨드 | 역할 |
|------|--------|------|
| **dispatch** | `/dispatch {작업}` | 복잡도 판단 → 최적 실행 경로 라우팅 |
| **prd** | `/prd {기능}` | PRD 문서 생성 + 1차 복잡도 판단 |
| **analyze** | `/analyze {기능}` | 코드베이스 분석 + 2차 복잡도 판단 + 실행 전략 |
| **spec** | `/spec` | 기술 명세서 작성 (architecture, API, DB schema) |

### Act 단계

| 스킬 | 커맨드 | 역할 |
|------|--------|------|
| **test** | `/test {모듈}` | TDD 테스트 케이스 작성 (Red 단계) |
| **run** | `/run {작업}` | 구현 (Orchestrator-Worker 패턴) |

### Review 단계

| 스킬 | 커맨드 | 역할 |
|------|--------|------|
| **check-spec** | `/check-spec {모듈}` | 설계문서 ↔ 코드베이스 일관성 검수 |
| **check-code** | `/check-code {모듈}` | 코드 품질 6단계 리뷰 |
| **qa-test** | `/qa-test {기능}` | 종합 QA 자동화 (4단계 난이도) |
| **qa-e2e** | `/qa-e2e {모듈}` | E2E 비즈니스 로직 + DB 검증 |

### Reflect 단계

| 스킬 | 커맨드 | 역할 |
|------|--------|------|
| **reflect** | `/reflect` | 자기성찰 + Memory 저장 + docs/complete/ |
| **complete** | `/complete` | 임시 파일 정리 + 문서 통합 |

### Utility

| 스킬 | 커맨드 | 역할 |
|------|--------|------|
| **stage** | `/stage` | Git 스테이징 + 커밋 메시지 제안 |
| **flow** | `/flow` | 세션 컨텍스트 정리 |
| **organize-docs** | `/organize-docs` | 누락된 문서화 보완 |
| **workflow** | `/workflow {기능}` | PDARR 전체 사이클 자동 실행 |
| **profile** | `/profile {대상}` | 성능 프로파일링 코드 삽입 |

---

## 프리셋 시스템

`analyze`, `spec`, `check-spec`, `check-code`, `qa-test`, `qa-e2e`는 **2축 프리셋**을 지원합니다.

```
깊이(depth):  --quick ← standard(기본) → --thorough
실행(mode):   단일    ← 기본           → --team
```

```bash
/analyze --quick {버그}          # 빠른 분석
/analyze {기능}                  # 표준 분석
/analyze --thorough {기능}       # 심층 분석
/analyze --team {기능}           # 팀 에이전트 분석 (최대 깊이)
/check-code --team --quick {모듈} # 팀 + 빠른 스캔 (조합 가능)
```

---

## 프로젝트 커스터마이징

### CUSTOMIZE 블록

각 스킬의 기술 스택 의존 부분은 `<!-- CUSTOMIZE: ... -->` HTML 주석으로 표시되어 있습니다.

```markdown
<!-- CUSTOMIZE: Technology Stack Rules
The section below contains example rules for a PHP/MySQL project.
Replace with your project's technology stack rules.
-->
```

### 커스터마이징 순서

1. **즉시 사용 가능** (커스터마이징 불필요):
   - dispatch, flow, stage, reflect, complete, organize-docs, workflow, prd

2. **프로젝트 설정 경로 수정** (5분):
   - analyze, spec, check-spec, test, profile
   - `.claude/coding_guidelines.md` 등의 경로를 본인 프로젝트에 맞게 조정

3. **기술 스택 규칙 교체** (30분):
   - run, check-code, qa-test, qa-e2e
   - CUSTOMIZE 블록 내의 PHP/MySQL 예시를 본인 스택으로 교체

### 기술 스택별 교체 예시

**Python/Django 프로젝트:**
```markdown
## 코드 표준
- Python 3.11+ 타입 힌트 사용
- Django ORM (raw SQL 금지)
- pytest 기반 테스트
- ruff 린팅
```

**Node.js/TypeScript 프로젝트:**
```markdown
## 코드 표준
- TypeScript strict mode
- ESLint + Prettier
- Jest 기반 테스트
- Prisma ORM
```

**React/Next.js 프로젝트:**
```markdown
## 코드 표준
- TypeScript + ESLint
- React Server Components 우선
- Tailwind CSS (인라인 스타일 금지)
- Vitest + Testing Library
```

---

## 디렉토리 구조

```
skills/
├── README.md              # 이 파일
├── dispatch/SKILL.md      # 스마트 라우터
├── prd/SKILL.md           # PRD 작성
├── analyze/SKILL.md       # 분석 + 실행 전략
├── spec/SKILL.md          # 기술 명세서
├── test/SKILL.md          # TDD 테스트
├── run/SKILL.md           # 구현 (Orchestrator-Worker)
├── check-spec/SKILL.md    # 설계 검수
├── check-code/SKILL.md    # 코드 검수 (6단계)
├── qa-test/SKILL.md       # QA 자동화
├── qa-e2e/SKILL.md        # E2E 테스트
├── reflect/
│   ├── SKILL.md           # 자기성찰
│   └── references/
│       └── report-template.md
├── complete/SKILL.md      # 작업 완료 정리
├── stage/SKILL.md         # Git 스테이징
├── flow/SKILL.md          # 컨텍스트 정리
├── organize-docs/
│   ├── SKILL.md           # 문서화 보완
│   └── references/
│       └── scenarios.md
├── workflow/
│   ├── SKILL.md           # PDARR 오케스트레이터
│   └── references/
│       ├── team-agent-guide.md
│       └── pdarr-agent-prompt.md
└── profile/SKILL.md       # 성능 프로파일링
```

---

## 충돌 방지

- 설치 스크립트는 **동일 이름의 기존 스킬을 덮어쓰지 않습니다**
- 기존 스킬이 있으면 `SKIP`으로 표시하고 건너뜁니다
- 강제 덮어쓰기: `--force` 옵션 사용
- 특정 스킬만 설치: `--skills dispatch,run` 옵션 사용

```bash
# 기존에 /run 스킬이 있는 프로젝트
$ bash scripts/install-skills.sh /my-project
  OK    dispatch
  OK    analyze
  SKIP  run (already exists, use --force to overwrite)
  OK    check-code
  ...
```

---

## 문서 구조 (스킬이 사용하는)

스킬들은 다음 디렉토리 구조를 전제합니다. 설치 후 프로젝트에 생성하세요:

```
your-project/
├── docs/
│   ├── prd/           # PRD 문서 (/prd가 생성)
│   ├── spec/          # 기술 명세 (/spec이 생성)
│   ├── todo/          # 할 일 목록
│   ├── history/       # 세션 히스토리
│   └── complete/      # 완료 정리 (/complete가 생성)
│       └── summary.md
└── .claude/
    └── skills/        # ← 스킬 설치 위치
```

`templates/project-structure/`를 복사하면 한 번에 생성됩니다:
```bash
cp -r templates/project-structure/* /your-project/
```

---

## 관련 문서

- [Workflow Commands Guide](./../.claude/workflow-commands-guide.md) — 커맨드 전체 구축 가이드
- [Quick Start](../QUICKSTART.md) — 실전 활용 패턴
- [Preset System](../docs/14-preset-system.md) — 프리셋 상세
- [Agent Personas](../docs/05-agent-personas.md) — 16개 에이전트
