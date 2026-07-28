#!/usr/bin/env python3
"""Validate portable claude-code-guide source surfaces."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


PORTABLE_DIRECTORIES = (
    "skills",
    "templates",
    "hooks/boilerplates",
    "scripts",
)
PORTABLE_ROOT_FILES = (
    "README.md",
    "QUICKSTART.md",
    "SETUP.md",
    "BOOTSTRAP.md",
    "CLAUDE.md",
)
SCANNED_SUFFIXES = {".md", ".sh", ".json", ".yaml", ".yml", ".py"}
HIDDEN_UNICODE_PATTERN = re.compile(
    "[\u200b\u200c\u200d\u2060\ufeff\u202a-\u202e\u2066-\u2069]"
)
PERSONAL_PATH_PATTERN = re.compile(
    r"(?P<path>/(?:Users|home)/(?!<(?:name|user)>)(?!\\?<)[^/\s`\"']+)"
)


def relative_path(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def portable_files(root: Path) -> list[Path]:
    files = []
    for directory_name in PORTABLE_DIRECTORIES:
        directory = root / directory_name
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            if (
                path.is_file()
                and (
                    path.suffix in SCANNED_SUFFIXES
                    or path.name.endswith((".json.example", ".toml.example"))
                )
                and "tests" not in path.parts
                and "__pycache__" not in path.parts
            ):
                files.append(path)
    for file_name in PORTABLE_ROOT_FILES:
        path = root / file_name
        if path.is_file():
            files.append(path)
    return sorted(set(files))


def validate(root: Path) -> dict:
    if not root.exists() or not root.is_dir():
        raise ValueError(f"repository root not found: {root}")
    root = root.resolve()
    issues = []

    skill_root = root / "skills"
    skill_dirs = sorted(path for path in skill_root.iterdir() if path.is_dir()) if skill_root.exists() else []
    for skill_dir in skill_dirs:
        if not (skill_dir / "SKILL.md").is_file():
            issues.append(
                {
                    "path": relative_path(skill_dir, root),
                    "line": 1,
                    "code": "missing-skill-contract",
                    "message": "skill directory must contain SKILL.md",
                }
            )

    files = portable_files(root)
    for path in files:
        text = path.read_text(encoding="utf-8")
        for match in HIDDEN_UNICODE_PATTERN.finditer(text):
            issues.append(
                {
                    "path": relative_path(path, root),
                    "line": line_number(text, match.start()),
                    "code": "hidden-unicode",
                    "message": (
                        "hidden or bidirectional Unicode control found: "
                        f"U+{ord(match.group(0)):04X}"
                    ),
                }
            )
        for match in PERSONAL_PATH_PATTERN.finditer(text):
            issues.append(
                {
                    "path": relative_path(path, root),
                    "line": line_number(text, match.start()),
                    "code": "personal-absolute-path",
                    "message": (
                        "portable surface contains a personal absolute path: "
                        f"{match.group('path')}"
                    ),
                }
            )

    issues.sort(key=lambda item: (item["path"], item["line"], item["code"]))
    return {
        "schema_version": 1,
        "status": "issues" if issues else "ok",
        "checked_files": len(files),
        "catalog": {
            "skills": len(skill_dirs),
            "hook_boilerplates": len(list((root / "hooks/boilerplates").glob("*.sh")))
            if (root / "hooks/boilerplates").exists()
            else 0,
        },
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        report = validate(Path(args.root))
    except (OSError, UnicodeError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    else:
        print(
            f"status={report['status']} files={report['checked_files']} "
            f"skills={report['catalog']['skills']} "
            f"hooks={report['catalog']['hook_boilerplates']}"
        )
        for item in report["issues"]:
            print(
                f"{item['path']}:{item['line']}: "
                f"{item['code']}: {item['message']}"
            )
    return 1 if report["issues"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
