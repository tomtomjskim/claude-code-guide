# Bootstrap — claude-code-guide 부트스트랩 레퍼런스

**저장소**: https://github.com/tomtomjskim/claude-code-guide

> **Fork 사용 시 (P2-L2)**: 아래 모든 raw URL은 이 저장소(`tomtomjskim/claude-code-guide`)의 main 브랜치 기준. 자체 fork에 있다면 sed 일괄 치환:
> ```bash
> sed -i.bak 's|tomtomjskim/claude-code-guide|<your-org>/<your-fork>|g' BOOTSTRAP.md
> ```

Claude Code 세션 또는 터미널에서 **복사-붙여넣기**로 바로 사용할 수 있는 명령/프롬프트 모음.

---

## 🚀 최소 1줄 (터미널 기준)

```bash
curl -fsSL https://raw.githubusercontent.com/tomtomjskim/claude-code-guide/main/scripts/quick-setup.sh | bash
```

자동 프로파일 감지 + 설치. 다른 동작 필요 시 아래 옵션 참고.

---

## 📋 Claude Code 프롬프트 템플릿

### T1. Zero-context 설치 (저장소 URL 명시, 가장 안전)

```
다음 GitHub 저장소의 자동 셋업 스크립트로 이 프로젝트를 셋업해줘:
https://github.com/tomtomjskim/claude-code-guide

실행 명령:
curl -fsSL https://raw.githubusercontent.com/tomtomjskim/claude-code-guide/main/scripts/quick-setup.sh | bash

SETUP.md wizard 따라서 프로젝트 분석 → profile 추천 → 확인 후 실행.
```

### T2. 프로파일 강제 지정

```
claude-code-guide을 'team' 프로파일로 설치해줘.

실행: curl -fsSL https://raw.githubusercontent.com/tomtomjskim/claude-code-guide/main/scripts/quick-setup.sh | bash -s -- --profile team

설치 후 /dispatch 테스트.
```

지원 profile: `solo` / `team` / `enterprise` / `review-only` / `auto`(기본)

### T3. Dry-run 먼저 확인

```
claude-code-guide 설치 명령 미리 확인하고 싶어. 아래 명령으로 dry-run 실행:
curl -fsSL https://raw.githubusercontent.com/tomtomjskim/claude-code-guide/main/scripts/quick-setup.sh | bash -s -- --dry-run

결과 확인 후 실제 설치 여부 물어봐줘.
```

### T4. 특정 경로 지정

```
/path/to/my-project에 claude-code-guide를 설치해줘.

curl -fsSL https://raw.githubusercontent.com/tomtomjskim/claude-code-guide/main/scripts/quick-setup.sh | bash -s -- --target /path/to/my-project
```

### T5. 이미 설치되어 있는 경우 덮어쓰기

```
claude-code-guide 기존 설치를 최신 버전으로 덮어쓰기 해줘:
curl -fsSL https://raw.githubusercontent.com/tomtomjskim/claude-code-guide/main/scripts/quick-setup.sh | bash -s -- --force
```

### T6. 리뷰만 도입

```
이 프로젝트에 리뷰 도입만 하고 싶어. claude-code-guide의 review-only 프로파일로 설치:

curl -fsSL https://raw.githubusercontent.com/tomtomjskim/claude-code-guide/main/scripts/quick-setup.sh | bash -s -- --profile review-only

check-code, check-spec, qa-test 3 스킬만 추가됨.
```

---

## 🔖 Claude Code 전역 메모리 북마크 (권장 설정)

**최초 1회**, Claude Code 세션에서 아래 문장을 붙여넣기:

```
~/.claude/CLAUDE.md 파일의 끝에 다음 블록을 추가해줘:

---

## claude-code-guide (PDARR 워크플로우 + Safety Hooks + 팀 시스템)

- 저장소: https://github.com/tomtomjskim/claude-code-guide
- 설치 원라이너: curl -fsSL https://raw.githubusercontent.com/tomtomjskim/claude-code-guide/main/scripts/quick-setup.sh | bash
- SETUP wizard: https://raw.githubusercontent.com/tomtomjskim/claude-code-guide/main/SETUP.md
- 자연어 트리거: "claude-code-guide 설치", "PDARR 워크플로우 적용", "/setup-wizard"
- 전역 설치 명령: git clone --depth 1 https://github.com/tomtomjskim/claude-code-guide /tmp/ccg && bash /tmp/ccg/scripts/install-skills.sh --skills setup-wizard ~/
- 릴리즈: v4.0 (docs/v4-changelog.md 참조)
```

이후 어느 세션에서든 "claude-code-guide 설치해줘" 한 문장으로 전체 흐름 자동 진행.

---

## 🛠 로컬 Clone 사용 (네트워크 제한 등)

```bash
# 1. Clone
git clone https://github.com/tomtomjskim/claude-code-guide
cd claude-code-guide

# 2. 설치 (대상 프로젝트로)
bash scripts/quick-setup.sh --target /path/to/my-project

# 또는 수동 단계별
bash scripts/install-skills.sh /path/to/my-project
bash scripts/install-hooks.sh /path/to/my-project
```

---

## 📦 Profile 요약

| Profile | 스킬 수 | Hooks | 팀 시스템 | 대상 |
|---------|--------|-------|----------|------|
| `solo` | 5 | minimal (2) | ✗ | 1인 개발, 학습·사이드 |
| `team` | 19 | standard (4) | ✗ | 2-5인 팀, 기본 권장 |
| `enterprise` | 19 | standard (4) | ✓ `~/.claude/team/` | 대형, validate 필수 |
| `review-only` | 3 | minimal (2) | ✗ | 기존 프로젝트 리뷰 도입 |
| `auto` | - | - | - | 자동 감지(기여자+소스 파일 기준) |

Auto 감지 매트릭스:
- 기여자 1 & 소스 <50 → **solo**
- 기여자 2-5 & 소스 50-500 → **team**
- 기여자 5+ 또는 소스 500+ → **enterprise**

---

## 📚 관련 문서

- [`README.md`](README.md) — repo 개요 + Quick Install
- [`SETUP.md`](SETUP.md) — wizard 상세 (Claude Code machine-readable)
- [`QUICKSTART.md`](QUICKSTART.md) — 설치 후 실전 활용 패턴
- [`docs/v4-changelog.md`](docs/v4-changelog.md) — v4.0 릴리즈 노트
- [`skills/README.md`](skills/README.md) — 19 스킬 인덱스
- [`hooks/README.md`](hooks/README.md) — Hook 보일러플레이트 가이드
- [`CLAUDE.md`](CLAUDE.md) — 이 레포의 Claude Code 규칙 (예시)

---

## 🐛 문제 해결

### Claude Code가 저장소 URL을 모른다고 할 때
→ 이 `BOOTSTRAP.md`의 내용을 복사해서 Claude Code에 붙여넣기. 또는 위 "전역 메모리 북마크" 섹션대로 `~/.claude/CLAUDE.md`에 등록.

### curl 실패 (네트워크 제한)
→ 위 "로컬 Clone 사용" 섹션 참고.

### 설치 후 /dispatch가 인식 안 됨
→ Claude Code 재시작. `.claude/skills/` 경로 확인. `ls .claude/skills/` 로 스킬 19개 존재 확인.

### Hooks 미작동
→ `.claude/settings.local.json`에 hooks 블록 확인 + Claude Code 세션 재시작 (hooks는 세션 시작 시 로드).

### validate-system.sh Errors 6
→ 정상. PyYAML env baseline (설치와 무관).
