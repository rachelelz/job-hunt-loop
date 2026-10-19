#!/usr/bin/env bash
# Render an HTML file to PDF with headless Chrome or Chromium, report the page count,
# and write low-resolution preview PNGs next to the PDF when pdftoppm is installed.
#
# Usage:
#   bash scripts/render_pdf.sh <input.html> <output.pdf> [max_pages]
#   bash scripts/render_pdf.sh cv.html "Firstname Lastname CV.pdf" 2
#   bash scripts/render_pdf.sh cover-letter.html "Cover letter.pdf" 1
#
# Environment:
#   CHROME_BIN     path or command name of the browser to use (otherwise auto-detected)
#   CHROME_FLAGS   extra flags, e.g. "--no-sandbox" inside containers or as root
#   NO_PREVIEW=1   skip the preview PNGs
#
# Output files: <output.pdf>, and <output>-preview-N.png (one per page) unless NO_PREVIEW is set.
# Needs Google Chrome, Chromium or Brave. macOS and Linux.

set -euo pipefail

if [ $# -lt 2 ]; then
  echo "usage: bash scripts/render_pdf.sh <input.html> <output.pdf> [max_pages]" >&2
  exit 2
fi

IN="$1"
OUT="$2"
MAX_PAGES="${3:-2}"
case "$MAX_PAGES" in
  ''|*[!0-9]*|0) echo "max_pages must be a positive integer" >&2; exit 2 ;;
esac
command -v python3 >/dev/null 2>&1 || { echo "python3 is required" >&2; exit 1; }
if [ "$(python3 -c 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).resolve() == pathlib.Path(sys.argv[2]).resolve())' "$IN" "$OUT")" = True ]; then
  echo "input and output must be different files" >&2
  exit 2
fi

if [ ! -f "$IN" ]; then
  echo "input not found: $IN" >&2
  exit 1
fi

find_chrome() {
  if [ -n "${CHROME_BIN:-}" ]; then
    if [ -x "$CHROME_BIN" ]; then echo "$CHROME_BIN"; return 0; fi
    if command -v -- "$CHROME_BIN" >/dev/null 2>&1; then command -v -- "$CHROME_BIN"; return 0; fi
    echo "CHROME_BIN is set to '$CHROME_BIN' but it is not an executable" >&2
    return 1
  fi
  local candidates=(
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    "/Applications/Chromium.app/Contents/MacOS/Chromium"
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
    "$HOME/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
  )
  local c
  for c in "${candidates[@]}"; do
    if [ -x "$c" ]; then echo "$c"; return 0; fi
  done
  for c in google-chrome google-chrome-stable chromium chromium-browser brave-browser; do
    if command -v -- "$c" >/dev/null 2>&1; then command -v -- "$c"; return 0; fi
  done
  return 1
}

CHROME="$(find_chrome)" || { echo "No Chrome or Chromium found. Install one or set CHROME_BIN=/path/to/chrome" >&2; exit 1; }

# file:// URL with proper escaping, so '#', '%', '?' and spaces in the path all work
URL="$(python3 -c 'import pathlib, sys; print(pathlib.Path(sys.argv[1]).resolve().as_uri())' "$IN")" \
  || { echo "could not build a file URL for $IN (is python3 installed?)" >&2; exit 1; }

# Isolate the render from any running browser and preserve an existing PDF on failure.
OUT="$(python3 -c 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).absolute())' "$OUT")"
mkdir -p -- "$(dirname -- "$OUT")"
RENDER_DIR="$(mktemp -d "$(dirname -- "$OUT")/.job-hunt-render.XXXXXX")"
ERRLOG="$RENDER_DIR/chrome.log"
TEMP_PDF="$RENDER_DIR/render.pdf"
trap 'rm -rf -- "$RENDER_DIR"' EXIT

if command -v timeout >/dev/null 2>&1; then TMO="timeout 90"; elif command -v gtimeout >/dev/null 2>&1; then TMO="gtimeout 90"; else TMO=""; fi

# shellcheck disable=SC2086
if ! $TMO "$CHROME" --headless=new --user-data-dir="$RENDER_DIR/profile" --disable-background-networking --disable-extensions --disable-gpu --no-pdf-header-footer ${CHROME_FLAGS:-} --print-to-pdf="$TEMP_PDF" "$URL" >"$ERRLOG" 2>&1; then
  # older Chrome: plain --headless
  $TMO "$CHROME" --headless --user-data-dir="$RENDER_DIR/profile" --disable-background-networking --disable-extensions --disable-gpu --no-pdf-header-footer ${CHROME_FLAGS:-} --print-to-pdf="$TEMP_PDF" "$URL" >"$ERRLOG" 2>&1 \
    || { echo "Chrome failed to render $IN:" >&2; tail -n 5 -- "$ERRLOG" >&2; exit 1; }
fi

if [ ! -s "$TEMP_PDF" ]; then
  echo "render failed: $OUT was not written. Chrome said:" >&2
  tail -n 5 -- "$ERRLOG" >&2
  exit 1
fi

mv -f -- "$TEMP_PDF" "$OUT"

PAGES=""
if command -v pdfinfo >/dev/null 2>&1; then
  PAGES="$(pdfinfo "$OUT" 2>/dev/null | awk '/^Pages:/ {print $2}' || true)"
fi
if [ -z "$PAGES" ]; then
  PAGES="$(python3 - "$OUT" <<'PY' || true
import re, sys
data = open(sys.argv[1], "rb").read()
print(len(re.findall(rb"/Type\s*/Page[^s]", data)))
PY
)"
fi

echo "wrote $OUT${PAGES:+ ($PAGES page(s))}"
if [ -n "$PAGES" ] && [ "$PAGES" -gt "$MAX_PAGES" ] 2>/dev/null; then
  echo "warning: $PAGES pages, target is $MAX_PAGES. Trim before sending." >&2
fi

if [ -z "${NO_PREVIEW:-}" ] && command -v pdftoppm >/dev/null 2>&1; then
  PREVIEW="${OUT%.pdf}-preview"
  rm -f -- "$PREVIEW"-*.png
  if pdftoppm -png -r 60 "$OUT" "$PREVIEW" >/dev/null 2>&1; then
    echo "preview images: ${PREVIEW}-*.png (open them to check page breaks)"
  fi
fi
