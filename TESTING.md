# Testing

| Test | Ergebnis |
|------|----------|
| GET /api/files (leer) | ✅ |
| POST /api/upload (Textdatei) | ✅ |
| GET /api/files (nach Upload) | ✅ |
| POST /api/download-url (lokaler Testserver) | ✅ |
| POST /api/download-url (Redirect-Kette) | ✅ |
| GET /api/files (nach URL-Download) | ✅ |
| GET /api/storage | ✅ |
| GET /download/<filename> | ✅ |
| DELETE /api/files/<filename> | ✅ |
| GET /api/files (nach Löschen) | ✅ |

Tests wurden mit dem Flask-Test-Client (siehe `python3` Skript im Verlauf) durchgeführt. Drag & Drop, Progress-Bar und UI konnten in dieser Umgebung nicht mit Screenshots dokumentiert werden.
