#!/usr/bin/env bash
# Fail when the checkout looks like it holds adventure content (ADR-0003).
# Read-only. Checks the files git tracks in the repository around the current
# directory, and reports every finding rather than stopping at the first.
#
#   bash scripts/check-no-adventure-content.sh
#
# A heuristic, not a proof: it cannot tell whether a paragraph was copied out
# of a book. It is meant to stop scans, images and unexplained fixtures
# slipping in by accident. Three rules:
#
#   1. nothing under content/, adventures/ or scans/, and no *.scan.* file —
#      the same paths .gitignore keeps out
#   2. no binary file and no image or document file, unless it is listed in
#      scripts/adventure-content-allowlist.txt with a justification
#   3. every directory named `fixtures` carries a PROVENANCE.md

set -uo pipefail
root="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "Not inside a git checkout: $(pwd)"
  exit 2
}
cd "$root"

ALLOWLIST="scripts/adventure-content-allowlist.txt"
DOCUMENT_EXTENSIONS=" png jpg jpeg gif webp bmp tif tiff heic svg pdf epub psd docx odt zip "
FINDINGS=0

finding() {            # finding <path> <reason>
  echo "  FAIL  $1: $2"
  if [ -n "${GITHUB_ACTIONS:-}" ]; then
    echo "::error file=$1::$2"
  fi
  FINDINGS=$((FINDINGS + 1))
}

# Allowlist entries, one path per line, comment and surrounding space removed.
allowed=""
if [ -f "$ALLOWLIST" ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    entry="$(printf '%s' "$line" | sed -e 's/#.*//' -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
    [ -n "$entry" ] || continue
    case "$line" in
      *"#"*) ;;
      *) finding "$ALLOWLIST" "entry '$entry' has no justification; add '# why'" ;;
    esac
    allowed="$allowed$entry"$'\n'
  done < "$ALLOWLIST"
fi

is_allowed() {
  printf '%s' "$allowed" | grep -Fxq -- "$1"
}

fixture_dirs=""

while IFS= read -r -d '' record; do
  info="${record%%$'\t'*}"
  path="${record#*$'\t'}"
  name="${path##*/}"

  # Rule 1: the paths that hold adventure material.
  case "$path" in
    content/*|adventures/*|scans/*)
      finding "$path" "adventure content path" ;;
  esac
  case "$name" in
    *.scan.*) finding "$path" "scan file" ;;
  esac

  # Rule 2: binaries, images and documents.
  if ! is_allowed "$path"; then
    ext=""
    case "$name" in
      *.*) ext="$(printf '%s' "${name##*.}" | tr '[:upper:]' '[:lower:]')" ;;
    esac
    if [ -n "$ext" ] && [ "${DOCUMENT_EXTENSIONS/ $ext /}" != "$DOCUMENT_EXTENSIONS" ]; then
      finding "$path" "image or document file (.$ext) not in $ALLOWLIST"
    elif [ "${info%% *}" = "i/-text" ]; then
      finding "$path" "binary file not in $ALLOWLIST"
    fi
  fi

  # Rule 3: remember every fixtures directory for the provenance check.
  case "/$path" in
    */fixtures/*)
      prefix="/$path"
      prefix="${prefix%%/fixtures/*}"
      prefix="${prefix#/}"
      fixture_dirs="$fixture_dirs${prefix:+$prefix/}fixtures"$'\n'
      ;;
  esac
done < <(git ls-files --eol -z)

while IFS= read -r dir; do
  [ -n "$dir" ] || continue
  if ! git ls-files --error-unmatch "$dir/PROVENANCE.md" >/dev/null 2>&1; then
    finding "$dir" "fixture directory without PROVENANCE.md"
  fi
done < <(printf '%s' "$fixture_dirs" | sort -u)

if [ "$FINDINGS" -eq 0 ]; then
  echo "no adventure content found"
else
  echo
  echo "$FINDINGS finding(s). See ADR-0003 and scripts/README.md."
  exit 1
fi
