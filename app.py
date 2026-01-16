"""Flask basierter Datei-Uploader gemäß projektspezifikation."""

from __future__ import annotations

import datetime as dt
import json
import logging
import os
import secrets
import shutil
import string
import time
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from flask import Flask, jsonify, request, send_from_directory, url_for
from flask_cors import CORS
from werkzeug.http import parse_options_header
from werkzeug.utils import secure_filename

# Projektweite Konstanten definieren Upload-Pfad.
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "transfer"
SLUG_FILE = BASE_DIR / "slugs.json"
ALLOWED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.zip', '.doc', '.docx', '.txt', '.csv', '.xlsx'}
MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500 MB
app = Flask(__name__, static_folder="static", static_url_path="")
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
CORS(app)

logger = logging.getLogger("file-uploader")
logging.basicConfig(level=logging.INFO)


def allowed_file(filename: str) -> bool:
    """Check if the file extension is allowed."""
    return '.' in filename and \
           os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS


def ensure_upload_dir() -> None:
    """Create upload directory when it is missing."""
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)


def format_size(num_bytes: int) -> str:
    """Convert bytes to a human readable string."""
    if num_bytes >= 1024 * 1024:
        return f"{num_bytes / (1024 * 1024):.1f} MB"
    if num_bytes >= 1024:
        return f"{num_bytes / 1024:.1f} KB"
    return f"{num_bytes} B"


def list_upload_files() -> List[dict]:
    """Collect metadata for each file in the upload folder."""
    ensure_upload_dir()
    entries = []
    for entry in sorted(UPLOAD_FOLDER.iterdir()):
        if entry.is_file():
            stats = entry.stat()
            modified_ts = int(stats.st_mtime)
            modified_iso = dt.datetime.fromtimestamp(modified_ts).isoformat()
            entries.append(
                {
                    "name": entry.name,
                    "size": stats.st_size,
                    "size_formatted": format_size(stats.st_size),
                    "modified": modified_iso,
                    "modified_timestamp": modified_ts,
                }
            )
    return entries


def storage_info() -> dict:
    """Return disk usage stats for the upload directory."""
    ensure_upload_dir()
    usage = shutil.disk_usage(UPLOAD_FOLDER)
    return {
        "total": usage.total,
        "total_formatted": format_size(usage.total),
        "used": usage.used,
        "used_formatted": format_size(usage.used),
        "free": usage.free,
        "free_formatted": format_size(usage.free),
    }


