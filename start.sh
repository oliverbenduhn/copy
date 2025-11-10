#!/usr/bin/env bash
# Startskript für Produktion mit Gunicorn
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

if [[ ! -d transfer ]]; then
  mkdir -p transfer
fi

if [[ -O transfer ]]; then
  chmod 755 transfer
fi

if [[ ! -x "$ROOT_DIR/.venv/bin/gunicorn" ]]; then
  echo "Lokales Virtualenv nicht gefunden. Bitte einmal ausführen:" >&2
  echo "  python3 -m venv .venv && .venv/bin/pip install -r requirements.txt gunicorn" >&2
  exit 1
fi

SENDFILE_FLAG=""
case "${SENDFILE:-False}" in
  [Tt]rue|1|yes|on)
    SENDFILE_FLAG="--sendfile"
    ;;
  *)
    SENDFILE_FLAG="--no-sendfile"
    ;;
esac

exec "$ROOT_DIR/.venv/bin/gunicorn" \
  --bind 0.0.0.0:8089 \
  --workers "${WORKERS:-4}" \
  --timeout "${TIMEOUT:-180}" \
  --graceful-timeout "${GRACEFUL_TIMEOUT:-180}" \
  $SENDFILE_FLAG \
  app:app
