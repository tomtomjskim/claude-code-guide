# 추천 플러그인 가이드

Claude Code의 플러그인 시스템을 활용하여 개발 워크플로우를 강화할 수 있습니다.

---

## 플러그인 관리 기본 명령어

```bash
# 마켓플레이스 등록
claude plugin marketplace add <owner/repo>

# 마켓플레이스 목록
claude plugin marketplace list

# 플러그인 설치
claude plugin install <plugin>@<marketplace>

# 설치된 플러그인 목록
claude plugin list

# 플러그인 업데이트
claude plugin update <plugin>

# 플러그인 비활성화/활성화
claude plugin disable <plugin>
claude plugin enable <plugin>

# 플러그인 삭제
claude plugin uninstall <plugin>
```

---

## 필수 플러그인

### Superpowers (v4.2.0+)

> 체계적 소프트웨어 개발 워크플로우를 Claude에게 부여하는 스킬 프레임워크

| 항목 | 내용 |
|------|------|
| **개발자** | Jesse Vincent (obra) |
| **GitHub** | [obra/superpowers](https://github.com/obra/superpowers) |
| **마켓플레이스** | [obra/superpowers-marketplace](https://github.com/obra/superpowers-marketplace) |
| **라이선스** | MIT (무료) |
| **Stars** | 42,000+ |

#### 설치

```bash
# 1. 마켓플레이스 등록
claude plugin marketplace add obra/superpowers-marketplace

# 2. 플러그인 설치
claude plugin install superpowers@superpowers-marketplace

# 3. 설치 확인
claude plugin list
```

#### 핵심 스킬 (14개 라우터 테이블)

| 카테고리 | 스킬 | 발동 시점 |
|----------|------|----------|
| **프로세스** | brainstorming | 새 기능/컴포넌트 설계 시 |
| | writing-plans | 스펙/요구사항 → 구현 계획 작성 |
| | executing-plans | 별도 세션에서 계획 배치 실행 |
| **구현** | test-driven-development | 코드 구현 전 (RED-GREEN-REFACTOR) |
| | systematic-debugging | 버그/에러/실패 시 (4단계 근본 원인) |
| | subagent-driven-development | 같은 세션에서 계획 실행 (2단계 리뷰) |
| | dispatching-parallel-agents | 2+ 독립 문제 병렬 처리 |
| **검증** | verification-before-completion | 완료 주장 전 증거 확인 |
| | requesting-code-review | 태스크/기능 완료 후 리뷰 요청 |
| | receiving-code-review | 리뷰 피드백 수신 시 평가 |
| **인프라** | using-git-worktrees | 격리 워크스페이스 필요 시 |
| | finishing-a-development-branch | 브랜치 완료 → 머지/PR/정리 |
| **메타** | using-superpowers | 스킬 라우팅 (어떤 스킬 쓸지) |
| | writing-skills | 스킬 작성/수정/검증 |

#### 토큰 최적화 (2026-03-10)

| 항목 | 원본 | 최적화 후 | 절감 |
|------|------|-----------|------|
| 전체 SKILL.md (14개) | 13,496 words | 8,326 words | -38.3% |
| Hook 세션 주입 | 581 words | 70 words | -88.0% |

> 플러그인 업데이트 시 최적화가 초기화될 수 있음. 재적용 스크립트: `/home/ubuntu/superpowers-benchmark/reapply-optimizations.sh`

#### 슬래시 커맨드

```bash
/superpowers:brainstorm      # 브레인스토밍 시작
/superpowers:write-plan      # 구현 계획 작성
/superpowers:execute-plan    # 계획 실행 (서브에이전트)
```

#### 워크플로우 예시

```
1. /superpowers:brainstorm
   → 요구사항 질문/정제 → 설계 문서 생성

2. /superpowers:write-plan
   → 2-5분 단위 태스크 분해 → 파일 경로, 코드, 검증 단계 포함

3. /superpowers:execute-plan
   → 서브에이전트가 태스크별 실행
   → 1차 리뷰: 스펙 준수 확인
   → 2차 리뷰: 코드 품질 확인
   → 실패 시 자동 재시도
```

#### Claude Code 네이티브 멀티 에이전트와의 통합

Claude Code는 이제 멀티 에이전트 오케스트레이션을 네이티브로 지원합니다. Superpowers는 이 네이티브 도구들과 함께 구조화된 워크플로우를 제공합니다:

| 기능 | Claude Code 네이티브 | Superpowers | 권장 사용 |
|------|---------------------|-------------|----------|
| 에이전트 오케스트레이션 | Task, Agent, TeamCreate, SendMessage | subagent-driven-development, dispatching-parallel-agents | **네이티브 도구** (Superpowers 스킬로 강화) |
| 워크플로우 관리 | 커스텀 커맨드 | 자동 스킬 발동 | 병행 사용 |
| TDD | 미적용 | RED-GREEN-REFACTOR 강제 | **Superpowers** |
| 체계적 디버깅 | 미적용 | 4단계 디버깅 | **Superpowers** |
| 브레인스토밍 | PM 에이전트 | 소크라테스식 정제 | **Superpowers** |
| 코드 리뷰 | QA 에이전트 | 2단계 자동 리뷰 | 병행 사용 |

**권장 하이브리드 전략:**
- 새 기능 개발 → Superpowers 워크플로우 (brainstorm → plan → execute)
- 긴급 버그 수정 → 기존 quick-fix 워크플로우
- 병렬 독립 작업 → `dispatching-parallel-agents` 스킬 + Claude Code `Task()`
- 대규모 리팩토링 → 기존 refactor 워크플로우 + Superpowers TDD
- 코드 품질 → Superpowers TDD + systematic-debugging

---

## 필수 플러그인: Skill Creator (Anthropic 공식)

> 스킬 생성, 테스트, 개선, 벤치마크를 위한 Anthropic 공식 플러그인

| 항목 | 내용 |
|------|------|
| **개발자** | Anthropic (공식) |
| **마켓플레이스** | claude-plugins-official (내장) |
| **라이선스** | MIT |

#### 설치

```bash
# 마켓플레이스 등록 (이미 내장되어 있을 수 있음)
claude plugin marketplace add anthropics/claude-plugins-official

# 플러그인 설치
claude plugin install skill-creator@claude-plugins-official
```

#### 슬래시 커맨드

```bash
/skill-creator    # Skill Creator 실행
```

#### 4가지 모드

| 모드 | 용도 | 사용 시점 |
|------|------|----------|
| **Create** | 대화형 Q&A로 새 스킬 생성 | "PR 보안 리뷰 스킬 만들어줘" |
| **Eval** | 테스트 케이스로 스킬 검증 | "내 code-review 스킬 eval 돌려줘" |
| **Improve** | 평가 결과 기반 스킬 최적화 | 피드백 반영 후 반복 개선 |
| **Benchmark** | 여러 번 실행해 성능/분산 비교 | "10회 벤치마크하고 분산 보여줘" |

#### 내부 에이전트

| 에이전트 | 역할 |
|---------|------|
| Executor | 스킬을 적용하여 테스트 프롬프트 실행 |
| Grader | assertion 기반 정량 평가 |
| Comparator | 블라인드 A/B 비교 |
| Analyzer | 벤치마크 패턴 분석 |

#### 워크플로우

```
1. Create: 의도 파악 → 인터뷰 → SKILL.md 작성
2. Eval: 테스트 프롬프트 작성 → with-skill / baseline 병렬 실행
3. Review: eval-viewer로 결과 비교 → 사용자 피드백
4. Improve: 피드백 반영 → 스킬 수정 → 재실행
5. Benchmark: 반복 실행으로 안정성/성능 검증
6. Description Optimization: 트리거 정확도 최적화 (선택)
```

#### Superpowers와의 관계

- Superpowers 스킬을 분석/개선할 때 Skill Creator 사용
- 커스텀 스킬 작성 시 Superpowers의 `writing-skills` 스킬과 병행
- 예: Superpowers 14개 스킬 벤치마크 → 토큰 38.3% 절감 달성 (2026-03-10)

---

## 추천 마켓플레이스 스킬 (6개)

커뮤니티 마켓플레이스에서 설치할 수 있는 검증된 스킬입니다.

### UI/UX Pro Max

> 50 스타일, 21 팔레트, 50 폰트 페어링, 20 차트, 9 스택 지원 UI/UX 디자인 인텔리전스

| 항목 | 내용 |
|------|------|
| **발동** | UI/UX 코드 작성, 리뷰, 디자인 시스템 관련 요청 시 |
| **스택** | React, Next.js, Vue, Svelte, SwiftUI, React Native, Flutter, Tailwind, shadcn/ui |
| **스타일** | glassmorphism, minimalism, brutalism, neumorphism, bento grid 등 50종 |
| **연동** | shadcn/ui MCP 서버 컴포넌트 검색 |

### Frontend Design

> 생산 수준의 프론트엔드 인터페이스를 높은 디자인 품질로 생성

| 항목 | 내용 |
|------|------|
| **발동** | 웹 컴포넌트, 페이지, 대시보드, 랜딩 페이지 빌드 요청 시 |
| **특징** | AI 미학 회피 (제네릭 패턴 거부), 창의적 + 정교한 코드 생성 |

### Web Design Guidelines

> Vercel의 Web Interface Guidelines 기반 UI 코드 리뷰

| 항목 | 내용 |
|------|------|
| **발동** | "review my UI", "check accessibility", "audit design" 요청 시 |
| **원본** | [Vercel Web Interface Guidelines](https://vercel.com/blog/web-interface-guidelines) |

### SEO Audit

> SEOmator CLI 기반 251개 규칙, 20개 카테고리 웹사이트 감사

| 항목 | 내용 |
|------|------|
| **발동** | 웹사이트 분석, SEO 디버깅, 사이트 헬스 체크 요청 시 |
| **요구사항** | Node.js 18+, Chrome/Chromium (선택, Core Web Vitals용) |
| **출력** | LLM 최적화 리포트, 헬스 스코어 |

### Webapp Testing

> Playwright 기반 로컬 웹 앱 상호작용 및 테스트

| 항목 | 내용 |
|------|------|
| **발동** | 프론트엔드 기능 검증, UI 디버깅, 브라우저 스크린샷, 로그 확인 시 |
| **특징** | 브라우저 직접 제어, 스크린샷 캡처, 콘솔 로그 수집 |

### Supabase Postgres Best Practices

> Supabase의 Postgres 성능 최적화 및 모범 사례

| 항목 | 내용 |
|------|------|
| **발동** | Postgres 쿼리 작성/리뷰/최적화, 스키마 설계, DB 설정 시 |
| **범위** | 인덱스 전략, 쿼리 플래닝, RLS, 파티셔닝, 커넥션 풀링 |

### 설치 (전체)

```bash
# 마켓플레이스별 스킬 설치
claude skill install ui-ux-pro-max
claude skill install frontend-design
claude skill install web-design-guidelines
claude skill install seo-audit
claude skill install webapp-testing
claude skill install supabase-postgres-best-practices
```

---

## 추천 플러그인 (추가 검토)

### Context7

> AI 에이전트가 최신 문서를 검색하고 참조할 수 있게 하는 문서 제공 플러그인

- **용도**: 최신 API 문서 참조, 라이브러리 문서 검색
- **GitHub**: [upstash/context7](https://github.com/upstash/context7)
- **설치**: 마켓플레이스에서 설치 가능

### Superpowers Lab

> Superpowers의 실험적 스킬 확장

- **용도**: 새로운 기법 및 도구 테스트
- **GitHub**: [obra/superpowers-lab](https://github.com/obra/superpowers-lab)
- **상태**: 실험적 (안정성 미보장)

### Superpowers Chrome

> Chrome DevTools Protocol을 통한 브라우저 직접 제어

- **용도**: 웹 테스트 자동화, UI 검증
- **GitHub**: [obra/superpowers-chrome](https://github.com/obra/superpowers-chrome)

---

## settings.json 플러그인 설정

```json
{
  "enabledPlugins": {
    "superpowers@superpowers-marketplace": true,
    "skill-creator@claude-plugins-official": true
  }
}
```

플러그인은 `~/.claude/settings.json`의 `enabledPlugins` 섹션에서 활성화/비활성화할 수 있습니다.

---

## 다음 단계

- [셋업 체크리스트](00-setup-checklist.md)
- [MCP 설정](01-mcp-configuration.md)
- [개발 파이프라인](03-development-pipeline.md)
