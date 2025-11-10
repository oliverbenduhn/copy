# COPY

Einfache Flask-Anwendung zum Hochladen, Auflisten, Herunterladen und Löschen von Dateien ohne Benutzerkonto. Frontend und Backend folgen der Projektspezifikation in `projekt.md`.

## Installation

1. Python 3.11+ bereitstellen.
2. Virtuelle Umgebung erstellen und Abhängigkeiten installieren:
   ```bash
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt gunicorn
   ```

## Entwicklung starten

```bash
python app.py
```
* Läuft per Default auf `http://localhost:8089`.
* Flask Debug-Mode ist aktiv; für Produktion deaktivieren.

## Produktion mit Gunicorn

```bash
. ./start.sh
```
Das Skript nutzt `.venv/bin/gunicorn`. Für einen manuellen Start:
```bash
.venv/bin/gunicorn --bind 0.0.0.0:8089 --workers 4 app:app
```

## Konfiguration

| Einstellung | Ort | Beschreibung |
|-------------|-----|--------------|
| Upload-Pfad | `UPLOAD_FOLDER` in `app.py` | Zielverzeichnis der Dateien |
| Dateigröße  | (kein Limit serverseitig) | Limit wird nur durch verfügbaren Speicher bestimmt |

Uploads sowie URL-Downloads werden automatisch blockiert, wenn nicht genug freier Speicher vorhanden ist. Die UI zeigt den aktuell freien Speicherbereich an.

Weitere Anpassungen (z. B. Styling) erfolgen über `static/index.html`.

## API-Endpunkte

- `GET /api/files` – Liste der Dateien mit Metadaten
- `POST /api/upload` – Multipart Upload (`file` Feld)
- `POST /api/download-url` – Lädt eine Datei anhand einer URL herunter
- `GET /api/storage` – Liefert Gesamt-, Belegt- und freien Speicherplatz
- `GET /download/<filename>` – Datei herunterladen
- `DELETE /api/files/<filename>` – Datei löschen

## Testing

Manuelle Tests (siehe `TESTING.md`) decken Upload, Liste, Download und Löschung ab.

## Deployment-Hinweise

- Beispiel-Nginx-Config: `nginx.conf.example`
- Systemd-Service: `file-uploader.service`
- Start-Script: `start.sh`
- Standardpfad in den Beispielen: `/var/www/copy` (kann bei Bedarf angepasst werden)

### Systemd aktivieren

1. Service-Datei kopieren:
   ```bash
   sudo cp file-uploader.service /etc/systemd/system/file-uploader.service
   ```
2. Dienste neu laden und aktivieren:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now file-uploader
   ```
Der Service ruft intern `start.sh` auf und nutzt damit automatisch die virtuelle Umgebung (`.venv`).

Weitere Details siehe Projektspezifikation.
