# ECC 선별 도입 및 설치 수명주기

## 평가 기준

- Upstream: `affaan-m/ECC`
- 평가 commit: `4e973d3eaf92d97f8d2e2d8abb39d8bdc8711b38`
- License: MIT
- 도입 방식: runtime dependency나 파일 벤더링이 아닌 동작 계약 재구현

ECC의 대규모 agent/skill/command catalog는 기존 PDARR 체계와 중복되므로 가져오지
않는다. 다음 메커니즘만 현재 구조에 맞게 적용한다.

- 검토된 ref 기반 원격 설치
- dry-run과 실제 source ref 일치
- install-state, doctor, repair, uninstall
- 관리 파일만 복구하는 ownership boundary
- symlink, 경로 탈출, unknown schema fail-closed
- portable surface의 skill contract, 숨은 Unicode, 개인 절대 경로 검증

## 설치 경계

로컬 clone에서 `quick-setup.sh`를 실행하면 해당 checkout을 source로 사용한다.
원격 bootstrap dry-run은 이름 ref도 미리볼 수 있지만 실제 apply는 검토된
full 40-character commit SHA만 허용한다. checkout 후 `HEAD`가 요청 SHA와 정확히
일치하는지도 확인하며 branch, tag, short SHA, `main`은 네트워크 apply 전에 중단한다.

설치 완료 시 target에 아래 상태 파일이 생긴다.

```text
.claude/claude-code-guide-install-state.json
```

파일에는 schema version, guide version, profile, target identity, resolved source
revision, 관리 파일의 상대 경로·hash·mode·uid·gid를 기록한다. 변경 전·설치 후
파일 본문은 target이나 Git에 두지 않고
`CLAUDE_CODE_GUIDE_STATE_HOME` 또는 XDG user state 아래의 권한 제한 디렉터리에 둔다.
`repair`와 `uninstall`은 해당 payload의 hash와 mode를 변경 전에 검증한다.
상태 generation은 예측 불가능한 ID의 임시 디렉터리에서 완성·검증한 뒤 원자적으로
publish하며, 새 state JSON이 확정된 뒤 이전 generation을 정리한다.
Git target에서는 상태 파일이 이미 tracked 상태면 finalize를 거부하고, untracked라면
repository root 기준 경로를 `.git/info/exclude`에 로컬 ignore로 추가해 다른
checkout으로 전파되지 않게 한다.

enterprise profile은 project `.claude/`와 함께 해당 설치가 변경한 Claude home의
`team/`, `agents/` 파일만 추적한다. 기존 설정, 사용자 skill, 다른 파일은 관리
대상에 포함하지 않는다. `CLAUDE_CONFIG_DIR`를 지정하면 설치, 검증, 상태 추적이
모두 같은 경로를 사용한다.

enterprise validation 전에 install-state를 확정한다. validation이 실패하면
명령은 실패 상태로 끝나지만, 생성된 상태를 이용해 `doctor`로 확인하거나
`uninstall`로 설치 전 상태를 복원할 수 있다.

begin snapshot과 WAL은 임시 `/tmp`가 아니라 XDG user state의
`transactions/<target-id>/<transaction-id>/`에 둔다. skill, hook,
`settings.local.json`의 모든 managed file은 destination을 바꾸기 전에 durable
before-image와 after metadata를 기록한다. transaction journal은 sibling staging
directory에서 완성한 뒤 registry에 원자 publish하고, 새 directory 계층의 각
component와 parent entry를 순서대로 `fsync`한다.
target별 stable `flock`은 병렬 설치를 막고 프로세스 사망 시 커널이 자동 해제한다.

`HUP`/`INT`/`TERM`은 즉시 rollback하고, trap을 실행할 수 없는 `SIGKILL`·process
crash·reboot는 다음 `quick-setup` 또는 명시적 `recover`에서 복구한다. durable
commit 전 transaction은 before-image로 rollback하고, commit-ready 이후 transaction은
새 state를 roll-forward한다. `repair`와 `uninstall`의 capture도 commit 전에는
삭제하지 않는다. destination이 기록된 before/after 어느 쪽과도 일치하지 않으면
동시 사용자 편집으로 간주해 보존하고 fail-closed한다.

지원 범위는 `fcntl`, `flock`, same-filesystem rename/link와 file·directory `fsync`를
제공하는 local POSIX filesystem이다. 네트워크 filesystem, Windows native,
저장장치/파일시스템 자체 손상은 이 보장의 범위 밖이다.

