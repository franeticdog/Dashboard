#!/bin/bash
# Deja listo el entorno del editor-video en las sesiones de Claude Code en la nube:
# Python con Whisper y MediaPipe, HyperFrames con su navegador, modelos y tipografías.
# kit.py instalar es idempotente: lo que ya está instalado (o cacheado) se salta.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR/videos"
mkdir -p brutos finales
PY=python3.12
command -v "$PY" >/dev/null || PY=python3
"$PY" "$CLAUDE_PROJECT_DIR/.claude/skills/editor-video/motor/herramientas/kit.py" instalar >&2
