#!/usr/bin/env python3
"""Track, inspect, repair, and uninstall claude-code-guide managed files."""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import re
import secrets
import shutil
import signal
import stat
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


SCHEMA_VERSION = 1
GUIDE_VERSION = "4.8"
STATE_RELATIVE_PATH = Path(".claude/claude-code-guide-install-state.json")
STATE_KEYS = {
    "schema_version",
    "guide_version",
    "profile",
    "installed_at",
    "source_revision",
    "state_id",
    "target_id",
    "claude_home_id",
    "entries",
}
ENTRY_KEYS = {
    "scope",
    "path",
    "installed_exists",
    "installed_sha256",
    "installed_mode",
    "installed_uid",
    "installed_gid",
    "previous_exists",
    "previous_sha256",
    "previous_mode",
    "previous_uid",
    "previous_gid",
}
MANIFEST_ENTRY_KEYS = {"scope", "path", "expected_sha256", "expected_mode"}
AUTHORIZED_RELATIVE_PATH = Path("authorized.json")
SNAPSHOT_ENTRY_KEYS = {"scope", "path", "sha256", "mode", "uid", "gid"}
PATH_ID_PATTERN = re.compile(r"^[0-9a-f]{24}$")
STATE_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
TRANSACTION_STATUSES = frozenset(
    {"initializing", "prepared", "commit-ready", "committed", "aborted"}
)
RUNTIME_TRANSACTION_STATUSES = frozenset(
    {"initializing", "prepared", "commit-ready", "committed"}
)

PROFILE_SKILLS = {
    "solo": ("dispatch", "stage", "check-code", "reflect", "flow"),
    "review-only": ("check-code", "check-spec", "qa-test"),
}
PROFILE_HOOKS = {
    "solo": ("guard-agent", "safety-careful"),
    "review-only": ("guard-agent", "safety-careful"),
    "team": ("guard-agent", "safety-careful", "safety-freeze", "audit-agent"),
    "enterprise": (
        "guard-agent",
        "safety-careful",
        "safety-freeze",
        "audit-agent",
    ),
}
VALID_PROFILES = frozenset({"solo", "team", "enterprise", "review-only"})


class InstallStateError(RuntimeError):
    """Raised when install state cannot be handled safely."""


def fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    try:
        descriptor = os.open(path, flags)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except OSError as error:
        raise InstallStateError(f"directory fsync failed: {path}") from error


def fsync_file(path: Path) -> None:
    try:
        with path.open("rb") as handle:
            os.fsync(handle.fileno())
    except OSError as error:
        raise InstallStateError(f"file fsync failed: {path}") from error


def ensure_directory_durable(path: Path, mode: int = 0o700) -> Path:
    path = path.absolute()
    missing = []
    current = path
    while not current.exists():
        if current.is_symlink():
            raise InstallStateError(
                f"directory path must not contain a symlink: {current}"
            )
        missing.append(current)
        if current.parent == current:
            break
        current = current.parent
    if current.is_symlink() or not current.is_dir():
        raise InstallStateError(f"directory path is unsafe: {current}")
    for directory in reversed(missing):
        try:
            directory.mkdir(mode=mode)
        except FileExistsError:
            if directory.is_symlink() or not directory.is_dir():
                raise InstallStateError(
                    f"directory path became unsafe: {directory}"
                )
        os.chmod(directory, mode)
        fsync_directory(directory.parent)
        fsync_directory(directory)
    if path.is_symlink() or not path.is_dir():
        raise InstallStateError(f"directory path is unsafe: {path}")
    fsync_directory(path)
    if path.parent != path:
        fsync_directory(path.parent)
    return path


def prepare_internal_stage(path: Path) -> Path:
    ensure_directory_durable(path.parent)
    if path.is_symlink():
        raise InstallStateError(f"internal stage must not be a symlink: {path}")
    if path.exists():
        if not path.is_file():
            raise InstallStateError(f"internal stage is unsafe: {path}")
        remove_path_durably(path)
    return path


def fault_point(name: str) -> None:
    if os.environ.get("CLAUDE_CODE_GUIDE_FAULT_POINT") == name:
        os.kill(os.getpid(), signal.SIGKILL)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def path_identity(path: Path) -> str:
    return hashlib.sha256(str(path.resolve()).encode("utf-8")).hexdigest()[:24]


def managed_state_home() -> Path:
    xdg_state_home = Path(
        os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local/state"))
    )
    return Path(
        os.environ.get(
            "CLAUDE_CODE_GUIDE_STATE_HOME",
            str(xdg_state_home / "claude-code-guide"),
        )
    ).expanduser()


def file_metadata(path: Path) -> tuple[int, int, int]:
    metadata = path.stat(follow_symlinks=False)
    return (
        stat.S_IMODE(metadata.st_mode),
        metadata.st_uid,
        metadata.st_gid,
    )


def validate_target(target: Path) -> Path:
    if not target.exists() or not target.is_dir():
        raise InstallStateError(f"target directory not found: {target}")
    if target.is_symlink():
        raise InstallStateError(f"target directory must not be a symlink: {target}")
    return target.resolve()


def validate_source(source: Path) -> Path:
    if not source.exists() or not source.is_dir():
        raise InstallStateError(f"source directory not found: {source}")
    if source.is_symlink():
        raise InstallStateError(f"source directory must not be a symlink: {source}")
    return source.resolve()


def validate_relative_path(value: str) -> PurePosixPath:
    relative = PurePosixPath(value)
    if relative.is_absolute() or not relative.parts or any(
        part in {"", ".", ".."} for part in relative.parts
    ):
        raise InstallStateError(f"unsafe managed path: {value}")
    return relative


def validate_scoped_path(scope: str, value: str) -> PurePosixPath:
    relative = validate_relative_path(value)
    if scope == "project":
        if relative.as_posix() == STATE_RELATIVE_PATH.name:
            raise InstallStateError("install state file cannot be a managed entry")
        return relative
    if scope == "claude-home":
        if relative.parts[0] not in {"team", "agents"}:
            raise InstallStateError(
                f"Claude-home managed path is outside team/ or agents/: {value}"
            )
        return relative
    raise InstallStateError(f"unknown managed scope: {scope}")


def safe_destination(root: Path, relative_value: str) -> Path:
    relative = validate_relative_path(relative_value)
    if root.is_symlink():
        raise InstallStateError(f"managed root is a symlink: {root}")
    root_resolved = root.resolve(strict=False)
    candidate = root_resolved.joinpath(*relative.parts)
    try:
        candidate.relative_to(root_resolved)
    except ValueError as error:
        raise InstallStateError(f"managed path escapes root: {relative_value}") from error

    current = root_resolved
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise InstallStateError(f"symlink found in managed path: {current}")
    return candidate


def scope_root(scope: str, target: Path, claude_home: Path) -> Path:
    if scope == "project":
        return target / ".claude"
    if scope == "claude-home":
        return claude_home
    raise InstallStateError(f"unknown managed scope: {scope}")


def write_json_atomic(path: Path, payload: dict, mode: int = 0o600) -> None:
    if path.parent.is_symlink():
        raise InstallStateError(f"JSON parent must not be a symlink: {path.parent}")
    ensure_directory_durable(path.parent)
    temp_path = prepare_internal_stage(
        path.with_name(f".{path.name}.ccg-json-stage")
    )
    try:
        with temp_path.open("w", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_path, mode)
        fsync_file(temp_path)
        os.replace(temp_path, path)
        fsync_directory(path.parent)
    finally:
        if temp_path.exists():
            remove_path_durably(temp_path)


def run_git(target: Path, *arguments: str) -> subprocess.CompletedProcess:
    environment = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}
    return subprocess.run(
        ["git", "-C", str(target), *arguments],
        text=True,
        capture_output=True,
        env=environment,
        check=False,
    )


def ensure_state_is_git_local(target: Path) -> None:
    if shutil.which("git") is None:
        return
    inside = run_git(target, "rev-parse", "--is-inside-work-tree")
    if inside.returncode != 0 or inside.stdout.strip() != "true":
        return
    target_relative = STATE_RELATIVE_PATH.as_posix()
    tracked = run_git(
        target,
        "ls-files",
        "--error-unmatch",
        "--",
        target_relative,
    )
    if tracked.returncode == 0:
        raise InstallStateError(
            f"install state must not be tracked by Git: {target_relative}"
        )
    ignored = run_git(target, "check-ignore", "-q", "--", target_relative)
    if ignored.returncode == 0:
        return
    prefix_result = run_git(target, "rev-parse", "--show-prefix")
    if prefix_result.returncode != 0:
        raise InstallStateError(
            f"could not resolve Git target prefix: {prefix_result.stderr.strip()}"
        )
    target_prefix = prefix_result.stdout.rstrip("\r\n").strip("/")
    repository_relative = (
        target_prefix + "/" + target_relative
        if target_prefix
        else target_relative
    )
    exclude_pattern = "/" + repository_relative
    git_path = run_git(target, "rev-parse", "--git-path", "info/exclude")
    if git_path.returncode != 0 or not git_path.stdout.strip():
        raise InstallStateError(
            f"could not resolve Git exclude file: {git_path.stderr.strip()}"
        )
    exclude_path = Path(git_path.stdout.strip())
    if not exclude_path.is_absolute():
        exclude_path = target / exclude_path
    if exclude_path.is_symlink():
        raise InstallStateError(
            f"Git exclude file must not be a symlink: {exclude_path}"
        )
    ensure_directory_durable(exclude_path.parent)
    try:
        import fcntl

        with exclude_path.open("a+b") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            handle.seek(0)
            content = handle.read()
            encoded = exclude_pattern.encode("utf-8")
            if encoded not in content.splitlines():
                prefix = b"" if not content or content.endswith(b"\n") else b"\n"
                handle.seek(0, os.SEEK_END)
                handle.write(prefix + encoded + b"\n")
                handle.flush()
                os.fsync(handle.fileno())
    except OSError as error:
        raise InstallStateError(
            f"could not update Git exclude file: {exclude_path}"
        ) from error
    ignored = run_git(target, "check-ignore", "-q", "--", target_relative)
    if ignored.returncode != 0:
        raise InstallStateError(
            f"Git exclude postcondition failed for: {repository_relative}"
        )


