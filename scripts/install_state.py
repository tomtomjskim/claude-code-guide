#!/usr/bin/env python3
"""Track, inspect, repair, and uninstall claude-code-guide managed files."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import shutil
import stat
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


SCHEMA_VERSION = 1
GUIDE_VERSION = "4.5"
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
SNAPSHOT_ENTRY_KEYS = {"scope", "path", "sha256", "mode", "uid", "gid"}
PATH_ID_PATTERN = re.compile(r"^[0-9a-f]{24}$")
STATE_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")

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
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temp_path = path.with_name(f".{path.name}.tmp-{os.getpid()}-{secrets.token_hex(4)}")
    try:
        temp_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        os.chmod(temp_path, mode)
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


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
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temp_path = destination.with_name(
        f".{destination.name}.restore-{os.getpid()}-{secrets.token_hex(4)}"
    )
    try:
        shutil.copyfile(record["source"], temp_path, follow_symlinks=False)
        apply_metadata(
            temp_path,
            record["mode"],
            record["uid"],
            record["gid"],
        )
        os.replace(temp_path, destination)
    finally:
        if temp_path.exists():
            temp_path.unlink()


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
        state_home.mkdir(parents=True, exist_ok=True, mode=0o700)
    if not state_home.exists() or not state_home.is_dir():
        raise InstallStateError(f"managed state home is missing or unsafe: {state_home}")
    os.chmod(state_home, 0o700)
    return state_home.resolve()


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
        "managed",
        "files",
    }
    if set(payload) != expected_keys:
        raise InstallStateError("invalid snapshot metadata shape")
    manifest = validate_manifest_entries(payload["managed"])
    records = deserialize_record_list(payload["files"])
    return payload, manifest, records


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

    output = Path(args.output)
    if output.exists():
        raise InstallStateError(f"snapshot output already exists: {output}")
    output.mkdir(parents=True, mode=0o700)
    os.chmod(output, 0o700)
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
            "managed": manifest,
            "files": serialized_records,
        }
        write_json_atomic(output / "snapshot.json", snapshot)
    except Exception:
        shutil.rmtree(output, ignore_errors=True)
        raise
    print(f"snapshot: {len(serialized_records)} files")
    return 0


def current_matches_trusted(
    current: dict,
    manifest_entry: dict,
) -> bool:
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


def command_abort(args: argparse.Namespace) -> int:
    target = validate_target(Path(args.target))
    claude_home = Path(args.claude_home).expanduser().resolve(strict=False)
    snapshot = Path(args.snapshot)
    snapshot_meta, manifest, before = deserialize_snapshot(snapshot)
    validate_snapshot_identity(
        snapshot_meta,
        target,
        claude_home,
        args.include_home,
    )
    validate_snapshot_payload(snapshot, before)
    current = scan_manifest(target, claude_home, manifest)
    manifest_by_key = {
        f"{entry['scope']}:{entry['path']}": entry
        for entry in manifest
    }

    conflicts = []
    for key, manifest_entry in manifest_by_key.items():
        before_record = before.get(key)
        current_record = current.get(key)
        if records_equal(before_record, current_record):
            continue
        if current_record is None or not current_matches_trusted(
            current_record,
            manifest_entry,
        ):
            conflicts.append(key)
    if conflicts:
        raise InstallStateError(
            "rollback stopped because of unexpected drift on declared paths: "
            + ", ".join(conflicts)
        )

    restored = 0
    for key in sorted(manifest_by_key, reverse=True):
        before_record = before.get(key)
        current_record = current.get(key)
        if records_equal(before_record, current_record):
            continue
        scope, relative = key.split(":", 1)
        root = scope_root(scope, target, claude_home)
        destination = safe_destination(root, relative)
        if before_record is None:
            if destination.exists():
                destination.unlink()
                remove_empty_parents(destination, root)
        else:
            snapshot_record = dict(before_record)
            snapshot_record["source"] = snapshot_file_path(
                snapshot,
                scope,
                relative,
            )
            copy_record_file(snapshot_record, destination)
        restored += 1
    print(f"rolled back: {restored} declared files")
    return 0


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
    snapshot_meta, manifest, before = deserialize_snapshot(snapshot)
    validate_snapshot_identity(
        snapshot_meta,
        target,
        claude_home,
        args.include_home,
    )
    validate_snapshot_payload(snapshot, before)
    after = scan_manifest(target, claude_home, manifest)
    changed_keys = changed_record_keys(before, after)

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
    pending = Path(
        tempfile.mkdtemp(prefix=".pending-", dir=state_home)
    )
    os.chmod(pending, 0o700)
    state_id = secrets.token_hex(16)
    state_root = state_home / state_id
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
        try:
            write_json_atomic(target / STATE_RELATIVE_PATH, state)
        except Exception:
            shutil.rmtree(state_root, ignore_errors=True)
            raise
    finally:
        if pending.exists():
            shutil.rmtree(pending, ignore_errors=True)

    if old_state_root and old_state_root != state_root:
        try:
            shutil.rmtree(old_state_root)
        except OSError as error:
            print(
                f"WARNING: stale state generation retained: {old_state_root}: {error}",
                file=sys.stderr,
            )
    print(f"managed: {len(changed_keys)} changed files")
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


def entry_issue(entry: dict, target: Path, claude_home: Path) -> dict | None:
    destination = safe_destination(
        scope_root(entry["scope"], target, claude_home),
        entry["path"],
    )
    if entry["installed_exists"]:
        if not destination.exists():
            return {
                "scope": entry["scope"],
                "path": entry["path"],
                "reason": "missing",
            }
        if not destination.is_file():
            return {
                "scope": entry["scope"],
                "path": entry["path"],
                "reason": "not-file",
            }
        mode, uid, gid = file_metadata(destination)
        if (
            sha256_file(destination) != entry["installed_sha256"]
            or mode != entry["installed_mode"]
            or uid != entry["installed_uid"]
            or gid != entry["installed_gid"]
        ):
            return {
                "scope": entry["scope"],
                "path": entry["path"],
                "reason": "drift",
            }
    elif destination.exists():
        return {
            "scope": entry["scope"],
            "path": entry["path"],
            "reason": "unexpected",
        }
    return None


def doctor_report(target: Path, claude_home: Path, state: dict) -> dict:
    issues = []
    for entry in state["entries"]:
        issue = entry_issue(entry, target, claude_home)
        if issue:
            issues.append(issue)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "drifted" if issues else "ok",
        "managed": len(state["entries"]),
        "source_revision": state["source_revision"],
        "issues": issues,
    }


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


def apply_payload_entry(
    entry: dict,
    prefix: str,
    target: Path,
    claude_home: Path,
    state_root: Path,
) -> None:
    root = scope_root(entry["scope"], target, claude_home)
    destination = safe_destination(root, entry["path"])
    if entry[f"{prefix}_exists"]:
        source = state_payload_path(
            state_root,
            prefix,
            entry["scope"],
            entry["path"],
        )
        record = payload_record(entry, prefix, source)
        copy_record_file(record, destination)
    elif destination.exists():
        if not destination.is_file():
            raise InstallStateError(
                f"managed destination is not a file: {destination}"
            )
        destination.unlink()
        remove_empty_parents(destination, root)


def snapshot_runtime_destinations(
    entries: list[dict],
    target: Path,
    claude_home: Path,
    backup_root: Path,
) -> dict[str, dict | None]:
    backups: dict[str, dict | None] = {}
    for entry in entries:
        key = f"{entry['scope']}:{entry['path']}"
        root = scope_root(entry["scope"], target, claude_home)
        destination = safe_destination(root, entry["path"])
        if not destination.exists():
            backups[key] = None
            continue
        if destination.is_symlink() or not destination.is_file():
            raise InstallStateError(
                f"managed destination is not a regular file: {destination}"
            )
        mode, uid, gid = file_metadata(destination)
        record = {
            "scope": entry["scope"],
            "path": entry["path"],
            "sha256": sha256_file(destination),
            "mode": mode,
            "uid": uid,
            "gid": gid,
            "source": destination,
        }
        validate_restorable_ownership(record)
        backup_path = state_payload_path(
            backup_root,
            "previous",
            entry["scope"],
            entry["path"],
        )
        copy_record_file(record, backup_path)
        record["source"] = backup_path
        backups[key] = record
    return backups


def restore_runtime_destinations(
    entries: list[dict],
    backups: dict[str, dict | None],
    target: Path,
    claude_home: Path,
) -> None:
    failures = []
    for entry in reversed(entries):
        key = f"{entry['scope']}:{entry['path']}"
        root = scope_root(entry["scope"], target, claude_home)
        try:
            destination = safe_destination(root, entry["path"])
            record = backups[key]
            if record is None:
                if destination.exists():
                    if not destination.is_file():
                        raise InstallStateError(
                            f"rollback destination is not a file: {destination}"
                        )
                    destination.unlink()
                    remove_empty_parents(destination, root)
            else:
                copy_record_file(record, destination)
        except (InstallStateError, OSError) as error:
            failures.append(f"{key}: {error}")
    if failures:
        raise InstallStateError(
            "runtime rollback failed: " + "; ".join(failures)
        )


def apply_entries_transactionally(
    entries: list[dict],
    prefix: str,
    target: Path,
    claude_home: Path,
    state_root: Path,
    after_apply=None,
) -> None:
    state_home = resolved_state_home(create=True)
    backup_root = Path(
        tempfile.mkdtemp(prefix=".runtime-backup-", dir=state_home)
    )
    os.chmod(backup_root, 0o700)
    backups: dict[str, dict | None] = {}
    try:
        backups = snapshot_runtime_destinations(
            entries,
            target,
            claude_home,
            backup_root,
        )
        try:
            for entry in entries:
                apply_payload_entry(
                    entry,
                    prefix,
                    target,
                    claude_home,
                    state_root,
                )
            if after_apply:
                after_apply()
        except (InstallStateError, OSError) as error:
            try:
                restore_runtime_destinations(
                    entries,
                    backups,
                    target,
                    claude_home,
                )
            except InstallStateError as rollback_error:
                raise InstallStateError(
                    f"runtime operation failed ({error}); {rollback_error}"
                ) from error
            raise InstallStateError(
                f"runtime operation failed and was rolled back: {error}"
            ) from error
    finally:
        shutil.rmtree(backup_root, ignore_errors=True)


def command_repair(args: argparse.Namespace) -> int:
    target, claude_home, state, state_root = load_runtime_state(
        args.target,
        args.claude_home,
    )
    issues_by_key = {
        f"{issue['scope']}:{issue['path']}": issue
        for issue in doctor_report(target, claude_home, state)["issues"]
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
        apply_entries_transactionally(
            entries,
            "installed",
            target,
            claude_home,
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
        apply_entries_transactionally(
            entries,
            "previous",
            target,
            claude_home,
            state_root,
            after_apply=lambda: (target / STATE_RELATIVE_PATH).unlink(),
        )
        try:
            shutil.rmtree(state_root)
        except OSError as error:
            print(
                f"WARNING: stale state generation retained: {state_root}: {error}",
                file=sys.stderr,
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    begin = subparsers.add_parser("begin")
    add_transaction_identity_arguments(begin)
    begin.add_argument("--output", required=True)
    begin.add_argument(
        "--source",
        default=str(Path(__file__).resolve().parents[1]),
    )
    begin.add_argument("--profile", choices=sorted(VALID_PROFILES), default="team")
    begin.add_argument("--managed-file", action="append", default=[])
    begin.set_defaults(handler=command_begin)

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
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.handler(args)
    except InstallStateError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
