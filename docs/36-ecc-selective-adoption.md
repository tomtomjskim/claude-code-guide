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
원격 bootstrap은 `--ref <tag-or-commit>`으로 내려받을 source를 고정한다.
`main`을 사용할 수는 있지만 moving target 경고를 출력한다.

설치 완료 시 target에 아래 상태 파일이 생긴다.

```text
.claude/claude-code-guide-install-state.json
```

파일에는 schema version, guide version, profile, 관리 파일의 상대 경로와 hash만
기록한다. 변경 전·설치 후 파일 본문은 target이나 Git에 두지 않고
`CLAUDE_CODE_GUIDE_STATE_HOME` 또는 XDG user state 아래의 권한 제한 디렉터리에 둔다.
`repair`와 `uninstall`은 해당 payload의 hash와 mode를 변경 전에 검증한다.

enterprise profile은 project `.claude/`와 함께 해당 설치가 변경한 Claude home의
`team/`, `agents/` 파일만 추적한다. 기존 설정, 사용자 skill, 다른 파일은 관리
대상에 포함하지 않는다. `CLAUDE_CONFIG_DIR`를 지정하면 설치, 검증, 상태 추적이
모두 같은 경로를 사용한다.

enterprise validation 전에 install-state를 확정한다. validation이 실패하면
명령은 실패 상태로 끝나지만, 생성된 상태를 이용해 `doctor`로 확인하거나
`uninstall`로 설치 전 상태를 복원할 수 있다.

skill/hook 설치 단계가 finalize 전에 실패하면 begin snapshot으로 부분 변경을
자동 rollback한다. 자동 rollback까지 실패하면 원본 snapshot이 든 권한 제한
임시 디렉터리를 삭제하지 않고 경로를 출력한다.

## 운영 명령

```bash
bash scripts/manage-install.sh doctor --target <project> --json
bash scripts/manage-install.sh repair --target <project> --dry-run --json
bash scripts/manage-install.sh repair --target <project>
bash scripts/manage-install.sh uninstall --target <project> --dry-run --json
bash scripts/manage-install.sh uninstall --target <project>
```

- `doctor`: 관리 파일의 누락, 내용·mode drift를 읽기 전용으로 검사한다.
- `repair`: drift가 있는 관리 파일만 설치 완료 snapshot으로 복구한다.
- `uninstall`: drift가 없을 때 설치 전 파일을 복원하고 설치가 만든 파일만 제거한다.
- drift 상태에서 uninstall은 사용자 변경 손실을 막기 위해 중단한다.
- 다른 Claude home으로 실행하거나 state schema가 더 새로우면 자동 추측하지 않는다.
- 변조된 `state_id`와 관리 경로의 symlink·경로 탈출은 fail closed한다.
- 같은 target을 다른 Claude home으로 재설치하려면 먼저 기존 home 기준으로
  uninstall해야 한다.

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
