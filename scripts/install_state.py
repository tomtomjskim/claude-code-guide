#!/usr/bin/env python3
"""Track, inspect, repair, and uninstall claude-code-guide managed files."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import sys
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
    "state_id",
    "claude_home_id",
    "entries",
}
ENTRY_KEYS = {
    "scope",
    "path",
    "installed_exists",
    "installed_sha256",
    "installed_mode",
    "previous_exists",
    "previous_sha256",
    "previous_mode",
}
IDENTITY_PATTERN = re.compile(r"^[0-9a-f]{24}$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


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


def file_mode(path: Path) -> int:
    return stat.S_IMODE(path.stat(follow_symlinks=False).st_mode)


def validate_target(target: Path) -> Path:
    if not target.exists() or not target.is_dir():
        raise InstallStateError(f"target directory not found: {target}")
    if target.is_symlink():
        raise InstallStateError(f"target directory must not be a symlink: {target}")
    return target.resolve()


def validate_relative_path(value: str) -> PurePosixPath:
    relative = PurePosixPath(value)
    if relative.is_absolute() or not relative.parts or any(
        part in {"", ".", ".."} for part in relative.parts
    ):
        raise InstallStateError(f"unsafe managed path: {value}")
    return relative


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


def should_exclude_project_file(relative: PurePosixPath) -> bool:
    return relative.as_posix() == STATE_RELATIVE_PATH.name


def scan_scope(root: Path, scope: str, prefixes: tuple[str, ...] | None = None) -> dict:
    records: dict[str, dict] = {}
    if not root.exists():
        return records
    if root.is_symlink():
        raise InstallStateError(f"managed root is a symlink: {root}")

    scan_roots = [root / prefix for prefix in prefixes] if prefixes else [root]
    for scan_root in scan_roots:
        if not scan_root.exists():
            continue
        if scan_root.is_symlink():
            raise InstallStateError(f"symlink found in managed tree: {scan_root}")
        for current_root, directories, files in os.walk(scan_root, followlinks=False):
            current_path = Path(current_root)
            for name in list(directories):
                directory = current_path / name
                if directory.is_symlink():
                    raise InstallStateError(f"symlink found in managed tree: {directory}")
            for name in files:
                file_path = current_path / name
                if file_path.is_symlink():
                    raise InstallStateError(f"symlink found in managed tree: {file_path}")
                if not file_path.is_file():
                    continue
                relative = PurePosixPath(file_path.relative_to(root).as_posix())
                if scope == "project" and should_exclude_project_file(relative):
                    continue
                key = f"{scope}:{relative.as_posix()}"
                records[key] = {
                    "scope": scope,
                    "path": relative.as_posix(),
                    "sha256": sha256_file(file_path),
                    "mode": file_mode(file_path),
                    "source": file_path,
                }
    return records


def scan_managed_tree(
    target: Path, claude_home: Path, include_home: bool
) -> dict[str, dict]:
    records = scan_scope(target / ".claude", "project")
    if include_home:
        records.update(
            scan_scope(claude_home, "claude-home", prefixes=("team", "agents"))
        )
    return records


def write_json_atomic(path: Path, payload: dict, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temp_path = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temp_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.chmod(temp_path, mode)
    os.replace(temp_path, path)


def copy_record_file(record: dict, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    shutil.copyfile(record["source"], destination, follow_symlinks=False)
    os.chmod(destination, record["mode"])


def snapshot_file_path(snapshot: Path, scope: str, relative: str) -> Path:
    return safe_destination(snapshot / "files" / scope, relative)


def state_payload_path(
    state_root: Path, kind: str, scope: str, relative: str
) -> Path:
    if kind not in {"previous", "installed"}:
        raise InstallStateError(f"invalid state payload kind: {kind}")
    return safe_destination(state_root / kind / scope, relative)


def validate_payload_file(entry: dict, state_root: Path, kind: str) -> None:
    if kind == "installed":
        exists = entry["installed_exists"]
        expected_hash = entry["installed_sha256"]
        expected_mode = entry["installed_mode"]
    elif kind == "previous":
        exists = entry["previous_exists"]
        expected_hash = entry["previous_sha256"]
        expected_mode = entry["previous_mode"]
    else:
        raise InstallStateError(f"invalid payload kind: {kind}")
    if not exists:
        return
    payload = state_payload_path(
        state_root, kind, entry["scope"], entry["path"]
    )
    if not payload.exists() or payload.is_symlink() or not payload.is_file():
        raise InstallStateError(f"{kind} payload missing or unsafe: {payload}")
    if sha256_file(payload) != expected_hash or file_mode(payload) != expected_mode:
        raise InstallStateError(f"{kind} payload integrity check failed: {payload}")


def command_begin(args: argparse.Namespace) -> int:
    target = validate_target(Path(args.target))
    claude_home = Path(args.claude_home).expanduser().resolve(strict=False)
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
        state_root = managed_state_home() / existing_state["state_id"]
        if not state_root.exists() or state_root.is_symlink():
            raise InstallStateError(
                f"managed state payload missing or unsafe: {state_root}"
            )
        for entry in existing_state["entries"]:
            validate_payload_file(entry, state_root, "installed")
            validate_payload_file(entry, state_root, "previous")
    output = Path(args.output)
    if output.exists():
        raise InstallStateError(f"snapshot output already exists: {output}")
    output.mkdir(parents=True, mode=0o700)
    os.chmod(output, 0o700)

    records = scan_managed_tree(target, claude_home, args.include_home)
    serialized_records = []
    for key in sorted(records):
        record = records[key]
        copy_record_file(
            record,
            snapshot_file_path(output, record["scope"], record["path"]),
        )
        serialized_records.append(
            {
                "scope": record["scope"],
                "path": record["path"],
                "sha256": record["sha256"],
                "mode": record["mode"],
            }
        )

    snapshot = {
        "schema_version": SCHEMA_VERSION,
        "target_id": path_identity(target),
        "claude_home_id": path_identity(claude_home),
        "include_home": bool(args.include_home),
        "files": serialized_records,
    }
    write_json_atomic(output / "snapshot.json", snapshot)
    print(f"snapshot: {len(serialized_records)} files")
    return 0


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


def validate_state(payload: dict) -> dict:
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise InstallStateError(
            f"unsupported schema version: {payload.get('schema_version')}"
        )
    if set(payload) != STATE_KEYS:
        missing = sorted(STATE_KEYS - set(payload))
        extra = sorted(set(payload) - STATE_KEYS)
        raise InstallStateError(f"invalid state keys: missing={missing} extra={extra}")
    for key in ("state_id", "claude_home_id"):
        value = payload[key]
        if not isinstance(value, str) or not IDENTITY_PATTERN.fullmatch(value):
            raise InstallStateError(f"invalid {key}: expected 24 lowercase hex characters")
    for key in ("guide_version", "profile", "installed_at"):
        if not isinstance(payload[key], str) or not payload[key]:
            raise InstallStateError(f"invalid {key}: expected a non-empty string")
    if not isinstance(payload["entries"], list):
        raise InstallStateError("state entries must be a list")
    for entry in payload["entries"]:
        if not isinstance(entry, dict) or set(entry) != ENTRY_KEYS:
            raise InstallStateError("invalid install-state entry shape")
        if not isinstance(entry["path"], str):
            raise InstallStateError("entry path must be a string")
        validate_relative_path(entry["path"])
        if entry["scope"] not in {"project", "claude-home"}:
            raise InstallStateError(f"invalid scope: {entry['scope']}")
        if not isinstance(entry["installed_exists"], bool) or not isinstance(
            entry["previous_exists"], bool
        ):
            raise InstallStateError("entry existence flags must be booleans")
        installed_hash = entry["installed_sha256"]
        if entry["installed_exists"]:
            if not isinstance(installed_hash, str) or not SHA256_PATTERN.fullmatch(
                installed_hash
            ):
                raise InstallStateError("installed file hash must be lowercase SHA-256")
            if type(entry["installed_mode"]) is not int:
                raise InstallStateError("installed file mode must be an integer")
        elif installed_hash is not None or entry["installed_mode"] is not None:
            raise InstallStateError("missing installed file must not have hash or mode")
        if entry["previous_exists"]:
            previous_hash = entry["previous_sha256"]
            if not isinstance(previous_hash, str) or not SHA256_PATTERN.fullmatch(
                previous_hash
            ):
                raise InstallStateError("previous file hash must be lowercase SHA-256")
            if type(entry["previous_mode"]) is not int:
                raise InstallStateError("previous file mode must be an integer")
        elif (
            entry["previous_sha256"] is not None
            or entry["previous_mode"] is not None
        ):
            raise InstallStateError("missing previous file must not have hash or mode")
    return payload


def load_existing_state(target: Path) -> dict | None:
    state_file = target / STATE_RELATIVE_PATH
    if not state_file.exists():
        return None
    if state_file.is_symlink():
        raise InstallStateError(f"install state must not be a symlink: {state_file}")
    return validate_state(read_json(state_file))


def deserialize_snapshot(snapshot: Path) -> dict[str, dict]:
    payload = read_json(snapshot / "snapshot.json")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise InstallStateError(
            f"unsupported snapshot schema version: {payload.get('schema_version')}"
        )
    records = {}
    for entry in payload.get("files", []):
        if set(entry) != {"scope", "path", "sha256", "mode"}:
            raise InstallStateError("invalid snapshot entry shape")
        validate_relative_path(entry["path"])
        key = f"{entry['scope']}:{entry['path']}"
        records[key] = entry
    return payload, records


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


def command_abort(args: argparse.Namespace) -> int:
    target = validate_target(Path(args.target))
    claude_home = Path(args.claude_home).expanduser().resolve(strict=False)
    snapshot_path = Path(args.snapshot)
    snapshot_meta, before = deserialize_snapshot(snapshot_path)
    validate_snapshot_identity(
        snapshot_meta, target, claude_home, args.include_home
    )
    after = scan_managed_tree(target, claude_home, args.include_home)

    for record in before.values():
        source = snapshot_file_path(
            snapshot_path, record["scope"], record["path"]
        )
        if (
            not source.exists()
            or source.is_symlink()
            or not source.is_file()
            or sha256_file(source) != record["sha256"]
            or file_mode(source) != record["mode"]
        ):
            raise InstallStateError(f"snapshot payload integrity check failed: {source}")
        safe_destination(
            scope_root(record["scope"], target, claude_home), record["path"]
        )
    for record in after.values():
        safe_destination(
            scope_root(record["scope"], target, claude_home), record["path"]
        )

    for key in sorted(set(after) - set(before), reverse=True):
        record = after[key]
        root = scope_root(record["scope"], target, claude_home)
        destination = safe_destination(root, record["path"])
        if destination.exists():
            if not destination.is_file():
                raise InstallStateError(
                    f"rollback destination is not a file: {destination}"
                )
            destination.unlink()
            remove_empty_parents(destination, root)

    for key in sorted(before):
        record = before[key]
        root = scope_root(record["scope"], target, claude_home)
        destination = safe_destination(root, record["path"])
        if destination.exists() and not destination.is_file():
            try:
                destination.rmdir()
            except OSError as error:
                raise InstallStateError(
                    f"rollback destination has unmanaged content: {destination}"
                ) from error
        source = snapshot_file_path(
            snapshot_path, record["scope"], record["path"]
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination, follow_symlinks=False)
        os.chmod(destination, record["mode"])

    print(f"rolled back: {len(set(before) | set(after))} files inspected")
    return 0


def command_finalize(args: argparse.Namespace) -> int:
    target = validate_target(Path(args.target))
    claude_home = Path(args.claude_home).expanduser().resolve(strict=False)
    snapshot_path = Path(args.snapshot)
    snapshot_meta, before = deserialize_snapshot(snapshot_path)
    validate_snapshot_identity(
        snapshot_meta, target, claude_home, args.include_home
    )

    after = scan_managed_tree(target, claude_home, args.include_home)
    changed_keys = {
        key
        for key in set(before) | set(after)
        if before.get(key, {}).get("sha256") != after.get(key, {}).get("sha256")
        or before.get(key, {}).get("mode") != after.get(key, {}).get("mode")
    }

    existing_state = load_existing_state(target)
    state_id = (
        existing_state["state_id"] if existing_state else path_identity(target)
    )
    state_home = managed_state_home()
    state_root = state_home / state_id
    state_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(state_home, 0o700)
    os.chmod(state_root, 0o700)

    entries_by_key = {}
    if existing_state:
        entries_by_key = {
            f"{entry['scope']}:{entry['path']}": dict(entry)
            for entry in existing_state["entries"]
        }

    for key in sorted(changed_keys):
        before_record = before.get(key)
        after_record = after.get(key)
        scope, relative = key.split(":", 1)
        if key not in entries_by_key:
            previous_exists = before_record is not None
            previous_mode = before_record["mode"] if before_record else None
            if before_record:
                source = snapshot_file_path(snapshot_path, scope, relative)
                destination = state_payload_path(
                    state_root, "previous", scope, relative
                )
                destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                shutil.copyfile(source, destination, follow_symlinks=False)
                os.chmod(destination, before_record["mode"])
            entries_by_key[key] = {
                "scope": scope,
                "path": relative,
                "installed_exists": False,
                "installed_sha256": None,
                "installed_mode": None,
                "previous_exists": previous_exists,
                "previous_sha256": (
                    before_record["sha256"] if before_record else None
                ),
                "previous_mode": previous_mode,
            }

        entry = entries_by_key[key]
        entry["installed_exists"] = after_record is not None
        entry["installed_sha256"] = after_record["sha256"] if after_record else None
        entry["installed_mode"] = after_record["mode"] if after_record else None
        installed_payload = state_payload_path(
            state_root, "installed", scope, relative
        )
        if after_record:
            installed_payload.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            shutil.copyfile(
                after_record["source"], installed_payload, follow_symlinks=False
            )
            os.chmod(installed_payload, after_record["mode"])
        elif installed_payload.exists():
            installed_payload.unlink()

    state = {
        "schema_version": SCHEMA_VERSION,
        "guide_version": GUIDE_VERSION,
        "profile": args.profile,
        "installed_at": datetime.now(timezone.utc).isoformat(),
        "state_id": state_id,
        "claude_home_id": path_identity(claude_home),
        "entries": [entries_by_key[key] for key in sorted(entries_by_key)],
    }
    write_json_atomic(target / STATE_RELATIVE_PATH, state)
    print(f"managed: {len(changed_keys)} changed files")
    return 0


def load_runtime_state(
    target_value: str, claude_home_value: str
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
    state_home = managed_state_home()
    state_root = state_home / state["state_id"]
    if not state_root.exists() or state_root.is_symlink():
        raise InstallStateError(f"managed state payload missing or unsafe: {state_root}")
    return target, claude_home, state, state_root


def entry_issue(
    entry: dict, target: Path, claude_home: Path
) -> dict | None:
    destination = safe_destination(
        scope_root(entry["scope"], target, claude_home), entry["path"]
    )
    if entry["installed_exists"]:
        if not destination.exists():
            return {"scope": entry["scope"], "path": entry["path"], "reason": "missing"}
        if not destination.is_file():
            return {
                "scope": entry["scope"],
                "path": entry["path"],
                "reason": "not-file",
            }
        actual_hash = sha256_file(destination)
        actual_mode = file_mode(destination)
        if (
            actual_hash != entry["installed_sha256"]
            or actual_mode != entry["installed_mode"]
        ):
            return {"scope": entry["scope"], "path": entry["path"], "reason": "drift"}
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
        args.target, args.claude_home
    )
    report = doctor_report(target, claude_home, state)
    render_result(report, args.json)
    return 1 if report["status"] == "drifted" else 0


def apply_installed_entry(
    entry: dict,
    target: Path,
    claude_home: Path,
    state_root: Path,
) -> None:
    destination = safe_destination(
        scope_root(entry["scope"], target, claude_home), entry["path"]
    )
    if entry["installed_exists"]:
        source = state_payload_path(
            state_root, "installed", entry["scope"], entry["path"]
        )
        if not source.exists() or source.is_symlink():
            raise InstallStateError(f"installed payload missing or unsafe: {source}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination, follow_symlinks=False)
        os.chmod(destination, entry["installed_mode"])
    elif destination.exists():
        if not destination.is_file():
            raise InstallStateError(f"managed destination is not a file: {destination}")
        destination.unlink()


def command_repair(args: argparse.Namespace) -> int:
    target, claude_home, state, state_root = load_runtime_state(
        args.target, args.claude_home
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
        for entry in entries:
            apply_installed_entry(entry, target, claude_home, state_root)
    result = {
        "schema_version": SCHEMA_VERSION,
        "status": "planned" if args.dry_run else "repaired",
        "planned": len(entries),
    }
    render_result(result, args.json)
    return 0


def remove_empty_parents(path: Path, stop: Path) -> None:
    current = path.parent
    stop_resolved = stop.resolve(strict=False)
    while current != stop_resolved:
        try:
            current.rmdir()
        except OSError:
            return
        current = current.parent


def restore_previous_entry(
    entry: dict,
    target: Path,
    claude_home: Path,
    state_root: Path,
) -> None:
    root = scope_root(entry["scope"], target, claude_home)
    destination = safe_destination(root, entry["path"])
    if entry["previous_exists"]:
        source = state_payload_path(
            state_root, "previous", entry["scope"], entry["path"]
        )
        if not source.exists() or source.is_symlink():
            raise InstallStateError(f"previous payload missing or unsafe: {source}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination, follow_symlinks=False)
        os.chmod(destination, entry["previous_mode"])
    elif destination.exists():
        if not destination.is_file():
            raise InstallStateError(f"managed destination is not a file: {destination}")
        destination.unlink()
        remove_empty_parents(destination, root)


def command_uninstall(args: argparse.Namespace) -> int:
    target, claude_home, state, state_root = load_runtime_state(
        args.target, args.claude_home
    )
    report = doctor_report(target, claude_home, state)
    if report["issues"] and not args.dry_run:
        raise InstallStateError(
            "managed files are drifted; repair or review them before uninstall"
        )
    if not args.dry_run:
        for entry in state["entries"]:
            validate_payload_file(entry, state_root, "previous")
        for entry in reversed(state["entries"]):
            restore_previous_entry(entry, target, claude_home, state_root)
        (target / STATE_RELATIVE_PATH).unlink()
        shutil.rmtree(state_root)
    result = {
        "schema_version": SCHEMA_VERSION,
        "status": "planned" if args.dry_run else "uninstalled",
        "planned": len(state["entries"]),
    }
    render_result(result, args.json)
    return 0


def add_common_runtime_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--target", required=True)
    parser.add_argument(
        "--claude-home",
        default=os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude")),
    )
    parser.add_argument("--json", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    begin = subparsers.add_parser("begin")
    begin.add_argument("--target", required=True)
    begin.add_argument("--output", required=True)
    begin.add_argument(
        "--claude-home",
        default=os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude")),
    )
    begin.add_argument("--include-home", action="store_true")
    begin.set_defaults(handler=command_begin)

    finalize = subparsers.add_parser("finalize")
    finalize.add_argument("--target", required=True)
    finalize.add_argument("--snapshot", required=True)
    finalize.add_argument("--profile", required=True)
    finalize.add_argument(
        "--claude-home",
        default=os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude")),
    )
    finalize.add_argument("--include-home", action="store_true")
    finalize.set_defaults(handler=command_finalize)

    abort = subparsers.add_parser("abort")
    abort.add_argument("--target", required=True)
    abort.add_argument("--snapshot", required=True)
    abort.add_argument(
        "--claude-home",
        default=os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude")),
    )
    abort.add_argument("--include-home", action="store_true")
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
