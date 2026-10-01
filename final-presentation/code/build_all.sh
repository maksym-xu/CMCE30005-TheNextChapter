#!/usr/bin/env bash
set -euo pipefail

PACKAGE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_ROOT="${RUNTIME_ROOT:-$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies}"
RUNTIME_PYTHON="${RUNTIME_PYTHON:-$RUNTIME_ROOT/python/bin/python3}"
RUNTIME_NODE="${RUNTIME_NODE:-$RUNTIME_ROOT/node/bin/node}"
export RUNTIME_NODE_MODULES="${RUNTIME_NODE_MODULES:-$RUNTIME_ROOT/node/node_modules}"
export RUNTIME_PYTHON
export PRESENTATIONS_SKILL_DIR="${PRESENTATIONS_SKILL_DIR:-$HOME/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.12148/skills/presentations}"
DOCUMENTS_SKILL_DIR="${DOCUMENTS_SKILL_DIR:-$HOME/.codex/plugins/cache/openai-primary-runtime/documents/26.909.12148/skills/documents}"
REBUILD_ID="$(date +%Y%m%d-%H%M%S)"
REBUILD_DIR="$PACKAGE_ROOT/working/rebuild-$REBUILD_ID"
mkdir -p "$REBUILD_DIR" "$PACKAGE_ROOT/qa"
MODE="${1:---artifacts-only}"
if [[ "$MODE" != "--artifacts-only" && "$MODE" != "--with-analysis" ]]; then
  printf 'Usage: bash code/build_all.sh [--artifacts-only|--with-analysis]\n' >&2
  exit 2
fi
if [[ -z "${FONTCONFIG_FILE:-}" && -f "$PACKAGE_ROOT/qa/fonts.conf" ]]; then
  export FONTCONFIG_FILE="$PACKAGE_ROOT/qa/fonts.conf"
fi
export FINAL_PPTX="$PACKAGE_ROOT/deliverables/TheNextChapter_Final_Rebuilt_$REBUILD_ID.pptx"
export FINAL_DOCX="$PACKAGE_ROOT/deliverables/TheNextChapter_Final_Script_Rebuilt_$REBUILD_ID.docx"

test -x "$RUNTIME_PYTHON"
test -x "$RUNTIME_NODE"
test -d "$RUNTIME_NODE_MODULES/@oai/artifact-tool"
if [[ ! -e "$PACKAGE_ROOT/code/node_modules" ]]; then
  ln -s "$RUNTIME_NODE_MODULES" "$PACKAGE_ROOT/code/node_modules"
fi

if [[ "$MODE" == "--with-analysis" ]]; then
  bash "$PACKAGE_ROOT/analysis/run.sh"
  (cd "$PACKAGE_ROOT/analysis" && Rscript scripts/matched_rf_comparison.R > logs/matched_rf_comparison.log 2>&1)
  (cd "$PACKAGE_ROOT/analysis" && Rscript scripts/association_stability.R > logs/association_stability.log 2>&1)
  (cd "$PACKAGE_ROOT/analysis" && "$RUNTIME_PYTHON" scripts/shortlisted_group_validation.py > logs/shortlisted_group_validation.log 2>&1)
  (cd "$PACKAGE_ROOT/analysis" && Rscript scripts/verify_shortlisted_group_validation.R > logs/verify_shortlisted_group_validation.log 2>&1)
fi
(cd "$PACKAGE_ROOT/analysis" && "$RUNTIME_PYTHON" scripts/check_publication.py)
"$RUNTIME_PYTHON" "$PACKAGE_ROOT/code/prepare_slide_data.py"
"$RUNTIME_PYTHON" "$PACKAGE_ROOT/code/build_script.py"
"$RUNTIME_NODE" "$PACKAGE_ROOT/code/build_deck.mjs"
"$RUNTIME_PYTHON" "$PACKAGE_ROOT/code/verify_deliverables.py" --pptx "$FINAL_PPTX"
"$RUNTIME_PYTHON" \
  "$DOCUMENTS_SKILL_DIR/render_docx.py" "$FINAL_DOCX" \
  --output_dir "$REBUILD_DIR/docx-render" --emit_pdf
"$RUNTIME_PYTHON" "$PACKAGE_ROOT/code/build_preview.py" "$PACKAGE_ROOT"
printf 'Rebuilt PowerPoint: %s\nRebuilt script: %s\n' "$FINAL_PPTX" "$FINAL_DOCX"
printf 'Inspect the new slide and Word renders before delivery. Preview files reflect this rebuild.\n'
