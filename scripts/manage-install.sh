#!/bin/bash
# Manage files recorded by claude-code-guide's install-state lifecycle.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

usage() {
  cat <<'USAGE'
Usage:
  bash scripts/manage-install.sh doctor --target <path> [--json]
  bash scripts/manage-install.sh repair --target <path> [--dry-run] [--json]
  bash scripts/manage-install.sh uninstall --target <path> [--dry-run] [--json]

Options are forwarded to scripts/install_state.py. Set CLAUDE_CONFIG_DIR to
inspect an installation that used a non-default Claude home.
USAGE
}

if [ "$#" -eq 0 ] || [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  usage
  exit 0
fi

case "$1" in
  doctor|repair|uninstall) ;;
  *)
    echo "ERROR: unsupported command '$1'" >&2
    usage >&2
    exit 2
    ;;
esac

exec python3 "$SCRIPT_DIR/install_state.py" "$@"
