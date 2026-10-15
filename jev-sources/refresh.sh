#!/bin/bash
# Refresh the Jev source library, then rebuild the section index.
#   bash refresh.sh --fetch   download every page in TypeSafe's docs sitemap and llms.txt, the cookbook list and typesafe.ai's blog (run this first)
#   bash refresh.sh           rebuild the index, then run the change check (downloads pages TypeSafe changed or added)
# Pages go to $JEV_SOURCES_DATA (default ~/.claude/jev-sources-data), never into the repo.
# Installs model2vec with pip if it's missing, for routing by meaning; JEV_SEMANTIC=off skips that.
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
if [ "${JEV_SEMANTIC:-}" != "off" ] && ! python3 -c "import model2vec" 2>/dev/null; then
  echo "installing model2vec for routing by meaning (once; JEV_SEMANTIC=off skips this)"
  python3 -m pip install --user --quiet model2vec || echo "model2vec install failed; routing stays keyword-only"
fi
# Local privacy check on saved blog posts: only where the checker and the owner's private config exist.
CHECKER="${JEV_PRIVATE_CHECKER:-$HERE/../scripts/private_text_check.py}"
PRIVATE_CFG="${JEV_PRIVATE_CONFIG:-$HOME/.claude/jevaluate-library/private-sources.json}"
if [ -f "$CHECKER" ] && [ -f "$PRIVATE_CFG" ] && [ -d "$DATA/blog" ]; then
  blog_files=()
  for f in "$DATA"/blog/*.txt "$DATA"/blog/*.md; do [ -e "$f" ] && blog_files+=("$f"); done
  rc=0
  if [ "${#blog_files[@]}" -gt 0 ]; then
    hits="$(JEV_PRIVATE_CONFIG="$PRIVATE_CFG" python3 "$CHECKER" "${blog_files[@]}")" || rc=$?
  else
    hits=""
  fi
  [ -n "$hits" ] && echo "$hits"
  if [ "$rc" -ne 0 ]; then
    if [ -n "$hits" ]; then
      echo "the privacy check refused the blog files listed above; they are not indexed"
    else
      echo "the privacy check failed (see the error above); no blog file will be indexed"
    fi
  fi
fi
python3 "$HERE/scripts/build_index.py"
python3 "$HERE/scripts/route_check.py" || true
python3 "$HERE/scripts/check_new.py" >/dev/null || true  # downloads pages TypeSafe changed or added since the last save, and appends a notice for the reminder hook to show
