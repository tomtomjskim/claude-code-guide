# Session State And Crash Recovery Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Hook 상태를 세션·사용자별로 격리하고, 설치 lifecycle의 managed file 변경을 local POSIX filesystem에서 crash-recoverable하게 만든다.

**Architecture:** Hook은 private runtime directory와 hashed session key, `flock`, TTL을 사용한다. Quick setup은 persistent state home에 before snapshot과 WAL을 만들고, 모든 static/generated managed file을 `install_state.py publish`로 적용한다. WAL `PREPARE`와 파일/디렉터리 `fsync`가 완료된 뒤 namespace를 변경하고, durable `COMMIT` 전 crash는 rollback, 이후 crash는 roll-forward cleanup한다.

**Tech Stack:** Bash, Python standard library, POSIX same-directory rename/link, `fcntl.flock`, `fsync`, `unittest`.

---

### Task 1: Hook state isolation

**Files:**
- Modify: `hooks/boilerplates/guard-agent.sh`
- Modify: `hooks/boilerplates/audit-agent.sh`
- Modify: `hooks/boilerplates/safety-careful.sh`
- Modify: `hooks/tests/run-tests.sh`
- Modify: `hooks/README.md`

**Steps:**
1. missing/invalid session ID가 counter 파일을 만들지 않는 RED 테스트를 추가한다.
2. 별도 state root를 사용하는 두 session과 병렬 increment RED 테스트를 추가한다.
3. test runner가 production `/tmp/claude-hooks`를 변경하지 않는 RED 테스트를 추가한다.
4. private `CLAUDE_HOOK_STATE_DIR`, hashed key, `flock`, `0600`, TTL cleanup을 구현한다.
5. audit/notice/Level 3 log도 같은 private state root를 사용하게 한다.
6. hook suite를 두 번 연속 실행해 격리와 반복 가능성을 검증한다.

### Task 2: Durable lifecycle WAL

**Files:**
- Modify: `scripts/install_state.py`
- Modify: `scripts/install-skills.sh`
- Modify: `scripts/install-hooks.sh`
- Modify: `scripts/quick-setup.sh`
- Modify: `scripts/manage-install.sh`
- Modify: `scripts/tests/test_install_state.py`
- Modify: `scripts/tests/test_quick_setup_lifecycle.py`

**Steps:**
1. persistent transaction snapshot과 WAL schema에 대한 RED 테스트를 추가한다.
2. WAL prepare 직후, capture 직후, publish 직후, state publish 직후 실제 child `SIGKILL` RED 테스트를 추가한다.
3. file과 parent directory를 동기화하는 durable JSON/copy/link/replace/unlink helper를 구현한다.
4. target별 stable `flock`과 persistent transaction registry를 구현한다.
5. static skill/hook/generated settings를 모두 transaction-aware `publish`로 통과시킨다.
6. recovery를 rollback/roll-forward 양쪽에서 idempotent하게 구현한다.
7. destination이 before/after 어느 쪽과도 다르면 사용자 편집을 보존하고 fail-closed한다.
8. recover를 두 번 실행하고 stale journal/capture/lock이 남지 않는지 검증한다.

### Task 3: Release documentation

**Files:**
- Create: `docs/v4.8-changelog.md`
- Modify: `README.md`
- Modify: `docs/README.md`
- Modify: `docs/39-ecc-selective-adoption.md`
- Modify: `scripts/install_state.py`

**Steps:**
1. `GUIDE_VERSION`을 `4.8`로 갱신한다.
2. migration, supported filesystem, legacy `/tmp` counter 비자동 삭제 이유를 기록한다.
3. crash recovery와 hook state 격리 검증 명령을 기록한다.
4. repository validator와 전체 회귀 테스트를 실행한다.

### Task 4: Review and delivery

**Steps:**
1. 독립 reviewer에게 exact fault-injection과 side-effect 재현을 요청한다.
2. blocker/major를 수정하고 최대 3회 bounded adversarial loop를 적용한다.
3. feature commit을 local main에 fast-forward 병합한다.
4. main에서 전체 검증 후 `origin/main`에 push하고 원격 SHA를 대조한다.
