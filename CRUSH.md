# CRUSH Handbook

## Project Overview
- Flask 3 backend serving a single-page uploader stored in `static/index.html`.
- Persisted uploads live under `transfer/` (auto-created) with short links tracked in `slugs.json`.
- Frontend bundle (CSS/JS) in `assets/` powers the SPA referenced by `static/index.html`.

## Repository Layout
- `app.py`: Flask app, API routes, slug handling, remote download logic.
- `static/index.html`: SPA with drag & drop uploads, progress display, and short-link copy.
- `assets/`: Generated asset bundle (no sources here).
- `start.sh`: Production launcher wrapping Gunicorn and folder prep.
- `requirements.txt`: Python deps (Flask, Flask-CORS, Werkzeug).
- `README.md`, `TESTING.md`, `projekt.md`: Spec + manual QA notes.
- Delivery environment assumes `/var/www/copy/` but use `BASE_DIR` discovery for portability.

## Environment Setup
```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt gunicorn
```
- `start.sh` exits early if `.venv/bin/gunicorn` is missing.
- Python 3.11+ recommended (see README).

## Running Locally
```bash
python app.py  # serves on http://localhost:8089 with debug on
```
- Ensure `transfer/` exists or let the app create it via `ensure_upload_dir()`.
- `app.py` seeds logging via the `file-uploader` logger.

## Production Operations
```bash
./start.sh
```
- Honors env vars: `WORKERS` (default 4), `TIMEOUT` (default 180), `GRACEFUL_TIMEOUT` (default 180), `SENDFILE` (defaults to `--no-sendfile`).
- Script ensures `transfer/` exists and applies `chmod 755` when directory owned by the caller.
- Example configs: `nginx.conf.example`, `file-uploader.service` use port `8089` and call `start.sh`.

## Testing & QA
- Manual test matrix documented in `TESTING.md` (covers API endpoints, download URLs, slug usage).
- No automated test suite; leverage Flask test client for regression coverage when adding features (`app.test_client()`).

## Backend Conventions (`app.py`)
- Path safety enforced via `validated_real_path()`; always reuse it for new file operations.
- Free-space guard: call `ensure_space_available(bytes_needed)` before writing data; remote downloads stream incrementally and re-check space per chunk.
- Short links generated via `generate_slug()` + `slugs.json`; delete entries with `delete_slug()` when removing files.
- All API responses return JSON on error; keep German message style for consistency.
- Remote downloads allow only http(s); customize headers in `download_remote_file()` if needed.

## Frontend Notes (`static/index.html`)
- Pure vanilla JS; no bundler. Event delegation handles action buttons (`data-download`, `data-delete`, `data-copy`).
- `loadFiles()` expects `short_link` in payload; backend falls back to `/s/<slug>` when `_external` URL generation is unavailable.
- Storage info UI polls `/api/storage`; update both `loadFiles()` and `loadStorage()` after mutating uploads.

## Storage & Slugs
- Uploads stored as sanitized filenames via `werkzeug.utils.secure_filename`.
- `slugs.json` sits beside `app.py`; ensure write permissions when deploying.
- Download/delete endpoints rely on sanitized paths; never bypass `validated_real_path()` in new routes.

## Gotchas & Tips
- Missing or unreadable `slugs.json` is tolerated (loader returns `{}`) but recreating the file drops existing slugs.
- If running behind proxies, ensure `APPLICATION_ROOT` or `PREFERRED_URL_SCHEME` adjustments for external URLs.
- `storage_info()` uses `shutil.disk_usage(UPLOAD_FOLDER)`; on network mounts, ensure permissions allow stat calls.
- Keep frontend and backend message language aligned (currently German).