def read_json(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise InstallStateError(f"state file not found: {path}") from error
    except (json.JSONDecodeError, OSError) as error:
        raise InstallStateError(f"invalid JSON file: {path}: {error}") from error
    if not isinstance(payload, dict):
        raise InstallStateError(f"JSON root must be an object: {path}")
    return payload


def add_manifest_entry(
    entries: dict[str, dict],
    scope: str,
    relative: str,
    source: Path | None,
    executable: bool = False,
) -> None:
    relative_value = validate_scoped_path(scope, relative).as_posix()
    key = f"{scope}:{relative_value}"
    if key in entries:
        return
    expected_hash = None
    expected_mode = None
    if source is not None:
        if source.is_symlink() or not source.is_file():
            raise InstallStateError(f"managed source file is missing or unsafe: {source}")
        expected_hash = sha256_file(source)
        expected_mode = file_metadata(source)[0]
        if executable:
            expected_mode |= 0o111
    entries[key] = {
        "scope": scope,
        "path": relative_value,
        "expected_sha256": expected_hash,
        "expected_mode": expected_mode,
    }


def add_source_tree(
    entries: dict[str, dict],
    source_root: Path,
    scope: str,
    destination_prefix: str,
    executable_predicate=None,
) -> None:
    if not source_root.exists():
        return
    if source_root.is_symlink() or not source_root.is_dir():
        raise InstallStateError(f"managed source tree is unsafe: {source_root}")
    for current_root, directories, files in os.walk(source_root, followlinks=False):
        current_path = Path(current_root)
        for name in list(directories):
            directory = current_path / name
            if directory.is_symlink():
                raise InstallStateError(f"symlink found in managed source: {directory}")
        for name in sorted(files):
            source = current_path / name
            if source.is_symlink():
                raise InstallStateError(f"symlink found in managed source: {source}")
            if not source.is_file():
                continue
            suffix = source.relative_to(source_root).as_posix()
            destination = (
                PurePosixPath(destination_prefix) / PurePosixPath(suffix)
            ).as_posix()
            executable = bool(
                executable_predicate
                and executable_predicate(PurePosixPath(suffix))
            )
            add_manifest_entry(
                entries,
                scope,
                destination,
                source,
                executable=executable,
            )


def build_manifest(
    source: Path,
    profile: str,
    include_home: bool,
    explicit_paths: list[str],
    existing_state: dict | None,
) -> list[dict]:
    if profile not in VALID_PROFILES:
        raise InstallStateError(f"unknown install profile: {profile}")
    entries: dict[str, dict] = {}

    skills_root = source / "skills"
    if skills_root.is_symlink() or not skills_root.is_dir():
        raise InstallStateError(f"skills source tree is missing or unsafe: {skills_root}")
    selected_skills = PROFILE_SKILLS.get(profile)
    if selected_skills is None:
        skill_names = sorted(
            path.name
            for path in skills_root.iterdir()
            if path.is_dir() and not path.name.startswith(".")
        )
    else:
        skill_names = list(selected_skills)
    for skill_name in skill_names:
        add_source_tree(
            entries,
            source / "skills" / skill_name,
            "project",
            f"skills/{skill_name}",
        )

    for hook_name in PROFILE_HOOKS[profile]:
        add_manifest_entry(
            entries,
            "project",
            f"hooks/{hook_name}.sh",
            source / "hooks" / "boilerplates" / f"{hook_name}.sh",
            executable=True,
        )
    add_manifest_entry(
        entries,
        "project",
        "settings.local.json",
        None,
    )

    if include_home:
        if profile != "enterprise":
            raise InstallStateError("Claude-home installation requires enterprise profile")
        add_manifest_entry(
            entries,
            "claude-home",
            "team/agents.yaml",
            source / "agents.yaml",
        )
        for source_file in sorted((source / "prompts").glob("*.md")):
            add_manifest_entry(
                entries,
                "claude-home",
                f"team/prompts/{source_file.name}",
                source_file,
            )
        for source_file in sorted((source / "workflows").glob("*.yaml")):
            add_manifest_entry(
                entries,
                "claude-home",
                f"team/workflows/{source_file.name}",
                source_file,
            )
        add_source_tree(
            entries,
            source / "context",
            "claude-home",
            "team/context",
        )
        add_source_tree(
            entries,
            source / "hooks",
            "claude-home",
            "team/hooks",
            executable_predicate=lambda path: (
                len(path.parts) >= 2
                and path.parts[0] == "scripts"
                and path.suffix == ".sh"
            ),
        )
        for source_file in sorted((source / "agents").glob("*.md")):
            add_manifest_entry(
                entries,
                "claude-home",
                f"agents/{source_file.name}",
                source_file,
            )
        for source_file in sorted((source / "scripts").glob("*.sh")):
            add_manifest_entry(
                entries,
                "claude-home",
                f"team/scripts/{source_file.name}",
                source_file,
                executable=True,
            )

    for raw_value in explicit_paths:
        if ":" not in raw_value:
            raise InstallStateError(
                f"managed file must use <scope>:<path> syntax: {raw_value}"
            )
        scope, relative = raw_value.split(":", 1)
        add_manifest_entry(entries, scope, relative, None)

    if existing_state:
        for entry in existing_state["entries"]:
            if entry["scope"] == "claude-home" and not include_home:
                raise InstallStateError(
                    "existing state includes Claude-home files; use --include-home"
                )
            key = f"{entry['scope']}:{entry['path']}"
            entries.setdefault(
                key,
                {
                    "scope": entry["scope"],
                    "path": entry["path"],
                    "expected_sha256": entry["installed_sha256"],
                    "expected_mode": entry["installed_mode"],
                },
            )
    return [entries[key] for key in sorted(entries)]


def manifest_by_key(entries: list[dict]) -> dict[str, dict]:
    return {
        f"{entry['scope']}:{entry['path']}": entry
        for entry in entries
    }


def validate_manifest_entries(raw_entries: object) -> list[dict]:
    if not isinstance(raw_entries, list):
        raise InstallStateError("snapshot managed entries must be a list")
    entries = []
    seen = set()
    for entry in raw_entries:
        if not isinstance(entry, dict) or set(entry) != MANIFEST_ENTRY_KEYS:
            raise InstallStateError("invalid managed manifest entry shape")
        if not isinstance(entry["path"], str):
            raise InstallStateError("managed path must be a string")
        validate_scoped_path(entry["scope"], entry["path"])
        key = f"{entry['scope']}:{entry['path']}"
        if key in seen:
            raise InstallStateError(f"duplicate managed entry: {key}")
        seen.add(key)
        expected_hash = entry["expected_sha256"]
        expected_mode = entry["expected_mode"]
        if expected_hash is None:
            if expected_mode is not None:
                raise InstallStateError("unhashed managed entry cannot declare a mode")
        elif (
            not isinstance(expected_hash, str)
            or not SHA256_PATTERN.fullmatch(expected_hash)
            or type(expected_mode) is not int
            or not 0 <= expected_mode <= 0o7777
        ):
            raise InstallStateError("invalid managed source hash or mode")
        entries.append(dict(entry))
    return entries


def scan_manifest(
    target: Path,
    claude_home: Path,
    manifest: list[dict],
) -> dict[str, dict]:
    records = {}
    for entry in manifest:
        key = f"{entry['scope']}:{entry['path']}"
        destination = safe_destination(
            scope_root(entry["scope"], target, claude_home),
            entry["path"],
        )
        if not destination.exists():
            continue
        if destination.is_symlink() or not destination.is_file():
            raise InstallStateError(
                f"managed destination is not a regular file: {destination}"
            )
        mode, uid, gid = file_metadata(destination)
        records[key] = {
            "scope": entry["scope"],
            "path": entry["path"],
            "sha256": sha256_file(destination),
            "mode": mode,
            "uid": uid,
            "gid": gid,
            "source": destination,
        }
    return records


def serialized_record(record: dict) -> dict:
    return {key: record[key] for key in SNAPSHOT_ENTRY_KEYS}


def validate_restorable_ownership(record: dict) -> None:
    if os.geteuid() == 0:
        return
    if record["uid"] != os.geteuid():
        raise InstallStateError(
            f"cannot safely restore owner for {record['scope']}:{record['path']}"
        )
    allowed_groups = set(os.getgroups()) | {os.getegid()}
    if record["gid"] not in allowed_groups:
        raise InstallStateError(
            f"cannot safely restore group for {record['scope']}:{record['path']}"
        )


def apply_metadata(path: Path, mode: int, uid: int, gid: int) -> None:
    try:
        os.chown(path, uid, gid, follow_symlinks=False)
        os.chmod(path, mode, follow_symlinks=False)
    except (OSError, NotImplementedError) as error:
        raise InstallStateError(f"failed to restore file ownership/mode: {path}") from error


def copy_record_file(record: dict, destination: Path) -> None:
    ensure_directory_durable(destination.parent)
    temp_path = prepare_internal_stage(
        destination.with_name(f".{destination.name}.ccg-copy-stage")
    )
    try:
        shutil.copyfile(record["source"], temp_path, follow_symlinks=False)
        apply_metadata(
            temp_path,
            record["mode"],
            record["uid"],
            record["gid"],
        )
        fsync_file(temp_path)
        os.replace(temp_path, destination)
        fsync_directory(destination.parent)
    finally:
        if temp_path.exists():
            remove_path_durably(temp_path)


def snapshot_file_path(snapshot: Path, scope: str, relative: str) -> Path:
    return safe_destination(snapshot / "files" / scope, relative)


def state_payload_path(
    state_root: Path,
    kind: str,
    scope: str,
    relative: str,
) -> Path:
    if kind not in {"previous", "installed"}:
        raise InstallStateError(f"invalid state payload kind: {kind}")
    return safe_destination(state_root / kind / scope, relative)


def resolved_state_home(create: bool) -> Path:
    state_home = managed_state_home()
    if state_home.is_symlink():
        raise InstallStateError(f"managed state home must not be a symlink: {state_home}")
    if create:
        ensure_directory_durable(state_home)
    if not state_home.exists() or not state_home.is_dir():
        raise InstallStateError(f"managed state home is missing or unsafe: {state_home}")
    os.chmod(state_home, 0o700)
    return state_home.resolve()


def transaction_parent_for(target: Path, create: bool) -> Path:
    state_home = resolved_state_home(create=create)
    transactions = state_home / "transactions"
    target_root = transactions / path_identity(target)
    for directory in (transactions, target_root):
        if directory.is_symlink():
            raise InstallStateError(
                f"transaction directory must not be a symlink: {directory}"
            )
        if create:
            ensure_directory_durable(directory)
            os.chmod(directory, 0o700)
    if not target_root.exists() or not target_root.is_dir():
        raise InstallStateError(
            f"transaction directory is missing or unsafe: {target_root}"
        )
    return target_root.resolve()


def new_transaction_path(target: Path) -> Path:
    parent = transaction_parent_for(target, create=True)
    return parent / secrets.token_hex(16)


def is_persistent_transaction(snapshot: Path, target: Path) -> bool:
    try:
        snapshot.resolve(strict=False).relative_to(
            transaction_parent_for(target, create=True)
        )
    except ValueError:
        return False
    return True


def transaction_file(snapshot: Path) -> Path:
    return snapshot / "transaction.json"


def runtime_transaction_file(snapshot: Path) -> Path:
    return snapshot / "runtime.json"


def runtime_before_path(snapshot: Path, scope: str, relative: str) -> Path:
    return safe_destination(snapshot / "before" / scope, relative)


def transaction_key(snapshot: Path) -> str:
    return hashlib.sha256(
        str(snapshot.resolve(strict=False)).encode("utf-8")
    ).hexdigest()[:16]


def internal_path(
    snapshot: Path,
    destination: Path,
    purpose: str,
) -> Path:
    return destination.with_name(
        f".{destination.name}.ccg-{purpose}-{transaction_key(snapshot)}"
    )


def runtime_capture_path(snapshot: Path, destination: Path) -> Path:
    return destination.with_name(
        f".{destination.name}.ccg-quarantine-{transaction_key(snapshot)}"
    )


def recovery_capture_path(snapshot: Path, destination: Path) -> Path:
    return internal_path(snapshot, destination, "recovery")


def publish_stage_path(snapshot: Path, destination: Path) -> Path:
    return internal_path(snapshot, destination, "stage")


def runtime_stage_path(snapshot: Path, destination: Path) -> Path:
    return internal_path(snapshot, destination, "runtime-stage")


def read_runtime_transaction(snapshot: Path) -> dict:
    path = runtime_transaction_file(snapshot)
    if not path.exists() or path.is_symlink() or not path.is_file():
        raise InstallStateError(
            f"runtime transaction journal missing or unsafe: {path}"
        )
    payload = read_json(path)
    expected = {
        "schema_version",
        "kind",
        "status",
        "target_id",
        "claude_home_id",
        "state_id",
        "entries",
    }
    if set(payload) != expected:
        raise InstallStateError(f"invalid runtime transaction shape: {path}")
    if (
        payload["schema_version"] != SCHEMA_VERSION
        or payload["kind"] not in {"repair", "uninstall"}
        or payload["status"] not in RUNTIME_TRANSACTION_STATUSES
        or not isinstance(payload["entries"], list)
        or not isinstance(payload["state_id"], str)
        or not STATE_ID_PATTERN.fullmatch(payload["state_id"])
    ):
        raise InstallStateError(f"invalid runtime transaction values: {path}")
    for key in ("target_id", "claude_home_id"):
        if (
            not isinstance(payload[key], str)
            or not PATH_ID_PATTERN.fullmatch(payload[key])
        ):
            raise InstallStateError(f"invalid runtime transaction {key}: {path}")
    required_entry_keys = {
        "scope",
        "path",
        "before_exists",
        "before_sha256",
        "before_mode",
        "before_uid",
        "before_gid",
        "after_prefix",
    }
    seen = set()
    for entry in payload["entries"]:
        if not isinstance(entry, dict) or set(entry) != required_entry_keys:
            raise InstallStateError(f"invalid runtime transaction entry: {path}")
        validate_scoped_path(entry["scope"], entry["path"])
        key = f"{entry['scope']}:{entry['path']}"
        if key in seen:
            raise InstallStateError(f"duplicate runtime transaction entry: {key}")
        seen.add(key)
        validate_optional_file_fields(
            {
                "before_exists": entry["before_exists"],
                "before_sha256": entry["before_sha256"],
                "before_mode": entry["before_mode"],
                "before_uid": entry["before_uid"],
                "before_gid": entry["before_gid"],
            },
            "before",
        )
        if entry["after_prefix"] not in {"installed", "previous"}:
            raise InstallStateError(
                f"invalid runtime transaction after prefix: {key}"
            )
    return payload


def write_runtime_transaction(snapshot: Path, payload: dict) -> None:
    write_json_atomic(runtime_transaction_file(snapshot), payload)


def update_runtime_transaction(snapshot: Path, status: str) -> dict:
    if status not in RUNTIME_TRANSACTION_STATUSES:
        raise InstallStateError(f"invalid runtime transaction status: {status}")
    payload = read_runtime_transaction(snapshot)
    payload["status"] = status
    write_runtime_transaction(snapshot, payload)
    return payload


def read_transaction(snapshot: Path) -> dict:
    path = transaction_file(snapshot)
    if not path.exists() or path.is_symlink() or not path.is_file():
        raise InstallStateError(f"transaction journal missing or unsafe: {path}")
    payload = read_json(path)
    expected = {
        "schema_version",
        "kind",
        "status",
        "target_id",
        "claude_home_id",
        "include_home",
        "pending_state_id",
        "old_state_id",
        "published",
    }
    if set(payload) != expected:
        raise InstallStateError(f"invalid transaction journal shape: {path}")
    if (
        payload["schema_version"] != SCHEMA_VERSION
        or payload["kind"] != "install"
        or payload["status"] not in TRANSACTION_STATUSES
        or not isinstance(payload["include_home"], bool)
        or not isinstance(payload["published"], list)
        or any(not isinstance(item, str) for item in payload["published"])
        or len(set(payload["published"])) != len(payload["published"])
    ):
        raise InstallStateError(f"invalid transaction journal values: {path}")
    for key in ("target_id", "claude_home_id"):
        if (
            not isinstance(payload[key], str)
            or not PATH_ID_PATTERN.fullmatch(payload[key])
        ):
            raise InstallStateError(f"invalid transaction {key}: {path}")
    for key in ("pending_state_id", "old_state_id"):
        value = payload[key]
        if value is not None and (
            not isinstance(value, str) or not STATE_ID_PATTERN.fullmatch(value)
        ):
            raise InstallStateError(f"invalid transaction {key}: {path}")
    return payload


def write_transaction(snapshot: Path, payload: dict) -> None:
    write_json_atomic(transaction_file(snapshot), payload)


def update_transaction(snapshot: Path, status: str, **updates) -> dict:
    if status not in TRANSACTION_STATUSES:
        raise InstallStateError(f"invalid transaction status: {status}")
    payload = read_transaction(snapshot)
    payload.update(updates)
    payload["status"] = status
    write_transaction(snapshot, payload)
    return payload


def capture_path_for(snapshot: Path, destination: Path) -> Path:
    return destination.with_name(
        f".{destination.name}.ccg-base-{transaction_key(snapshot)}"
    )


def remove_path_durably(path: Path) -> None:
    if not path.exists():
        return
    path.unlink()
    fsync_directory(path.parent)


def initialize_transaction_directory(
    output: Path,
    journal_name: str,
    journal: dict,
) -> None:
    ensure_directory_durable(output.parent)
    stage = output.with_name(f".{output.name}.ccg-init")
    if output.exists() or output.is_symlink():
        raise InstallStateError(f"transaction output already exists: {output}")
    if stage.exists() or stage.is_symlink():
        raise InstallStateError(
            f"incomplete transaction staging requires review: {stage}"
        )
    ensure_directory_durable(stage)
    try:
        write_json_atomic(stage / journal_name, journal)
        os.rename(stage, output)
        fsync_directory(output.parent)
    except Exception:
        if stage.exists() and stage.is_dir() and not stage.is_symlink():
            shutil.rmtree(stage)
            fsync_directory(stage.parent)
        raise


def cleanup_directory_durably(path: Path, prefix: str) -> None:
    if not path.exists():
        return
    if path.is_symlink() or not path.is_dir():
        raise InstallStateError(f"cleanup path is unsafe: {path}")
    parent = path.parent
    tombstone = parent / (
        f".{prefix}-{path.name}-{secrets.token_hex(8)}"
    )
    os.rename(path, tombstone)
    fsync_directory(parent)
    shutil.rmtree(tombstone)
    fsync_directory(parent)


def cleanup_transaction_directory(snapshot: Path, target: Path) -> None:
    if not is_persistent_transaction(snapshot, target):
        return
    cleanup_directory_durably(snapshot, "cleanup")


def cleanup_state_generation(state_root: Path, target: Path) -> None:
    if not state_root.exists():
        return
    state_home = state_root.parent
    tombstone = state_home / (
        f".cleanup-state-{path_identity(target)}-"
        f"{state_root.name}-{secrets.token_hex(8)}"
    )
    os.rename(state_root, tombstone)
    fsync_directory(state_home)
    shutil.rmtree(tombstone)
    fsync_directory(state_home)


def cleanup_stale_tombstones(target: Path) -> None:
    transaction_parent = transaction_parent_for(target, create=True)
    for stage in transaction_parent.glob(".*.ccg-init"):
        if stage.is_symlink() or not stage.is_dir():
            raise InstallStateError(
                f"unsafe transaction staging directory: {stage}"
            )
        cleanup_directory_durably(stage, "cleanup-init")
    for tombstone in transaction_parent.glob(".cleanup-*"):
        if tombstone.is_symlink() or not tombstone.is_dir():
            raise InstallStateError(
                f"unsafe transaction cleanup tombstone: {tombstone}"
            )
        shutil.rmtree(tombstone)
        fsync_directory(transaction_parent)
    state_home = resolved_state_home(create=True)
    for tombstone in state_home.glob(
        f".cleanup-state-{path_identity(target)}-*"
    ):
        if tombstone.is_symlink() or not tombstone.is_dir():
            raise InstallStateError(
                f"unsafe state cleanup tombstone: {tombstone}"
            )
        shutil.rmtree(tombstone)
        fsync_directory(state_home)


@contextlib.contextmanager
def target_lock(target: Path):
    state_home = resolved_state_home(create=True)
    lock_root = state_home / "locks"
    if lock_root.is_symlink():
        raise InstallStateError(f"lock directory must not be a symlink: {lock_root}")
    ensure_directory_durable(lock_root)
    os.chmod(lock_root, 0o700)
    lock_path = lock_root / f"{path_identity(target)}.lock"
    descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise InstallStateError(
                f"another install-state operation holds the target lock: {target}"
            ) from error
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def state_root_for(state_id: str, must_exist: bool) -> Path:
    if not STATE_ID_PATTERN.fullmatch(state_id):
        raise InstallStateError(
            "invalid state_id: expected 32 lowercase hex characters"
        )
    state_home = resolved_state_home(create=False)
    state_root = state_home / state_id
    if state_root.is_symlink():
        raise InstallStateError(f"managed state payload is a symlink: {state_root}")
    if must_exist and (not state_root.exists() or not state_root.is_dir()):
        raise InstallStateError(f"managed state payload missing or unsafe: {state_root}")
    return state_root


def validate_payload_file(entry: dict, state_root: Path, kind: str) -> None:
    prefix = "installed" if kind == "installed" else "previous"
    exists = entry[f"{prefix}_exists"]
    if not exists:
        return
    payload = state_payload_path(
        state_root,
        kind,
        entry["scope"],
        entry["path"],
    )
    if not payload.exists() or payload.is_symlink() or not payload.is_file():
        raise InstallStateError(f"{kind} payload missing or unsafe: {payload}")
    if (
        sha256_file(payload) != entry[f"{prefix}_sha256"]
        or file_metadata(payload)[0] != entry[f"{prefix}_mode"]
    ):
        raise InstallStateError(f"{kind} payload integrity check failed: {payload}")


def validate_optional_file_fields(entry: dict, prefix: str) -> None:
    exists = entry[f"{prefix}_exists"]
    hash_value = entry[f"{prefix}_sha256"]
    mode = entry[f"{prefix}_mode"]
    uid = entry[f"{prefix}_uid"]
    gid = entry[f"{prefix}_gid"]
    if not isinstance(exists, bool):
        raise InstallStateError(f"{prefix} existence flag must be boolean")
    if not exists:
        if any(value is not None for value in (hash_value, mode, uid, gid)):
            raise InstallStateError(
                f"missing {prefix} file must not have metadata"
            )
        return
    if (
        not isinstance(hash_value, str)
        or not SHA256_PATTERN.fullmatch(hash_value)
        or type(mode) is not int
        or not 0 <= mode <= 0o7777
        or type(uid) is not int
        or uid < 0
        or type(gid) is not int
        or gid < 0
    ):
        raise InstallStateError(f"invalid {prefix} file metadata")


def validate_state(payload: dict) -> dict:
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise InstallStateError(
            f"unsupported schema version: {payload.get('schema_version')}"
        )
    if set(payload) != STATE_KEYS:
        missing = sorted(STATE_KEYS - set(payload))
        extra = sorted(set(payload) - STATE_KEYS)
        raise InstallStateError(f"invalid state keys: missing={missing} extra={extra}")
    if (
        not isinstance(payload["state_id"], str)
        or not STATE_ID_PATTERN.fullmatch(payload["state_id"])
    ):
        raise InstallStateError(
            "invalid state_id: expected 32 lowercase hex characters"
        )
    for key in ("target_id", "claude_home_id"):
        value = payload[key]
        if not isinstance(value, str) or not PATH_ID_PATTERN.fullmatch(value):
            raise InstallStateError(
                f"invalid {key}: expected 24 lowercase hex characters"
            )
    for key in (
        "guide_version",
        "profile",
        "installed_at",
        "source_revision",
    ):
        if not isinstance(payload[key], str) or not payload[key]:
            raise InstallStateError(f"invalid {key}: expected a non-empty string")
    if not isinstance(payload["entries"], list):
        raise InstallStateError("state entries must be a list")
    seen = set()
    for entry in payload["entries"]:
        if not isinstance(entry, dict) or set(entry) != ENTRY_KEYS:
            raise InstallStateError("invalid install-state entry shape")
        if not isinstance(entry["path"], str):
            raise InstallStateError("entry path must be a string")
        validate_scoped_path(entry["scope"], entry["path"])
        key = f"{entry['scope']}:{entry['path']}"
        if key in seen:
            raise InstallStateError(f"duplicate install-state entry: {key}")
        seen.add(key)
        validate_optional_file_fields(entry, "installed")
        validate_optional_file_fields(entry, "previous")
    return payload


def load_existing_state(target: Path) -> dict | None:
    state_file = target / STATE_RELATIVE_PATH
    if not state_file.exists():
        return None
    if state_file.is_symlink():
        raise InstallStateError(f"install state must not be a symlink: {state_file}")
    payload = validate_state(read_json(state_file))
    if payload["target_id"] != path_identity(target):
        raise InstallStateError("install state target does not match requested target")
    return payload


def deserialize_record_list(raw_entries: object) -> dict[str, dict]:
    if not isinstance(raw_entries, list):
        raise InstallStateError("snapshot files must be a list")
    records = {}
    for entry in raw_entries:
        if not isinstance(entry, dict) or set(entry) != SNAPSHOT_ENTRY_KEYS:
            raise InstallStateError("invalid snapshot entry shape")
        if not isinstance(entry["path"], str):
            raise InstallStateError("snapshot path must be a string")
        validate_scoped_path(entry["scope"], entry["path"])
        if (
            not isinstance(entry["sha256"], str)
            or not SHA256_PATTERN.fullmatch(entry["sha256"])
            or type(entry["mode"]) is not int
            or not 0 <= entry["mode"] <= 0o7777
            or type(entry["uid"]) is not int
            or entry["uid"] < 0
            or type(entry["gid"]) is not int
            or entry["gid"] < 0
        ):
            raise InstallStateError("invalid snapshot file metadata")
        key = f"{entry['scope']}:{entry['path']}"
        if key in records:
            raise InstallStateError(f"duplicate snapshot entry: {key}")
        records[key] = dict(entry)
    return records


def deserialize_snapshot(snapshot: Path) -> tuple[dict, list[dict], dict[str, dict]]:
    payload = read_json(snapshot / "snapshot.json")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise InstallStateError(
            f"unsupported snapshot schema version: {payload.get('schema_version')}"
        )
    expected_keys = {
        "schema_version",
        "target_id",
        "claude_home_id",
        "include_home",
        "profile",
        "source_revision",
        "managed",
        "files",
    }
    if set(payload) != expected_keys:
        raise InstallStateError("invalid snapshot metadata shape")
    manifest = validate_manifest_entries(payload["managed"])
    records = deserialize_record_list(payload["files"])
    return payload, manifest, records


def load_authorized_entries(
    snapshot: Path,
    manifest: list[dict],
) -> dict[str, dict]:
    path = snapshot / AUTHORIZED_RELATIVE_PATH
    if not path.exists():
        return {}
    payload = read_json(path)
    if set(payload) != {"schema_version", "entries"}:
        raise InstallStateError("invalid authorized-file metadata shape")
    if payload["schema_version"] != SCHEMA_VERSION:
        raise InstallStateError("unsupported authorized-file schema version")
    entries = validate_manifest_entries(payload["entries"])
    declared = manifest_by_key(manifest)
    authorized = {}
    for entry in entries:
        key = f"{entry['scope']}:{entry['path']}"
        if key not in declared or declared[key]["expected_sha256"] is not None:
            raise InstallStateError(
                f"authorized file is not a generated managed path: {key}"
            )
        authorized[key] = entry
    return authorized


def validate_snapshot_identity(
    snapshot_meta: dict,
    target: Path,
    claude_home: Path,
    include_home: bool,
) -> None:
    if snapshot_meta.get("target_id") != path_identity(target):
        raise InstallStateError("snapshot target does not match requested target")
    if snapshot_meta.get("claude_home_id") != path_identity(claude_home):
        raise InstallStateError("snapshot Claude home does not match requested home")
    if bool(snapshot_meta.get("include_home")) != bool(include_home):
        raise InstallStateError("snapshot include-home mode does not match")


def validate_snapshot_payload(snapshot: Path, records: dict[str, dict]) -> None:
    for record in records.values():
        source = snapshot_file_path(
            snapshot,
            record["scope"],
            record["path"],
        )
        if (
            not source.exists()
            or source.is_symlink()
            or not source.is_file()
            or sha256_file(source) != record["sha256"]
            or file_metadata(source)[0] != record["mode"]
        ):
            raise InstallStateError(f"snapshot payload integrity check failed: {source}")


def records_equal(left: dict | None, right: dict | None) -> bool:
    if left is None or right is None:
        return left is right
    return all(
        left[key] == right[key]
        for key in ("sha256", "mode", "uid", "gid")
    )


def command_begin(args: argparse.Namespace) -> int:
    target = validate_target(Path(args.target))
    claude_home = Path(args.claude_home).expanduser().resolve(strict=False)
    source = validate_source(Path(args.source))
    existing_state = load_existing_state(target)
    if (
        existing_state
        and existing_state["claude_home_id"] != path_identity(claude_home)
    ):
        raise InstallStateError(
            "Claude home does not match the existing install state; "
            "uninstall with the recorded home before reinstalling"
        )
    if existing_state and existing_state["source_revision"] != args.source_revision:
        if existing_state["profile"] != args.profile:
            raise InstallStateError(
                "source revision and profile changed together; uninstall the "
                "existing profile before installing the new one"
            )
        if not args.allow_source_change:
            raise InstallStateError(
                "source revision changed; rerun with --force after reviewing "
                "the new source"
            )
    if existing_state:
        state_root = state_root_for(existing_state["state_id"], must_exist=True)
        for entry in existing_state["entries"]:
            validate_payload_file(entry, state_root, "installed")
            validate_payload_file(entry, state_root, "previous")

    manifest = build_manifest(
        source,
        args.profile,
        args.include_home,
        args.managed_file,
        existing_state,
    )
    records = scan_manifest(target, claude_home, manifest)
    for record in records.values():
        validate_restorable_ownership(record)

    output = Path(args.output) if args.output else new_transaction_path(target)
    if output.exists():
        raise InstallStateError(f"snapshot output already exists: {output}")
    transaction = {
        "schema_version": SCHEMA_VERSION,
        "kind": "install",
        "status": "initializing",
        "target_id": path_identity(target),
        "claude_home_id": path_identity(claude_home),
        "include_home": bool(args.include_home),
        "pending_state_id": None,
        "old_state_id": existing_state["state_id"] if existing_state else None,
        "published": [],
    }
    initialize_transaction_directory(
        output,
        transaction_file(output).name,
        transaction,
    )
    try:
        serialized_records = []
        for key in sorted(records):
            record = records[key]
            copy_record_file(
                record,
                snapshot_file_path(output, record["scope"], record["path"]),
            )
            serialized_records.append(serialized_record(record))
        snapshot = {
            "schema_version": SCHEMA_VERSION,
            "target_id": path_identity(target),
            "claude_home_id": path_identity(claude_home),
            "include_home": bool(args.include_home),
            "profile": args.profile,
            "source_revision": args.source_revision,
            "managed": manifest,
            "files": serialized_records,
        }
        write_json_atomic(output / "snapshot.json", snapshot)
        update_transaction(output, "prepared")
    except Exception:
        if output.exists():
            cleanup_directory_durably(output, "aborted-begin")
        raise
    print(f"snapshot: {len(serialized_records)} files")
    print(f"transaction: {output}")
    return 0


def restore_capture_exclusive(capture: Path, destination: Path) -> None:
    try:
        os.link(capture, destination, follow_symlinks=False)
    except FileExistsError as error:
        raise InstallStateError(
            "generated-file base could not be restored without overwriting "
            f"concurrent content; capture preserved at {capture}"
        ) from error
    fsync_directory(destination.parent)
    remove_path_durably(capture)


def optional_path_record(entry: dict, path: Path) -> dict | None:
    if not path.exists():
        if path.is_symlink():
            raise InstallStateError(f"captured path is a symlink: {path}")
        return None
    return path_record(entry, path)


def record_matches_any(
    record: dict | None,
    candidates: list[dict | None],
) -> bool:
    return any(records_equal(record, candidate) for candidate in candidates)


def copy_record_file_exclusive(
    record: dict,
    destination: Path,
    stage: Path,
) -> None:
    ensure_directory_durable(destination.parent)
    prepare_internal_stage(stage)
    try:
        shutil.copyfile(record["source"], stage, follow_symlinks=False)
        apply_metadata(
            stage,
            record["mode"],
            record["uid"],
            record["gid"],
        )
        fsync_file(stage)
        os.link(stage, destination, follow_symlinks=False)
        fsync_directory(destination.parent)
    except FileExistsError as error:
        raise InstallStateError(
            f"destination changed during recovery: {destination}"
        ) from error
    finally:
        if stage.exists():
            remove_path_durably(stage)


def converge_path_exclusive(
    entry: dict,
    destination: Path,
    allowed: list[dict | None],
    desired: dict | None,
    mutation_capture: Path,
    stage: Path,
) -> bool:
    """Converge one path without overwriting an unverified concurrent edit."""
    ensure_directory_durable(destination.parent)
    if mutation_capture.exists():
        captured = path_record(entry, mutation_capture)
        if not record_matches_any(captured, allowed):
            if not destination.exists():
                restore_capture_exclusive(mutation_capture, destination)
            raise InstallStateError(
                "recovery preserved unexpected concurrent drift: "
                f"{entry['scope']}:{entry['path']}"
            )
        current = optional_path_record(entry, destination)
        if records_equal(current, desired):
            remove_path_durably(mutation_capture)
            if stage.exists():
                remove_path_durably(stage)
            return False
        if current is not None:
            raise InstallStateError(
                "recovery preserved concurrent destination and capture: "
                f"{entry['scope']}:{entry['path']}"
            )
        changed = True
    else:
        current = optional_path_record(entry, destination)
        if records_equal(current, desired):
            if stage.exists():
                remove_path_durably(stage)
            return False
        if not record_matches_any(current, allowed):
            raise InstallStateError(
                "recovery preserved unexpected concurrent drift: "
                f"{entry['scope']}:{entry['path']}"
            )
        changed = True
        if current is not None:
            os.replace(destination, mutation_capture)
            fsync_directory(destination.parent)
            captured = path_record(entry, mutation_capture)
            if not records_equal(captured, current):
                if not destination.exists():
                    restore_capture_exclusive(mutation_capture, destination)
                raise InstallStateError(
                    "recovery preserved edit captured after validation: "
                    f"{entry['scope']}:{entry['path']}"
                )

    if desired is not None:
        copy_record_file_exclusive(desired, destination, stage)
    elif destination.exists():
        raise InstallStateError(
            "destination appeared during recovery: "
            f"{entry['scope']}:{entry['path']}"
        )
    if mutation_capture.exists():
        remove_path_durably(mutation_capture)
    final = optional_path_record(entry, destination)
    if not records_equal(final, desired):
        raise InstallStateError(
            "recovery preserved a destination edited during finalization: "
            f"{entry['scope']}:{entry['path']}"
        )
    return changed


def command_publish(args: argparse.Namespace) -> int:
    target = validate_target(Path(args.target))
    claude_home = Path(
        getattr(
            args,
            "claude_home",
            os.environ.get(
                "CLAUDE_CONFIG_DIR",
                str(Path.home() / ".claude"),
            ),
        )
    ).expanduser().resolve(strict=False)
    snapshot = Path(args.snapshot)
    transaction = read_transaction(snapshot)
    if transaction["status"] != "prepared":
        raise InstallStateError(
            f"transaction is not publishable: {transaction['status']}"
        )
    snapshot_meta, manifest, before = deserialize_snapshot(snapshot)
    if snapshot_meta["target_id"] != path_identity(target):
        raise InstallStateError("snapshot target does not match requested target")
    if snapshot_meta["claude_home_id"] != path_identity(claude_home):
        raise InstallStateError("snapshot Claude home does not match requested home")
    validate_snapshot_payload(snapshot, before)
    key = f"{args.scope}:{args.path}"
    declared = manifest_by_key(manifest)
    if key not in declared:
        raise InstallStateError(f"path is not a declared managed file: {key}")
    current = scan_manifest(target, claude_home, [declared[key]]).get(key)
    if not records_equal(before.get(key), current):
        raise InstallStateError(f"managed file base changed since begin: {key}")
    source = Path(args.source)
    if source.is_symlink() or not source.is_file():
        raise InstallStateError(f"managed source is missing or unsafe: {source}")
    source_hash = sha256_file(source)
    source_mode = file_metadata(source)[0]
    generated = declared[key]["expected_sha256"] is None
    expected_mode = (
        source_mode if generated else declared[key]["expected_mode"]
    )
    if generated:
        authorized = load_authorized_entries(snapshot, manifest)
        authorized[key] = {
            "scope": args.scope,
            "path": args.path,
            "expected_sha256": source_hash,
            "expected_mode": expected_mode,
        }
        write_json_atomic(
            snapshot / AUTHORIZED_RELATIVE_PATH,
            {
                "schema_version": SCHEMA_VERSION,
                "entries": [authorized[item] for item in sorted(authorized)],
            },
        )
    elif source_hash != declared[key]["expected_sha256"]:
        raise InstallStateError(f"managed source does not match manifest: {key}")

    current = scan_manifest(target, claude_home, [declared[key]]).get(key)
    if not records_equal(before.get(key), current):
        raise InstallStateError(
            f"managed file base changed after journal authorization: {key}"
        )
    destination = safe_destination(
        scope_root(args.scope, target, claude_home),
        args.path,
    )
    ensure_directory_durable(destination.parent)
    destination = safe_destination(
        scope_root(args.scope, target, claude_home),
        args.path,
    )
    capture = (
        capture_path_for(snapshot, destination)
        if before.get(key) is not None
        else None
    )
    stage = prepare_internal_stage(publish_stage_path(snapshot, destination))
    if capture is not None and capture.exists():
        raise InstallStateError(f"transaction capture already exists: {capture}")
    shutil.copyfile(source, stage, follow_symlinks=False)
    os.chmod(stage, expected_mode, follow_symlinks=False)
    fsync_file(stage)
    capture = None
    try:
        if before.get(key) is not None:
            capture = capture_path_for(snapshot, destination)
            os.replace(destination, capture)
            fsync_directory(destination.parent)
            fault_point("publish_after_capture")
            if not records_equal(before[key], path_record(declared[key], capture)):
                restore_capture_exclusive(capture, destination)
                capture = None
                raise InstallStateError(
                    f"managed file base changed during publish: {key}"
                )
        elif destination.exists():
            raise InstallStateError(f"managed file appeared during publish: {key}")
        try:
            os.link(stage, destination, follow_symlinks=False)
            fsync_directory(destination.parent)
            fault_point("publish_after_link")
        except FileExistsError as error:
            raise InstallStateError(
                f"managed destination changed during publish: {key}"
            ) from error
    except (InstallStateError, OSError) as error:
        base_capture = capture_path_for(snapshot, destination)
        base_valid = False
        if base_capture.exists():
            try:
                captured = path_record(declared[key], base_capture)
            except (InstallStateError, OSError) as capture_error:
                raise InstallStateError(
                    f"publish failed ({error}); base capture is unsafe: "
                    f"{base_capture}"
                ) from capture_error
            if before.get(key) is None or not records_equal(
                before[key],
                captured,
            ):
                if not destination.exists():
                    restore_capture_exclusive(base_capture, destination)
                raise InstallStateError(
                    f"publish failed ({error}); an edit captured after "
                    f"validation was preserved: {key}"
                ) from error
            base_valid = True
        try:
            current = optional_path_record(declared[key], destination)
        except InstallStateError as current_error:
            raise InstallStateError(
                f"publish failed ({error}); destination was preserved: {key}"
            ) from current_error
        allowed = [before.get(key)]
        if current is None:
            if before.get(key) is not None and not base_valid:
                raise InstallStateError(
                    f"publish failed ({error}); destination disappeared: {key}"
                ) from error
            if before.get(key) is not None:
                allowed.append(None)
        elif not records_equal(current, before.get(key)):
            if (
                current["sha256"] != source_hash
                or current["mode"] != expected_mode
            ):
                raise InstallStateError(
                    f"publish failed ({error}); concurrent destination was "
                    f"preserved: {key}"
                ) from error
            allowed.append(current)
        desired = None
        if before.get(key) is not None:
            desired = dict(before[key])
            desired["source"] = snapshot_file_path(
                snapshot,
                args.scope,
                args.path,
            )
        try:
            converge_path_exclusive(
                declared[key],
                destination,
                allowed,
                desired,
                recovery_capture_path(snapshot, destination),
                internal_path(snapshot, destination, "rollback-stage"),
            )
        except (InstallStateError, OSError) as recovery_error:
            raise InstallStateError(
                f"publish failed ({error}); recovery preserved transaction: "
                f"{recovery_error}"
            ) from error
        if base_capture.exists():
            remove_path_durably(base_capture)
        raise
    finally:
        if stage.exists():
            remove_path_durably(stage)
    if generated:
        try:
            remove_path_durably(source)
        except OSError as error:
            print(
                f"WARNING: generated source temp retained: {source}: {error}",
                file=sys.stderr,
            )
    transaction = read_transaction(snapshot)
    if key not in transaction["published"]:
        transaction["published"].append(key)
        write_transaction(snapshot, transaction)
    print(f"published: {key}")
    return 0


def current_matches_trusted(
    current: dict,
    manifest_entry: dict,
    authorized_entry: dict | None,
) -> bool:
    if authorized_entry is not None:
        if (
            current["sha256"] == authorized_entry["expected_sha256"]
            and current["mode"] == authorized_entry["expected_mode"]
        ):
            return True
    return (
        manifest_entry["expected_sha256"] is not None
        and current["sha256"] == manifest_entry["expected_sha256"]
        and current["mode"] == manifest_entry["expected_mode"]
    )


def remove_empty_parents(path: Path, stop: Path) -> None:
    current = path.parent
    stop_resolved = stop.resolve(strict=False)
    while current != stop_resolved:
        try:
            current.rmdir()
        except OSError:
            return
        current = current.parent


def rollback_snapshot(
    target: Path,
    claude_home: Path,
    snapshot: Path,
    include_home: bool,
) -> int:
    snapshot_meta, manifest, before = deserialize_snapshot(snapshot)
    validate_snapshot_identity(
        snapshot_meta,
        target,
        claude_home,
        include_home,
    )
    validate_snapshot_payload(snapshot, before)
    authorized = load_authorized_entries(snapshot, manifest)
    declared = manifest_by_key(manifest)
    conflicts = []
    restored = 0
    for key in sorted(declared, reverse=True):
        manifest_entry = declared[key]
        before_record = before.get(key)
        scope, relative = key.split(":", 1)
        root = scope_root(scope, target, claude_home)
        destination = safe_destination(root, relative)
        publish_stage = publish_stage_path(snapshot, destination)
        try:
            prepare_internal_stage(publish_stage)
        except InstallStateError:
            conflicts.append(key)
            continue
        base_capture = capture_path_for(snapshot, destination)
        base_capture_valid = False
        if base_capture.exists():
            if before_record is None:
                conflicts.append(key)
                continue
            try:
                captured = path_record(manifest_entry, base_capture)
            except (InstallStateError, OSError):
                conflicts.append(key)
                continue
            if not records_equal(before_record, captured):
                if not destination.exists():
                    try:
                        restore_capture_exclusive(base_capture, destination)
                    except InstallStateError:
                        pass
                conflicts.append(key)
                continue
            base_capture_valid = True

        mutation_capture = recovery_capture_path(snapshot, destination)
        try:
            current_record = optional_path_record(
                manifest_entry,
                destination,
            )
        except InstallStateError:
            conflicts.append(key)
            continue
        allowed = [before_record]
        if current_record is None:
            if (
                before_record is not None
                and not base_capture_valid
                and not mutation_capture.exists()
            ):
                conflicts.append(key)
                continue
            if before_record is not None:
                allowed.append(None)
        elif not records_equal(before_record, current_record):
            if not current_matches_trusted(
                current_record,
                manifest_entry,
                authorized.get(key),
            ):
                conflicts.append(key)
                continue
            allowed.append(current_record)

        if mutation_capture.exists():
            try:
                mutation_record = path_record(
                    manifest_entry,
                    mutation_capture,
                )
            except (InstallStateError, OSError):
                conflicts.append(key)
                continue
            if (
                not records_equal(mutation_record, before_record)
                and not current_matches_trusted(
                    mutation_record,
                    manifest_entry,
                    authorized.get(key),
                )
            ):
                if not destination.exists():
                    try:
                        restore_capture_exclusive(
                            mutation_capture,
                            destination,
                        )
                    except InstallStateError:
                        pass
                conflicts.append(key)
                continue
            allowed.append(mutation_record)

        desired = None
        if before_record is not None:
            desired = dict(before_record)
            desired["source"] = snapshot_file_path(
                snapshot,
                scope,
                relative,
            )
        try:
            changed = converge_path_exclusive(
                manifest_entry,
                destination,
                allowed,
                desired,
                mutation_capture,
                internal_path(snapshot, destination, "rollback-stage"),
            )
        except (InstallStateError, OSError):
            conflicts.append(key)
            continue
        if base_capture.exists():
            remove_path_durably(base_capture)
        if publish_stage.exists():
            remove_path_durably(publish_stage)
        if changed:
            if before_record is None:
                remove_empty_parents(destination, root)
            restored += 1

    if conflicts:
        raise InstallStateError(
            f"rollback restored {restored} safe files but preserved unexpected "
            "drift on declared paths: " + ", ".join(conflicts)
        )
    update_transaction(snapshot, "aborted")
    return restored


def command_abort(args: argparse.Namespace) -> int:
    target = validate_target(Path(args.target))
    claude_home = Path(args.claude_home).expanduser().resolve(strict=False)
    snapshot = Path(args.snapshot)
    transaction = read_transaction(snapshot)
    if transaction["status"] in {"commit-ready", "committed"}:
        complete_install_commit(
            snapshot,
            target,
            claude_home,
            transaction,
        )
        cleanup_transaction_directory(snapshot, target)
        print("commit recovered: 1 transaction")
        return 0
    restored = rollback_snapshot(
        target,
        claude_home,
        snapshot,
        args.include_home,
    )
    print(f"rolled back: {restored} declared files")
    cleanup_transaction_directory(snapshot, target)
    return 0


def cleanup_install_captures(
    snapshot: Path,
    target: Path,
    claude_home: Path,
    manifest: list[dict],
) -> None:
    for entry in manifest:
        destination = safe_destination(
            scope_root(entry["scope"], target, claude_home),
            entry["path"],
        )
        for internal in (
            capture_path_for(snapshot, destination),
            publish_stage_path(snapshot, destination),
        ):
            if internal.exists():
                remove_path_durably(internal)


def changed_record_keys(before: dict, after: dict) -> set[str]:
    return {
        key
        for key in set(before) | set(after)
        if not records_equal(before.get(key), after.get(key))
    }


def new_entry(scope: str, relative: str, previous: dict | None, installed: dict | None):
    return {
        "scope": scope,
        "path": relative,
        "installed_exists": installed is not None,
        "installed_sha256": installed["sha256"] if installed else None,
        "installed_mode": installed["mode"] if installed else None,
        "installed_uid": installed["uid"] if installed else None,
        "installed_gid": installed["gid"] if installed else None,
        "previous_exists": previous is not None,
        "previous_sha256": previous["sha256"] if previous else None,
        "previous_mode": previous["mode"] if previous else None,
        "previous_uid": previous["uid"] if previous else None,
        "previous_gid": previous["gid"] if previous else None,
    }


def payload_record(entry: dict, prefix: str, source: Path) -> dict:
    return {
        "scope": entry["scope"],
        "path": entry["path"],
        "sha256": entry[f"{prefix}_sha256"],
        "mode": entry[f"{prefix}_mode"],
        "uid": entry[f"{prefix}_uid"],
        "gid": entry[f"{prefix}_gid"],
        "source": source,
    }


def command_finalize(args: argparse.Namespace) -> int:
    target = validate_target(Path(args.target))
    claude_home = Path(args.claude_home).expanduser().resolve(strict=False)
    snapshot = Path(args.snapshot)
    transaction = read_transaction(snapshot)
    if transaction["status"] != "prepared":
        raise InstallStateError(
            f"transaction is not finalizable: {transaction['status']}"
        )
    snapshot_meta, manifest, before = deserialize_snapshot(snapshot)
    validate_snapshot_identity(
        snapshot_meta,
        target,
        claude_home,
        args.include_home,
    )
    if snapshot_meta["profile"] != args.profile:
        raise InstallStateError("snapshot profile does not match finalize profile")
    if snapshot_meta["source_revision"] != args.source_revision:
        raise InstallStateError(
            "snapshot source revision does not match finalize source"
        )
    validate_snapshot_payload(snapshot, before)
    after = scan_manifest(target, claude_home, manifest)
    authorized = load_authorized_entries(snapshot, manifest)
    declared = manifest_by_key(manifest)
    for key, manifest_entry in declared.items():
        if (
            manifest_entry["expected_sha256"] is None
            or key not in transaction["published"]
        ):
            continue
        current = after.get(key)
        if (
            current is None
            or current["sha256"] != manifest_entry["expected_sha256"]
            or current["mode"] != manifest_entry["expected_mode"]
        ):
            raise InstallStateError(
                f"managed file changed before finalize: {key}"
            )
    for key, authorized_entry in authorized.items():
        current = after.get(key)
        if (
            current is None
            or current["sha256"] != authorized_entry["expected_sha256"]
            or current["mode"] != authorized_entry["expected_mode"]
        ):
            raise InstallStateError(
                f"authorized generated file changed before finalize: {key}"
            )
    changed_keys = changed_record_keys(before, after)
    unjournaled = changed_keys - set(transaction["published"])
    if unjournaled:
        raise InstallStateError(
            "finalize found changes without a completed publish journal; "
            "run recover instead: " + ", ".join(sorted(unjournaled))
        )

    ensure_state_is_git_local(target)
    existing_state = load_existing_state(target)
    old_state_root = None
    existing_entries = {}
    if existing_state:
        if existing_state["claude_home_id"] != path_identity(claude_home):
            raise InstallStateError(
                "Claude home does not match the existing install state"
            )
        old_state_root = state_root_for(
            existing_state["state_id"],
            must_exist=True,
        )
        for entry in existing_state["entries"]:
            validate_payload_file(entry, old_state_root, "previous")
            validate_payload_file(entry, old_state_root, "installed")
            existing_entries[f"{entry['scope']}:{entry['path']}"] = entry

    state_home = resolved_state_home(create=True)
    state_id = secrets.token_hex(16)
    pending = state_home / f".pending-{state_id}"
    ensure_directory_durable(pending)
    os.chmod(pending, 0o700)
    state_root = state_home / state_id
    update_transaction(
        snapshot,
        "prepared",
        pending_state_id=state_id,
        old_state_id=existing_state["state_id"] if existing_state else None,
    )
    try:
        entries = []
        for key in sorted(set(existing_entries) | changed_keys):
            scope, relative = key.split(":", 1)
            old_entry = existing_entries.get(key)
            if old_entry and key not in changed_keys:
                entry = dict(old_entry)
                for prefix in ("previous", "installed"):
                    if not entry[f"{prefix}_exists"]:
                        continue
                    source = state_payload_path(
                        old_state_root,
                        prefix,
                        scope,
                        relative,
                    )
                    copy_record_file(
                        payload_record(old_entry, prefix, source),
                        state_payload_path(
                            pending,
                            prefix,
                            scope,
                            relative,
                        ),
                    )
                entries.append(entry)
                continue
            if old_entry:
                previous = (
                    {
                        "sha256": old_entry["previous_sha256"],
                        "mode": old_entry["previous_mode"],
                        "uid": old_entry["previous_uid"],
                        "gid": old_entry["previous_gid"],
                    }
                    if old_entry["previous_exists"]
                    else None
                )
            else:
                previous = before.get(key)
            installed = after.get(key)
            entry = new_entry(scope, relative, previous, installed)

            if entry["previous_exists"]:
                if old_entry:
                    source = state_payload_path(
                        old_state_root,
                        "previous",
                        scope,
                        relative,
                    )
                    record = payload_record(old_entry, "previous", source)
                else:
                    record = dict(before[key])
                    record["source"] = snapshot_file_path(
                        snapshot,
                        scope,
                        relative,
                    )
                copy_record_file(
                    record,
                    state_payload_path(
                        pending,
                        "previous",
                        scope,
                        relative,
                    ),
                )
            if entry["installed_exists"]:
                copy_record_file(
                    installed,
                    state_payload_path(
                        pending,
                        "installed",
                        scope,
                        relative,
                    ),
                )
            entries.append(entry)

        state = {
            "schema_version": SCHEMA_VERSION,
            "guide_version": GUIDE_VERSION,
            "profile": args.profile,
            "installed_at": datetime.now(timezone.utc).isoformat(),
            "source_revision": args.source_revision,
            "state_id": state_id,
            "target_id": path_identity(target),
            "claude_home_id": path_identity(claude_home),
            "entries": entries,
        }
        validate_state(state)
        for entry in entries:
            validate_payload_file(entry, pending, "previous")
            validate_payload_file(entry, pending, "installed")
        os.rename(pending, state_root)
        fsync_directory(state_home)
        fault_point("finalize_after_state_generation")
        write_json_atomic(snapshot / "next-state.json", state)
        update_transaction(snapshot, "commit-ready")
        fault_point("finalize_after_commit_ready")
        write_json_atomic(target / STATE_RELATIVE_PATH, state)
        fault_point("finalize_after_state_publish")
        update_transaction(snapshot, "committed")
    finally:
        if pending.exists():
            cleanup_state_generation(pending, target)

    cleanup_install_captures(snapshot, target, claude_home, manifest)
    if old_state_root and old_state_root != state_root:
        try:
            cleanup_state_generation(old_state_root, target)
        except OSError as error:
            print(
                f"WARNING: stale state generation retained: {old_state_root}: {error}",
                file=sys.stderr,
            )
    cleanup_transaction_directory(snapshot, target)
    print(f"managed: {len(changed_keys)} changed files")
    return 0


def cleanup_pending_generation(transaction: dict, target: Path) -> None:
    state_id = transaction["pending_state_id"]
    if state_id is None:
        return
    state_home = resolved_state_home(create=True)
    for path in (state_home / state_id, state_home / f".pending-{state_id}"):
        if path.exists():
            if path.is_symlink() or not path.is_dir():
                raise InstallStateError(
                    f"pending state generation is unsafe: {path}"
                )
            cleanup_state_generation(path, target)


def complete_install_commit(
    snapshot: Path,
    target: Path,
    claude_home: Path,
    transaction: dict,
) -> None:
    state_path = snapshot / "next-state.json"
    if not state_path.exists() or state_path.is_symlink():
        raise InstallStateError(
            f"commit-ready transaction is missing next state: {state_path}"
        )
    state = validate_state(read_json(state_path))
    if (
        state["target_id"] != path_identity(target)
        or state["claude_home_id"] != path_identity(claude_home)
        or state["state_id"] != transaction["pending_state_id"]
    ):
        raise InstallStateError("commit-ready transaction identity mismatch")
    state_root = state_root_for(state["state_id"], must_exist=True)
    for entry in state["entries"]:
        validate_payload_file(entry, state_root, "previous")
        validate_payload_file(entry, state_root, "installed")
        destination = safe_destination(
            scope_root(entry["scope"], target, claude_home),
            entry["path"],
        )
        if entry["installed_exists"]:
            if (
                not destination.exists()
                or destination.is_symlink()
                or not destination.is_file()
                or not record_matches_entry(
                    path_record(entry, destination),
                    entry,
                    "installed",
                )
            ):
                raise InstallStateError(
                    "managed file changed during commit recovery: "
                    f"{entry['scope']}:{entry['path']}"
                )
        elif destination.exists():
            raise InstallStateError(
                "managed file appeared during commit recovery: "
                f"{entry['scope']}:{entry['path']}"
            )
    write_json_atomic(target / STATE_RELATIVE_PATH, state)
    update_transaction(snapshot, "committed")
    _, manifest, _ = deserialize_snapshot(snapshot)
    cleanup_install_captures(snapshot, target, claude_home, manifest)
    old_state_id = transaction["old_state_id"]
    if old_state_id and old_state_id != state["state_id"]:
        old_state_root = state_root_for(old_state_id, must_exist=False)
        if old_state_root.exists():
            cleanup_state_generation(old_state_root, target)


def recover_install_transaction(
    snapshot: Path,
    target: Path,
    claude_home: Path,
) -> None:
    transaction = read_transaction(snapshot)
    if (
        transaction["target_id"] != path_identity(target)
        or transaction["claude_home_id"] != path_identity(claude_home)
    ):
        raise InstallStateError(
            f"transaction identity does not match recovery request: {snapshot}"
        )
    status = transaction["status"]
    if status == "initializing":
        cleanup_pending_generation(transaction, target)
        cleanup_transaction_directory(snapshot, target)
        return
    if status in {"commit-ready", "committed"}:
        complete_install_commit(
            snapshot,
            target,
            claude_home,
            transaction,
        )
        cleanup_transaction_directory(snapshot, target)
        return
    if status in {"prepared", "aborted"}:
        if status == "prepared":
            rollback_snapshot(
                target,
                claude_home,
                snapshot,
                transaction["include_home"],
            )
        cleanup_pending_generation(transaction, target)
        cleanup_transaction_directory(snapshot, target)
        return
    raise InstallStateError(f"unsupported transaction status: {status}")


def recover_runtime_transaction(
    snapshot: Path,
    target: Path,
    claude_home: Path,
) -> None:
    journal = read_runtime_transaction(snapshot)
    if (
        journal["target_id"] != path_identity(target)
        or journal["claude_home_id"] != path_identity(claude_home)
    ):
        raise InstallStateError(
            f"runtime transaction identity mismatch: {snapshot}"
        )
    if journal["status"] == "initializing":
        cleanup_transaction_directory(snapshot, target)
        return
    state = runtime_state(snapshot)
    state_root = state_root_for(state["state_id"], must_exist=False)
    side = "before" if journal["status"] == "prepared" else "after"
    restore_runtime_side(
        snapshot,
        target,
        claude_home,
        journal,
        state,
        state_root,
        side,
    )
    state_file = target / STATE_RELATIVE_PATH
    if journal["kind"] == "uninstall":
        if side == "before":
            write_json_atomic(state_file, state)
        else:
            remove_path_durably(state_file)
            if state_root.exists():
                cleanup_state_generation(state_root, target)
    if side == "after" and journal["status"] != "committed":
        update_runtime_transaction(snapshot, "committed")
    cleanup_transaction_directory(snapshot, target)


def recover_incomplete_transactions(
    target: Path,
    claude_home: Path,
) -> int:
    cleanup_stale_tombstones(target)
    parent = transaction_parent_for(target, create=True)
    recovered = 0
    for snapshot in sorted(parent.iterdir()):
        if snapshot.is_symlink() or not snapshot.is_dir():
            raise InstallStateError(
                f"unsafe transaction entry blocks recovery: {snapshot}"
            )
        if transaction_file(snapshot).is_file():
            recover_install_transaction(snapshot, target, claude_home)
        elif runtime_transaction_file(snapshot).is_file():
            recover_runtime_transaction(snapshot, target, claude_home)
        else:
            raise InstallStateError(
                f"transaction journal missing; manual review required: {snapshot}"
            )
        recovered += 1
    return recovered


def command_recover(args: argparse.Namespace) -> int:
    target = validate_target(Path(args.target))
    claude_home = Path(args.claude_home).expanduser().resolve(strict=False)
    recovered = recover_incomplete_transactions(target, claude_home)
    render_result(
        {
            "schema_version": SCHEMA_VERSION,
            "status": "recovered",
            "recovered": recovered,
        },
        args.json,
    )
    return 0


def load_runtime_state(
    target_value: str,
    claude_home_value: str,
) -> tuple[Path, Path, dict, Path]:
    target = validate_target(Path(target_value))
    claude_home = Path(claude_home_value).expanduser().resolve(strict=False)
    state = load_existing_state(target)
    if state is None:
        raise InstallStateError(
            f"install state file not found: {target / STATE_RELATIVE_PATH}"
        )
    if state["claude_home_id"] != path_identity(claude_home):
        raise InstallStateError("Claude home does not match recorded install state")
    state_root = state_root_for(state["state_id"], must_exist=True)
    return target, claude_home, state, state_root


def inspect_runtime_state(
    target: Path,
    claude_home: Path,
    state: dict,
) -> tuple[dict, dict[str, dict | None]]:
    issues = []
    observed: dict[str, dict | None] = {}
    for entry in state["entries"]:
        key = f"{entry['scope']}:{entry['path']}"
        destination = safe_destination(
            scope_root(entry["scope"], target, claude_home),
            entry["path"],
        )
        record = None
        reason = None
        if destination.exists():
            if destination.is_symlink() or not destination.is_file():
                reason = "not-file"
            else:
                record = path_record(entry, destination)
        observed[key] = record
        if entry["installed_exists"]:
            if record is None:
                reason = reason or "missing"
            elif not record_matches_entry(record, entry, "installed"):
                reason = "drift"
        elif destination.exists():
            reason = reason or "unexpected"
        if reason:
            issues.append(
                {
                    "scope": entry["scope"],
                    "path": entry["path"],
                    "reason": reason,
                }
            )
    report = {
        "schema_version": SCHEMA_VERSION,
        "status": "drifted" if issues else "ok",
        "managed": len(state["entries"]),
        "source_revision": state["source_revision"],
        "issues": issues,
    }
    return report, observed


def doctor_report(target: Path, claude_home: Path, state: dict) -> dict:
    return inspect_runtime_state(target, claude_home, state)[0]


def render_result(payload: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return
    for key, value in payload.items():
        if key == "issues":
            continue
        print(f"{key}: {value}")
    for issue in payload.get("issues", []):
        print(f"- {issue['scope']}:{issue['path']} ({issue['reason']})")


def command_doctor(args: argparse.Namespace) -> int:
    target, claude_home, state, _ = load_runtime_state(
        args.target,
        args.claude_home,
    )
    report = doctor_report(target, claude_home, state)
    render_result(report, args.json)
    return 1 if report["status"] == "drifted" else 0


def path_record(entry: dict, path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise InstallStateError(f"captured path is not a regular file: {path}")
    mode, uid, gid = file_metadata(path)
    return {
        "scope": entry["scope"],
        "path": entry["path"],
        "sha256": sha256_file(path),
        "mode": mode,
        "uid": uid,
        "gid": gid,
        "source": path,
    }


def record_matches_entry(record: dict | None, entry: dict, prefix: str) -> bool:
    if not entry[f"{prefix}_exists"]:
        return record is None
    if record is None:
        return False
    return all(
        record[field] == entry[f"{prefix}_{field}"]
        for field in ("sha256", "mode", "uid", "gid")
    )


def expected_entry_record(entry: dict, prefix: str) -> dict | None:
    if not entry[f"{prefix}_exists"]:
        return None
    return {
        "scope": entry["scope"],
        "path": entry["path"],
        "sha256": entry[f"{prefix}_sha256"],
        "mode": entry[f"{prefix}_mode"],
        "uid": entry[f"{prefix}_uid"],
        "gid": entry[f"{prefix}_gid"],
    }


def copy_payload_exclusive(
    entry: dict,
    prefix: str,
    destination: Path,
    state_root: Path,
    stage: Path,
) -> None:
    source = state_payload_path(
        state_root,
        prefix,
        entry["scope"],
        entry["path"],
    )
    record = payload_record(entry, prefix, source)
    copy_record_file_exclusive(record, destination, stage)


def runtime_entry_before_record(entry: dict) -> dict | None:
    if not entry["before_exists"]:
        return None
    return {
        "scope": entry["scope"],
        "path": entry["path"],
        "sha256": entry["before_sha256"],
        "mode": entry["before_mode"],
        "uid": entry["before_uid"],
        "gid": entry["before_gid"],
    }


def begin_runtime_transaction(
    kind: str,
    target: Path,
    claude_home: Path,
    state: dict,
    entries: list[dict],
    before_records: dict[str, dict | None],
) -> Path:
    snapshot = new_transaction_path(target)
    serialized_entries = []
    for entry in entries:
        key = f"{entry['scope']}:{entry['path']}"
        before = before_records[key]
        serialized_entries.append(
            {
                "scope": entry["scope"],
                "path": entry["path"],
                "before_exists": before is not None,
                "before_sha256": before["sha256"] if before else None,
                "before_mode": before["mode"] if before else None,
                "before_uid": before["uid"] if before else None,
                "before_gid": before["gid"] if before else None,
                "after_prefix": (
                    "installed" if kind == "repair" else "previous"
                ),
            }
        )
    journal = {
        "schema_version": SCHEMA_VERSION,
        "kind": kind,
        "status": "initializing",
        "target_id": path_identity(target),
        "claude_home_id": path_identity(claude_home),
        "state_id": state["state_id"],
        "entries": serialized_entries,
    }
    initialize_transaction_directory(
        snapshot,
        runtime_transaction_file(snapshot).name,
        journal,
    )
    write_json_atomic(snapshot / "state.json", state)
    try:
        for entry in entries:
            key = f"{entry['scope']}:{entry['path']}"
            expected = before_records[key]
            destination = safe_destination(
                scope_root(entry["scope"], target, claude_home),
                entry["path"],
            )
            current = (
                path_record(entry, destination)
                if destination.exists()
                and not destination.is_symlink()
                and destination.is_file()
                else None
            )
            if not records_equal(expected, current):
                raise InstallStateError(
                    f"managed file changed before {kind}: {destination}"
                )
            if expected is not None:
                record = dict(expected)
                record["source"] = destination
                copy_record_file(
                    record,
                    runtime_before_path(
                        snapshot,
                        entry["scope"],
                        entry["path"],
                    ),
                )
        update_runtime_transaction(snapshot, "prepared")
    except Exception:
        if snapshot.exists():
            cleanup_directory_durably(snapshot, "aborted-runtime")
        raise
    return snapshot


def runtime_state(snapshot: Path) -> dict:
    state_path = snapshot / "state.json"
    if not state_path.exists() or state_path.is_symlink():
        raise InstallStateError(
            f"runtime transaction state is missing or unsafe: {state_path}"
        )
    return validate_state(read_json(state_path))


def runtime_state_and_root(snapshot: Path) -> tuple[dict, Path]:
    state = runtime_state(snapshot)
    return state, state_root_for(state["state_id"], must_exist=True)


def runtime_state_entries(state: dict) -> dict[str, dict]:
    return {
        f"{entry['scope']}:{entry['path']}": entry
        for entry in state["entries"]
    }


def restore_runtime_side(
    snapshot: Path,
    target: Path,
    claude_home: Path,
    journal: dict,
    state: dict,
    state_root: Path,
    side: str,
) -> None:
    state_entries = runtime_state_entries(state)
    for runtime_entry in journal["entries"]:
        key = f"{runtime_entry['scope']}:{runtime_entry['path']}"
        state_entry = state_entries[key]
        before = runtime_entry_before_record(runtime_entry)
        after = expected_entry_record(
            state_entry,
            runtime_entry["after_prefix"],
        )
        destination = safe_destination(
            scope_root(runtime_entry["scope"], target, claude_home),
            runtime_entry["path"],
        )
        operation_capture = runtime_capture_path(snapshot, destination)
        operation_capture_valid = False
        if operation_capture.exists():
            try:
                captured = path_record(state_entry, operation_capture)
            except (InstallStateError, OSError) as error:
                if not destination.exists():
                    try:
                        restore_capture_exclusive(
                            operation_capture,
                            destination,
                        )
                    except InstallStateError:
                        pass
                raise InstallStateError(
                    f"runtime capture could not be verified: {key}"
                ) from error
            if not records_equal(captured, before):
                if not destination.exists():
                    restore_capture_exclusive(
                        operation_capture,
                        destination,
                    )
                raise InstallStateError(
                    "runtime recovery preserved an edit captured after "
                    f"validation: {key}"
                )
            operation_capture_valid = True

        desired = (
            before
            if side == "before"
            else after
        )
        desired_with_source = None
        if desired is not None:
            desired_with_source = dict(desired)
            if side == "before":
                desired_with_source["source"] = runtime_before_path(
                    snapshot,
                    runtime_entry["scope"],
                    runtime_entry["path"],
                )
            else:
                desired_with_source["source"] = state_payload_path(
                    state_root,
                    runtime_entry["after_prefix"],
                    runtime_entry["scope"],
                    runtime_entry["path"],
                )
        allowed = [before, after]
        if operation_capture_valid and not record_matches_any(None, allowed):
            allowed.append(None)
        converge_path_exclusive(
            state_entry,
            destination,
            allowed,
            desired_with_source,
            recovery_capture_path(snapshot, destination),
            runtime_stage_path(snapshot, destination),
        )
        if operation_capture.exists():
            remove_path_durably(operation_capture)


def execute_runtime_transaction(
    snapshot: Path,
    target: Path,
    claude_home: Path,
    state: dict,
    state_root: Path,
) -> None:
    journal = read_runtime_transaction(snapshot)
    state_entries = runtime_state_entries(state)
    try:
        for runtime_entry in journal["entries"]:
            key = f"{runtime_entry['scope']}:{runtime_entry['path']}"
            state_entry = state_entries[key]
            expected = runtime_entry_before_record(runtime_entry)
            destination = safe_destination(
                scope_root(runtime_entry["scope"], target, claude_home),
                runtime_entry["path"],
            )
            capture = runtime_capture_path(snapshot, destination)
            if capture.exists():
                raise InstallStateError(
                    f"runtime transaction capture already exists: {capture}"
                )
            if expected is not None:
                if (
                    not destination.exists()
                    or destination.is_symlink()
                    or not destination.is_file()
                ):
                    raise InstallStateError(
                        f"managed file changed before {journal['kind']}: "
                        f"{destination}"
                    )
                os.replace(destination, capture)
                fsync_directory(destination.parent)
                try:
                    captured = path_record(state_entry, capture)
                except (InstallStateError, OSError) as error:
                    if not destination.exists():
                        restore_capture_exclusive(capture, destination)
                    raise InstallStateError(
                        f"managed file capture failed during "
                        f"{journal['kind']}: {destination}"
                    ) from error
                if not records_equal(captured, expected):
                    if not destination.exists():
                        restore_capture_exclusive(capture, destination)
                    raise InstallStateError(
                        f"managed file changed during {journal['kind']}: "
                        f"{destination}"
                    )
                fault_point(f"{journal['kind']}_after_capture")
            elif destination.exists():
                raise InstallStateError(
                    f"managed file appeared during {journal['kind']}: "
                    f"{destination}"
                )
            prefix = runtime_entry["after_prefix"]
            if state_entry[f"{prefix}_exists"]:
                copy_payload_exclusive(
                    state_entry,
                    prefix,
                    destination,
                    state_root,
                    runtime_stage_path(snapshot, destination),
                )
            fault_point(f"{journal['kind']}_after_publish")

        update_runtime_transaction(snapshot, "commit-ready")
        if journal["kind"] == "uninstall":
            remove_path_durably(target / STATE_RELATIVE_PATH)
            fault_point("uninstall_after_state_unlink")
        update_runtime_transaction(snapshot, "committed")
    except (InstallStateError, OSError) as error:
        journal = read_runtime_transaction(snapshot)
        side = (
            "before"
            if journal["status"] == "prepared"
            else "after"
        )
        try:
            restore_runtime_side(
                snapshot,
                target,
                claude_home,
                journal,
                state,
                state_root,
                side,
            )
            state_file = target / STATE_RELATIVE_PATH
            if journal["kind"] == "uninstall":
                if side == "before":
                    write_json_atomic(state_file, state)
                else:
                    remove_path_durably(state_file)
                    if state_root.exists():
                        cleanup_state_generation(state_root, target)
            if side == "after" and journal["status"] != "committed":
                update_runtime_transaction(snapshot, "committed")
            cleanup_transaction_directory(snapshot, target)
        except (InstallStateError, OSError) as recovery_error:
            raise InstallStateError(
                f"runtime operation failed ({error}); recovery failed: "
                f"{recovery_error}; transaction preserved at {snapshot}"
            ) from error
        if side == "after":
            return
        raise InstallStateError(
            f"runtime operation failed and was rolled back: {error}"
        ) from error

    restore_runtime_side(
        snapshot,
        target,
        claude_home,
        read_runtime_transaction(snapshot),
        state,
        state_root,
        "after",
    )
    if journal["kind"] == "uninstall":
        cleanup_state_generation(state_root, target)
        fault_point("uninstall_after_state_generation_cleanup")
    cleanup_transaction_directory(snapshot, target)


def command_repair(args: argparse.Namespace) -> int:
    target, claude_home, state, state_root = load_runtime_state(
        args.target,
        args.claude_home,
    )
    report, observed = inspect_runtime_state(target, claude_home, state)
    issues_by_key = {
        f"{issue['scope']}:{issue['path']}": issue
        for issue in report["issues"]
    }
    entries = [
        entry
        for entry in state["entries"]
        if f"{entry['scope']}:{entry['path']}" in issues_by_key
    ]
    if not args.dry_run:
        for entry in entries:
            validate_payload_file(entry, state_root, "installed")
            safe_destination(
                scope_root(entry["scope"], target, claude_home),
                entry["path"],
            )
        snapshot = begin_runtime_transaction(
            "repair",
            target,
            claude_home,
            state,
            entries,
            observed,
        )
        execute_runtime_transaction(
            snapshot,
            target,
            claude_home,
            state,
            state_root,
        )
    result = {
        "schema_version": SCHEMA_VERSION,
        "status": "planned" if args.dry_run else "repaired",
        "planned": len(entries),
    }
    render_result(result, args.json)
    return 0


def command_uninstall(args: argparse.Namespace) -> int:
    target, claude_home, state, state_root = load_runtime_state(
        args.target,
        args.claude_home,
    )
    report = doctor_report(target, claude_home, state)
    if report["issues"] and not args.dry_run:
        raise InstallStateError(
            "managed files are drifted; repair or review them before uninstall"
        )
    if not args.dry_run:
        for entry in state["entries"]:
            validate_payload_file(entry, state_root, "previous")
            safe_destination(
                scope_root(entry["scope"], target, claude_home),
                entry["path"],
            )
        entries = list(reversed(state["entries"]))
        before_records = {
            f"{entry['scope']}:{entry['path']}": expected_entry_record(
                entry,
                "installed",
            )
            for entry in entries
        }
        snapshot = begin_runtime_transaction(
            "uninstall",
            target,
            claude_home,
            state,
            entries,
            before_records,
        )
        execute_runtime_transaction(
            snapshot,
            target,
            claude_home,
            state,
            state_root,
        )
    result = {
        "schema_version": SCHEMA_VERSION,
        "status": "planned" if args.dry_run else "uninstalled",
        "planned": len(state["entries"]),
    }
    render_result(result, args.json)
    return 0


def add_transaction_identity_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--target", required=True)
    parser.add_argument(
        "--claude-home",
        default=os.environ.get(
            "CLAUDE_CONFIG_DIR",
            str(Path.home() / ".claude"),
        ),
    )
    parser.add_argument("--include-home", action="store_true")


def add_common_runtime_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--target", required=True)
    parser.add_argument(
        "--claude-home",
        default=os.environ.get(
            "CLAUDE_CONFIG_DIR",
            str(Path.home() / ".claude"),
        ),
    )
    parser.add_argument("--json", action="store_true")


def command_transaction_path(args: argparse.Namespace) -> int:
    target = validate_target(Path(args.target))
    print(new_transaction_path(target))
    return 0


def command_lock_path(args: argparse.Namespace) -> int:
    target = validate_target(Path(args.target))
    state_home = resolved_state_home(create=True)
    lock_root = state_home / "locks"
    if lock_root.is_symlink():
        raise InstallStateError(f"lock directory must not be a symlink: {lock_root}")
    ensure_directory_durable(lock_root)
    os.chmod(lock_root, 0o700)
    print(lock_root / f"{path_identity(target)}.lock")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    begin = subparsers.add_parser("begin")
    add_transaction_identity_arguments(begin)
    begin.add_argument("--output")
    begin.add_argument(
        "--source",
        default=str(Path(__file__).resolve().parents[1]),
    )
    begin.add_argument("--profile", choices=sorted(VALID_PROFILES), default="team")
    begin.add_argument("--source-revision", required=True)
    begin.add_argument("--allow-source-change", action="store_true")
    begin.add_argument("--managed-file", action="append", default=[])
    begin.set_defaults(handler=command_begin)

    publish = subparsers.add_parser("publish")
    publish.add_argument("--target", required=True)
    publish.add_argument("--snapshot", required=True)
    publish.add_argument(
        "--claude-home",
        default=os.environ.get(
            "CLAUDE_CONFIG_DIR",
            str(Path.home() / ".claude"),
        ),
    )
    publish.add_argument(
        "--scope",
        choices=("project", "claude-home"),
        required=True,
    )
    publish.add_argument("--path", required=True)
    publish.add_argument("--source", required=True)
    publish.set_defaults(handler=command_publish)

    finalize = subparsers.add_parser("finalize")
    add_transaction_identity_arguments(finalize)
    finalize.add_argument("--snapshot", required=True)
    finalize.add_argument("--profile", required=True)
    finalize.add_argument("--source-revision", required=True)
    finalize.set_defaults(handler=command_finalize)

    abort = subparsers.add_parser("abort")
    add_transaction_identity_arguments(abort)
    abort.add_argument("--snapshot", required=True)
    abort.set_defaults(handler=command_abort)

    recover = subparsers.add_parser("recover")
    add_common_runtime_arguments(recover)
    recover.set_defaults(handler=command_recover)

    doctor = subparsers.add_parser("doctor")
    add_common_runtime_arguments(doctor)
    doctor.set_defaults(handler=command_doctor)

    repair = subparsers.add_parser("repair")
    add_common_runtime_arguments(repair)
    repair.add_argument("--dry-run", action="store_true")
    repair.set_defaults(handler=command_repair)

    uninstall = subparsers.add_parser("uninstall")
    add_common_runtime_arguments(uninstall)
    uninstall.add_argument("--dry-run", action="store_true")
    uninstall.set_defaults(handler=command_uninstall)

    transaction_path = subparsers.add_parser("transaction-path")
    transaction_path.add_argument("--target", required=True)
    transaction_path.set_defaults(handler=command_transaction_path)

    lock_path = subparsers.add_parser("lock-path")
    lock_path.add_argument("--target", required=True)
    lock_path.set_defaults(handler=command_lock_path)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        helper_commands = {"transaction-path", "lock-path"}
        def run_handler() -> int:
            should_recover = args.command == "begin" or (
                args.command in {"repair", "uninstall"}
                and not args.dry_run
            )
            if should_recover:
                target = validate_target(Path(args.target))
                claude_home = Path(args.claude_home).expanduser().resolve(
                    strict=False
                )
                recover_incomplete_transactions(target, claude_home)
            return args.handler(args)

        if (
            args.command in helper_commands
            or os.environ.get("CLAUDE_CODE_GUIDE_LOCK_HELD") == "1"
        ):
            return run_handler()
        with target_lock(validate_target(Path(args.target))):
            return run_handler()
    except InstallStateError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
