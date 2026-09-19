#!/usr/bin/env bash
# Set the size and iteration fields of issues that already exist on the board.
# Use when an issue was created but its fields were not set — for instance
# because a script failed halfway.
#
#   bash scripts/set-issue-fields.sh 13 S Backlog
#
# Status is never set here: it is the maintainer's judgement, not a fact.

set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE/.."

if [ "$#" -ne 3 ]; then
  echo "usage: bash scripts/$(basename "$0") <issue number> <size> <iteration>"
  echo "  e.g. bash scripts/$(basename "$0") 13 S Backlog"
  exit 1
fi

# shellcheck source=gh-board.sh
source "$HERE/gh-board.sh"
board_connect

set_issue_fields "$1" "$2" "$3"
