#!/bin/bash
set -euo pipefail
cd /var/www/projects/copy

echo "[$(date)] Deploy gestartet" >> /var/log/copy/deploy.log

# Git-Remote-URL aus Config lesen (Token schon hinterlegt)
git pull origin main >> /var/log/copy/deploy.log 2>&1

# Dependencies aktualisieren falls requirements.txt geändert
.venv/bin/pip install -q gunicorn -r requirements.txt >> /var/log/copy/deploy.log 2>&1

# Service neu starten
rc-service copy restart >> /var/log/copy/deploy.log 2>&1

echo "[$(date)] Deploy abgeschlossen" >> /var/log/copy/deploy.log
