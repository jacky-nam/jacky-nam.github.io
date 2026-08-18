#!/usr/bin/env bash
# Renders deck/index.html to ReferenceDeck.pdf at the repo root.
# Requires a headless Chrome/Chromium binary. Set CHROME_BIN to override
# auto-detection (e.g. a "Chrome for Testing" build installed via:
#   npx puppeteer browsers install chrome
# ).
set -euo pipefail

DECK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$DECK_DIR/.." && pwd)"
OUT="$REPO_ROOT/ReferenceDeck.pdf"

find_chrome() {
  if [[ -n "${CHROME_BIN:-}" ]]; then
    echo "$CHROME_BIN"
    return
  fi
  local candidates=(
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    "/Applications/Chromium.app/Contents/MacOS/Chromium"
  )
  for c in "${candidates[@]}"; do
    if [[ -x "$c" ]]; then
      echo "$c"
      return
    fi
  done
  # Fall back to a puppeteer-managed "Chrome for Testing" build.
  local pup
  pup="$(find "$HOME/.cache/puppeteer/chrome" -maxdepth 2 -type d -name 'mac_arm-*' -o -maxdepth 2 -type d -name 'mac-*' 2>/dev/null | sort -V | tail -1)"
  if [[ -n "$pup" ]]; then
    local bin
    bin="$(find "$pup" -name 'Google Chrome for Testing' -type f 2>/dev/null | head -1)"
    [[ -n "$bin" ]] && echo "$bin" && return
    bin="$(find "$pup" -name 'chrome' -type f 2>/dev/null | head -1)"
    [[ -n "$bin" ]] && echo "$bin" && return
  fi
  echo "ERROR: no Chrome/Chromium binary found. Install one, e.g.:" >&2
  echo "  npx puppeteer browsers install chrome" >&2
  exit 1
}

CHROME="$(find_chrome)"

TMP_PDF="$(mktemp -t referencedeck-XXXXXX).pdf"
trap 'rm -f "$TMP_PDF"' EXIT

"$CHROME" \
  --headless=new \
  --disable-gpu \
  --no-pdf-header-footer \
  --no-sandbox \
  --print-to-pdf="$TMP_PDF" \
  --print-to-pdf-no-header \
  "file://$DECK_DIR/index.html"

# Strip identifying document metadata (title/author/producer/creator) that
# Chrome's PDF writer sets by default, and clean up unused named destinations.
python3 "$DECK_DIR/set_metadata.py" "$TMP_PDF" "$OUT"

echo "Wrote $OUT"
