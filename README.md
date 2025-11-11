# COPY

Einfache Flask-Anwendung zum Hochladen, Auflisten, Herunterladen, Teilen und Löschen von Dateien ohne Benutzerkonto. Frontend und Backend folgen der Projektspezifikation in `projekt.md`.

> **Kommunikation:** Bitte ausschließlich auf Deutsch antworten, wenn Fragen zu diesem Projekt gestellt oder Änderungen beschrieben werden.

## Funktionsumfang

- Drag & Drop Upload, Datei-Dialog (mobil: jedes Dateiformat) sowie Upload per URL inkl. Fortschrittsbalken.
- Kurzlinks, Download/Löschaktionen und Benachrichtigungen komplett im UI-Stil (keine Browser-Alerts).
- Grid/List-Ansicht samt eingeklappter Karten werden lokal im Browser gespeichert.
- FAB (`+`) dient als sekundäre Drop-Zone und enthält Quick-Actions für Datei-Dialog und URL-Downloads.
- Speicheranzeige basiert auf dem real belegten Platz im Ordner `transfer` plus freiem Speicher laut `shutil.disk_usage`.
- Manifest + Service Worker machen COPY installierbar und offline-fähig (PWA).

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
Die sichtbare Speicheranzeige berechnet: `Verbraucht = Summe aller Dateien unter transfer/`, `Gesamt = Verbraucht + von Flask gemeldeter freier Speicher`.

## Progressive Web App

- Manifest liegt erreichbar unter `/manifest.webmanifest`, Icons unter `/icons/...` (Flask liefert `static/` direkt unter `/` aus).
- Service Worker: `static/sw.js` (registriert beim Seitenstart).
- COPY lässt sich auf unterstützten Endgeräten installieren und cacht das Frontend offline.

Weitere Anpassungen (z. B. Styling) erfolgen über `static/index.html`. Für jeden Upload wird automatisch ein Kurzlink erzeugt und im Frontend angezeigt.

## Frontend/UX

- Alle Assets liegen in `static/`; das HTML wird ohne Build-Step direkt bearbeitet.
- Grid/List-Ansicht, eingeklappte Karten und laufende Uploads werden per `localStorage` gespeichert.
- Drag & Drop, FAB-Dropzone, URL-Uploads und Benachrichtigungen laufen komplett ohne Browser-Dialoge.
- Fortschrittsanzeigen (Upload, URL, Speicherplatz) teilen sich das graue Balkendesign aus `static/index.html`.

## API-Endpunkte

- `GET /api/files` – Liste der Dateien mit Metadaten inkl. Kurzlink (`short_link`)
- `POST /api/upload` – Multipart Upload (`file` Feld)
- `POST /api/download-url` – Lädt eine Datei anhand einer URL herunter
- `GET /api/storage` – Liefert Gesamt-, Belegt- und freien Speicherplatz
- `GET /download/<filename>` – Datei herunterladen
- `GET /s/<slug>` – Kurzlink, der direkt auf den Download zeigt
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
