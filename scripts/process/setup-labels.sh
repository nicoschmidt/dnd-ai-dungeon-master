#!/usr/bin/env bash
# Managed by ai-dev-process.
#
# Create or update the labels the process relies on. Safe to re-run: existing
# labels are updated in place, others are left alone.
#
#   bash scripts/process/setup-labels.sh
#   GH_REPO=owner/name bash scripts/process/setup-labels.sh

set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$(git -C "$HERE" rev-parse --show-toplevel)"

command -v gh >/dev/null || { echo "gh is not installed."; exit 1; }

# An empty array expands safely under `set -u` only in bash 4.4 and later;
# macOS ships bash 3.2, hence the ${x[@]+...} form below.
repo_args=()
if [ -n "${GH_REPO:-}" ]; then repo_args=(--repo "$GH_REPO"); fi

failed=0
while IFS='|' read -r name color description; do
  [ -n "$name" ] || continue
  if gh label create "$name" --color "$color" --description "$description" --force ${repo_args[@]+"${repo_args[@]}"} >/dev/null; then
    echo "label    $name"
  else
    echo "FAILED   $name"
    failed=1
  fi
done <<'LABELS'
idea|FBCA04|Captured in passing; refined before any work starts
process|5319E7|About the way of working; read by the retro
type:feature|0E8A16|A capability the application should have
type:bug|D73A4A|Something behaves differently from what it should
type:spike|1D76DB|A time-boxed investigation that answers a question
type:chore|C5DEF5|Tooling, dependencies, process upkeep
LABELS

exit "$failed"
