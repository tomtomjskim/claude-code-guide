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

#### 핵심 스킬

| 스킬 | 설명 | 자동 발동 시점 |
|------|------|--------------|
| **brainstorming** | 소크라테스식 요구사항 정제 | 새 기능 작업 시작 시 |
| **writing-plans** | 세부 구현 계획 작성 | 설계 승인 후 |
| **executing-plans** | 배치 실행 + 체크포인트 | 계획 실행 시 |
| **subagent-driven-development** | 서브에이전트 병렬 개발 + 2단계 리뷰 | 계획 실행 시 |
| **test-driven-development** | RED-GREEN-REFACTOR 사이클 강제 | 코드 구현 시 |
| **systematic-debugging** | 4단계 근본 원인 분석 | 버그 수정 시 |
| **requesting-code-review** | 코드 리뷰 체크리스트 | 태스크 간 전환 시 |
| **using-git-worktrees** | 격리된 워크스페이스 생성 | 설계 승인 후 |
| **finishing-a-development-branch** | 머지/PR 결정 워크플로우 | 모든 태스크 완료 시 |
| **verification-before-completion** | 실제로 수정됐는지 검증 | 디버깅 완료 시 |
| **writing-skills** | 새 스킬 작성 가이드 | 스킬 확장 시 |

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

#### 기존 멀티 에이전트 시스템과의 통합

Superpowers는 기존 팀 오케스트레이션 시스템과 공존 가능합니다:

| 기능 | 기존 시스템 | Superpowers | 권장 사용 |
|------|-----------|-------------|----------|
| 에이전트 오케스트레이션 | Team Orchestrator MCP | subagent-driven-development | 상황에 따라 선택 |
| 워크플로우 관리 | workflows/*.yaml | 자동 스킬 발동 | 병행 사용 |
| TDD | 미적용 | RED-GREEN-REFACTOR 강제 | **Superpowers** |
| 체계적 디버깅 | 미적용 | 4단계 디버깅 | **Superpowers** |
| 브레인스토밍 | PM 에이전트 | 소크라테스식 정제 | **Superpowers** |
| 코드 리뷰 | QA 에이전트 | 2단계 자동 리뷰 | 병행 사용 |

**권장 하이브리드 전략:**
- 새 기능 개발 → Superpowers 워크플로우 (brainstorm → plan → execute)
- 긴급 버그 수정 → 기존 quick-fix 워크플로우
- 대규모 리팩토링 → 기존 refactor 워크플로우 + Superpowers TDD
- 코드 품질 → Superpowers TDD + systematic-debugging

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
    "superpowers@superpowers-marketplace": true
  }
}
```

플러그인은 `~/.claude/settings.json`의 `enabledPlugins` 섹션에서 활성화/비활성화할 수 있습니다.

---

## 다음 단계

- [셋업 체크리스트](00-setup-checklist.md)
- [MCP 설정](01-mcp-configuration.md)
- [개발 파이프라인](03-development-pipeline.md)