## 운영 명령

```bash
bash scripts/manage-install.sh doctor --target <project> --json
bash scripts/manage-install.sh recover --target <project> --json
bash scripts/manage-install.sh repair --target <project> --dry-run --json
bash scripts/manage-install.sh repair --target <project>
bash scripts/manage-install.sh uninstall --target <project> --dry-run --json
bash scripts/manage-install.sh uninstall --target <project>
```

- `doctor`: 관리 파일의 누락, 내용·mode·ownership drift를 읽기 전용으로 검사한다.
- `recover`: 미완료 WAL을 commit 경계에 따라 rollback 또는 roll-forward한다.
- `repair`: 처음 관찰한 drift 파일을 원자 격리해 같은 내용인지 다시 확인한 뒤에만
  설치 완료 snapshot으로 복구한다.
- `uninstall`: drift가 없을 때 설치 전 파일을 복원하고 설치가 만든 파일만 제거한다.
- drift 상태에서 uninstall은 사용자 변경 손실을 막기 위해 중단한다.
- uninstall은 현재 파일을 같은 디렉터리의 quarantine으로 원자 이동한 뒤 hash,
  mode, ownership을 다시 확인하고, 불일치 시 원위치로 복구한다.
- 다른 target으로 복사된 state, 다른 Claude home으로 실행한 state, 더 새 schema는
  자동 추측하지 않는다.
- 변조된 `state_id`와 관리 경로의 symlink·경로 탈출은 fail closed한다.
- 같은 target을 다른 Claude home으로 재설치하려면 먼저 기존 home 기준으로
  uninstall해야 한다.
- 기존 install-state와 source revision이 달라지면 검토 후 `--force`를 명시해야
  하며, source revision과 profile을 동시에 바꾸려면 먼저 uninstall한다.

여기서 `doctor`와 `--dry-run`의 읽기 전용 범위는 managed target 파일과 install-state다.
동시 lifecycle 작업을 배제하기 위한 XDG state home의 target별 lock directory/file은
생성되거나 mode가 보정될 수 있다.

## Hook runtime state

Agent counter, 감사 로그, Level 3 로그는 사용자 전용 `0700` runtime 디렉터리를
공유하되 counter는 hash된 session ID별 `0600` 파일로 분리한다. 누락된 session ID는
counter를 만들지 않으며, 7일 TTL과 `flock`을 사용한다. 테스트는 별도
`CLAUDE_HOOK_STATE_DIR`을 사용해 실제 세션 상태를 수정하지 않는다.

legacy `/tmp/claude-hooks/agent-count-unknown`은 자동 초기화하거나 삭제하지 않는다.
그 작업은 아직 구버전 Hook을 실행 중인 다른 세션의 호출 제한을 되돌릴 수 있다.
모든 Hook을 v4.5.1로 갱신하고 구버전 세션이 종료된 뒤에만 별도 정리한다.

pre-v4.5.1 중단 설치는 새 WAL 복구 대상이 아니다. v4.5의 before-image는 임의
`/tmp` 디렉터리에 있었고 project-local directory lock을 사용했다. legacy lock의
PID가 실제 설치 프로세스인지 확인하고 target과 남은 snapshot을 수동 검토하기
전에는 `<project>/.claude/.claude-code-guide-install.lock`을 삭제하거나 `--force`
재설치를 실행하지 않는다.

## 검증

```bash
python3 -m unittest discover -s scripts/tests -p 'test_*.py' -v
bash hooks/tests/run-tests.sh
bash scripts/validate-repository.sh
bash scripts/validate-system.sh \
  --project <project> \
  --claude-home <claude-home>
```

`validate-system.sh`를 인자 없이 실행하면 기존 global 설치 위치를 검사한다.
project-local skill과 settings를 검증할 때는 두 경로를 명시한다.

## 채택하지 않은 ECC 기본값

- proactive agent delegation과 항상 병렬 실행
- 모든 프로젝트에 동일한 80% coverage 강제
- ECC plugin/sync와 이 가이드의 중복 설치
- ECC memory runtime, 자동 학습, dashboard
- 전체 skill, agent, command catalog 복제

현재 기본값은 계속 단일 실행, 리스크 기반 상향, 기존 PDARR workflow다.
