#!/bin/bash
# Refresh the Jev source library, then rebuild the section index.
#   bash refresh.sh --fetch   download every page TypeSafe lists in llms.txt (run this first)
#   bash refresh.sh           rebuild the index from the pages already downloaded
# Pages go to $JEV_SOURCES_DATA (default ~/.claude/jev-sources-data), never into the repo.
# Optional: set JEV_VAULT to a folder holding docs/, cookbooks/ and patterns/ copies to keep in step with it.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA="${JEV_SOURCES_DATA:-$HOME/.claude/jev-sources-data}"
mkdir -p "$DATA/docs" "$DATA/cookbooks" "$DATA/patterns"
copy() {  # copy src/{docs,cookbooks,patterns}/*.md into dst, skipping extracts and raw copies
  for kind in docs cookbooks patterns; do
    [ -d "$1/$kind" ] || continue
    mkdir -p "$2/$kind"
    for f in "$1/$kind"/*.md; do
      [ -e "$f" ] || continue
      case "$(basename "$f")" in extract.md|*.raw.md) ;; *) cp "$f" "$2/$kind/";; esac
    done
  done
}
if [ "${1:-}" = "--fetch" ]; then
  python3 "$HERE/scripts/fetch.py" || echo "the fetch reported problems (above); building the index from what was downloaded"
  [ -n "${JEV_VAULT:-}" ] && copy "$DATA" "$JEV_VAULT"
elif [ -n "${JEV_VAULT:-}" ]; then
  copy "$JEV_VAULT" "$DATA"
fi
python3 "$HERE/scripts/build_index.py"
python3 "$HERE/scripts/check_new.py" >/dev/null || true  # clears the notice once the library matches
