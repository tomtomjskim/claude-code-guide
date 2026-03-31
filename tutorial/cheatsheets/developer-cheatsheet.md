# 개발자 치트시트

> PDARR 워크플로우 + 프리셋 빠른 참조

---

## PDARR 사이클

```
Plan → Document → Act → Review → Reflect
 /prd    /spec    /run  /check-code  /reflect
  /analyze                /check-spec  /complete
```

## 커맨드 전체 맵

| 단계 | 커맨드 | 용도 |
|------|--------|------|
| 시작 | `/dispatch {작업}` | 복잡도 판단 → 경로 추천 |
| 계획 | `/prd {기능}` | 요구사항 문서 + 1차 판단 |
| 분석 | `/analyze {기능}` | 코드 분석 + 2차 판단 |
| 설계 | `/spec` | 기술 명세서 |
| 구현 | `/run` | 구현 실행 |
| 설계검수 | `/check-spec {모듈}` | 설계 ↔ 코드 일관성 |
| 코드검수 | `/check-code {모듈}` | 코드 품질 검사 |
| 완료 | `/complete` | 문서 통합 정리 |

## 프리셋 선택

```
깊이:  --quick ← standard → --thorough
실행:  단일    ← 기본    → --team
```

| 상황 | 프리셋 |
|------|--------|
| 작업 중 빠른 체크 | `--quick` |
| 일반 개발 후 | standard (기본) |
| PR / 머지 전 | `--thorough` |
| 배포 전 / 대규모 변경 | `--team` |

## 작업 유형별 패턴

```bash
# 간단한 수정 (Simple)
/run → /check-code → 커밋

# 일반 기능 (Medium)
/analyze → /spec → /run → /check-code → 커밋

# 대규모 기능 (Complex)
/prd → /analyze --team → /spec --team → /workflow → /check-code --team

# 배포 전 감사
/check-code --team {모듈}
```

## CLAUDE.md 필수 섹션

```markdown
# 프로젝트 개요    — 뭐 하는 프로젝트인지
## 기술 스택       — 언어, 프레임워크, 도구
## 코딩 컨벤션     — 네이밍, 구조 규칙
## 금지 사항       — 하면 안 되는 것
## 파일 구조       — 디렉토리 설명
```

## 안티패턴

| X 하지 마세요 | O 대신 이렇게 |
|-------------|-------------|
| 모든 작업에 `--team` | 6개 파일 이하면 standard |
| 매번 `--thorough` | 배포 전에만 사용 |
| `/analyze` 없이 바로 `/run` (큰 기능) | 분석 먼저, 구현은 나중 |
| CLAUDE.md 없이 시작 | 프로젝트 설정 먼저 |