def load_slugs() -> Dict[str, str]:
    if SLUG_FILE.exists():
        try:
            return json.loads(SLUG_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def save_slugs(mapping: Dict[str, str]) -> None:
    SLUG_FILE.write_text(
        json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def generate_slug(length: int = 5) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def get_or_create_slug(filename: str) -> str:
    slugs = load_slugs()
    for slug, mapped in slugs.items():
        if mapped == filename:
            return slug
    slug = generate_slug()
    while slug in slugs:
        slug = generate_slug()
    slugs[slug] = filename
    save_slugs(slugs)
    return slug


def delete_slug(filename: str) -> None:
    slugs = load_slugs()
    updated = {slug: name for slug, name in slugs.items() if name != filename}
    if len(updated) != len(slugs):
        save_slugs(updated)


def get_filename_for_slug(slug: str) -> str | None:
    slugs = load_slugs()
    return slugs.get(slug)


def ensure_space_available(required: int | None) -> None:
    """Raise ValueError when not enough free space is available."""
    if required is None:
        return
    free = storage_info()["free"]
    if required > free:
        raise ValueError("Nicht genug Speicherplatz verfügbar")


def get_filestorage_size(file_storage) -> int | None:
    """Best-effort ermitteln der Dateigröße eines Uploads."""
    stream = getattr(file_storage, "stream", None)
    if stream is None:
        return file_storage.content_length
    size = file_storage.content_length
    try:
        current_pos = stream.tell()
        stream.seek(0, os.SEEK_END)
        size = stream.tell()
    except (OSError, AttributeError):
        return size
    finally:
        try:
            stream.seek(current_pos)
        except Exception:
            pass
    return size


def validated_real_path(filename: str) -> Path:
    """Return safe absolute path for filename inside UPLOAD_FOLDER."""
    candidate = (UPLOAD_FOLDER / filename).resolve()
    upload_root = UPLOAD_FOLDER.resolve()
    if not str(candidate).startswith(str(upload_root)):
        raise PermissionError("Ungültiger Pfad außerhalb des Upload-Verzeichnisses")
    return candidate


def derive_filename_from_headers(
    url: str, headers: dict
) -> Tuple[str, str | None]:
    """Ermittle Dateiname und Content-Type auf Basis der Header."""
    filename = ""
    content_type = headers.get("Content-Type")

    disposition = headers.get("Content-Disposition")
    if disposition:
        _, params = parse_options_header(disposition)
        filename = params.get("filename") or params.get("filename*") or ""

    if not filename:
        path_name = Path(urlparse(url).path).name
        filename = path_name or f"download_{int(time.time())}"

    filename = secure_filename(filename)
    if not filename:
        filename = f"download_{int(time.time())}"
    return filename, content_type


def download_remote_file(url: str) -> str:
    """Lade eine Datei über HTTP/S herunter und speichere sie im Upload-Ordner."""
    if not url.lower().startswith(("http://", "https://")):
        raise ValueError("Nur HTTP/HTTPS URLs sind erlaubt")

    request_headers = {
        "User-Agent": "COPY-Uploader/1.0",
        "Accept": "*/*",
    }
    req = Request(url, headers=request_headers)

    destination = None
    try:
        with urlopen(req, timeout=60) as response:  # nosec - urllib handles http/https
            final_url = response.geturl()
            headers = dict(response.headers)
            filename, _ = derive_filename_from_headers(final_url, headers)
            if not allowed_file(filename):
                raise ValueError("Dateityp nicht erlaubt")
            destination = validated_real_path(filename)
            content_length = headers.get("Content-Length")
            if content_length and content_length.isdigit():
                ensure_space_available(int(content_length))

            ensure_upload_dir()
            written = 0
            with open(destination, "wb") as target:
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    written += len(chunk)
                    if written > MAX_CONTENT_LENGTH:
                        raise ValueError("Download überschreitet maximale Größe")
                    ensure_space_available(written)
                    target.write(chunk)

            return filename
    except ValueError:
        if destination and destination.exists():
            destination.unlink()
        raise
    except (HTTPError, URLError) as exc:  # pragma: no cover
        if destination and destination.exists():
            destination.unlink()
        raise RuntimeError("Fehler beim Herunterladen der Datei") from exc


@app.route("/api/files", methods=["GET"])
def get_files():
    """Return metadata for all uploaded files."""
    try:
        files = list_upload_files()
        for entry in files:
            try:
                slug = get_or_create_slug(entry["name"])
            except Exception as exc:
                logger.warning("Kurzlink konnte nicht erzeugt werden: %s", exc)
                entry["short_code"] = None
                entry["short_link"] = None
                continue

            entry["short_code"] = slug
            try:
                entry["short_link"] = url_for(
                    "resolve_short_link", slug=slug, _external=True
                )
            except RuntimeError:
                entry["short_link"] = f"/s/{slug}"
        return jsonify(files)
    except Exception as exc:  # pragma: no cover - logged for operations
        logger.exception("Fehler beim Lesen der Dateien: %s", exc)
        return jsonify({"error": "Fehler beim Lesen der Dateien"}), 500


@app.route("/api/upload", methods=["POST"])
def upload_file():
    """Handle incoming file upload."""
    ensure_upload_dir()

    if "file" not in request.files:
        return jsonify({"error": "Keine Datei im Request gefunden"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Kein Dateiname übermittelt"}), 400

    try:
        ensure_space_available(get_filestorage_size(file))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    secure_name = secure_filename(file.filename)
    if not secure_name or not allowed_file(secure_name):
        return jsonify({"error": "Ungültiger Dateiname oder Dateityp nicht erlaubt"}), 400

    destination = UPLOAD_FOLDER / secure_name
    try:
        file.save(destination)
        logger.info("Datei %s hochgeladen", secure_name)
        return (
            jsonify(
                {
                    "success": True,
                    "filename": secure_name,
                    "message": "Datei erfolgreich hochgeladen",
                }
            ),
            200,
        )
    except Exception as exc:  # pragma: no cover - runtime safety
        logger.exception("Fehler beim Speichern: %s", exc)
        return jsonify({"error": "Fehler beim Speichern der Datei"}), 500


@app.route("/download/<path:filename>", methods=["GET"])
def download(filename: str):
    """Send a file to the client as attachment."""
    try:
        file_path = validated_real_path(filename)
    except PermissionError:
        return jsonify({"error": "Ungültiger Pfad"}), 403

    if not file_path.exists():
        return jsonify({"error": "Datei nicht gefunden"}), 404

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        file_path.name,
        as_attachment=True,
    )


@app.route("/api/files/<path:filename>", methods=["DELETE"])
def delete_file(filename: str):
    """Delete the requested file when it resides in upload folder."""
    try:
        file_path = validated_real_path(filename)
    except PermissionError:
        return jsonify({"error": "Ungültiger Pfad"}), 403

    if not file_path.exists():
        return jsonify({"error": "Datei nicht gefunden"}), 404

    try:
        file_path.unlink()
        delete_slug(file_path.name)
        logger.info("Datei %s gelöscht", file_path.name)
        return jsonify({"success": True, "message": "Datei gelöscht"})
    except Exception as exc:  # pragma: no cover
        logger.exception("Fehler beim Löschen: %s", exc)
        return jsonify({"error": "Fehler beim Löschen der Datei"}), 500


@app.route("/", methods=["GET"])
def serve_frontend():
    """Serve the single page application."""
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/download-url", methods=["POST"])
def download_from_url():
    """Lade eine entfernte Datei anhand einer URL herunter."""
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or "").strip()
    if not url:
        return jsonify({"error": "URL fehlt"}), 400

    try:
        filename = download_remote_file(url)
        return jsonify(
            {
                "success": True,
                "filename": filename,
                "message": "Datei erfolgreich heruntergeladen",
            }
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except RuntimeError as exc:
        logger.exception("Fehler beim URL-Download: %s", exc)
        return jsonify({"error": "Download fehlgeschlagen"}), 500


@app.route("/api/storage", methods=["GET"])
def get_storage():
    """Liefer Informationen zum verfügbaren Speicherplatz."""
    try:
        return jsonify(storage_info())
    except Exception as exc:  # pragma: no cover
        logger.exception("Fehler beim Lesen des Speicherplatzes: %s", exc)
        return jsonify({"error": "Speicherinfo nicht verfügbar"}), 500


@app.route("/s/<slug>", methods=["GET"])
def resolve_short_link(slug: str):
    """Leite Kurzlinks auf die eigentliche Datei weiter."""
    filename = get_filename_for_slug(slug)
    if not filename:
        return jsonify({"error": "Kurzlink unbekannt"}), 404

    try:
        file_path = validated_real_path(filename)
    except PermissionError:
        return jsonify({"error": "Ungültiger Pfad"}), 403

    if not file_path.exists():
        return jsonify({"error": "Datei nicht gefunden"}), 404

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        file_path.name,
        as_attachment=True,
    )


if __name__ == "__main__":
    ensure_upload_dir()
    app.run(host="0.0.0.0", port=8089, debug=True)
