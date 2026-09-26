#!/usr/bin/env bash
# Exercise check-no-adventure-content.sh against throwaway repositories. Needs
# nothing but git, and touches nothing outside a temporary directory.
#
#   bash scripts/test-check-no-adventure-content.sh

set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
CHECK="$HERE/check-no-adventure-content.sh"
WORK="$(mktemp -d)"
FAILURES=0
trap 'rm -rf "$WORK"' EXIT

check() {              # check <description> <expected> <actual>
  if [ "$2" = "$3" ]; then
    echo "  ok    $1"
  else
    echo "  FAIL  $1"
    echo "        expected: $2"
    echo "        actual:   $3"
    FAILURES=$((FAILURES + 1))
  fi
}

repo() {               # repo <name>: a fresh repository with one clean file
  REPO="$WORK/$1"
  git init -q "$REPO"
  echo "# readme" > "$REPO/README.md"
}

put() {                # put <path> [content]: write a text file and stage it
  mkdir -p "$(dirname "$REPO/$1")"
  printf '%s\n' "${2:-text}" > "$REPO/$1"
  git -C "$REPO" add -- "$1"
}

put_binary() {         # put_binary <path>: write a binary file and stage it
  mkdir -p "$(dirname "$REPO/$1")"
  printf '\211PNG\r\n\032\n\000\000\000\015IHDR' > "$REPO/$1"
  git -C "$REPO" add -- "$1"
}

run() {                # run: check the current repository; sets OUT and CODE
  OUT="$(cd "$REPO" && env -u GITHUB_ACTIONS bash "$CHECK" 2>&1)"
  CODE=$?
}

names() {              # names <path>: 1 if the output names the path as a finding
  printf '%s\n' "$OUT" | grep -Fq -- "FAIL  $1:" && echo 1 || echo 0
}

echo "a clean repository"
repo clean
put README.md
put tests/fixtures/PROVENANCE.md "Original content written for this project."
put tests/fixtures/opponent.json '{"name": "Training dummy"}'
run
check "passes" "0" "$CODE"

echo "adventure content paths"
repo paths
put content/scene.md
put adventures/intro.md
put scans/page-001.txt
put notes/chapter1.scan.txt
put docs/content.md
run
check "fails" "1" "$CODE"
check "names content/" "1" "$(names content/scene.md)"
check "names adventures/" "1" "$(names adventures/intro.md)"
check "names scans/" "1" "$(names scans/page-001.txt)"
check "names *.scan.*" "1" "$(names notes/chapter1.scan.txt)"
check "leaves a file merely called content alone" "0" "$(names docs/content.md)"

echo "binaries, images and documents"
repo binaries
put_binary data/blob.dat
put maps/cellar.svg '<svg xmlns="http://www.w3.org/2000/svg"/>'
put scans-look-alike/PAGE.PDF
run
check "fails" "1" "$CODE"
check "names a binary file" "1" "$(names data/blob.dat)"
check "names an image by extension, even as text" "1" "$(names maps/cellar.svg)"
check "matches extensions in any case" "1" "$(names scans-look-alike/PAGE.PDF)"

echo "the allowlist"
repo allowlist
put_binary client/public/icon.png
put scripts/adventure-content-allowlist.txt "client/public/icon.png  # original app icon"
run
check "a justified entry passes" "0" "$CODE"
put scripts/adventure-content-allowlist.txt "client/public/icon.png"
run
check "an entry without justification fails" "1" "$CODE"
check "names the allowlist" "1" "$(names scripts/adventure-content-allowlist.txt)"

echo "fixture provenance"
repo fixtures
put tests/fixtures/opponent.json
put tools/ingest/tests/fixtures/pages/one.txt
put tools/ingest/tests/fixtures/PROVENANCE.md "SRD 5.1, CC-BY-4.0."
run
check "fails" "1" "$CODE"
check "names the fixtures directory without provenance" "1" "$(names tests/fixtures)"
check "a nested fixtures directory with provenance passes" "0" "$(names tools/ingest/tests/fixtures)"

echo "outside a git checkout"
mkdir -p "$WORK/plain"
OUT="$(cd "$WORK/plain" && bash "$CHECK" 2>&1)"; CODE=$?
check "fails loudly" "2" "$CODE"

echo
if [ "$FAILURES" -eq 0 ]; then
  echo "all checks passed"
else
  echo "$FAILURES check(s) failed"
  exit 1
fi
