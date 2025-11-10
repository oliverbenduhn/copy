# 📋 Projektspezifikation: Minimaler Datei-Uploader

## 🎯 Projektziel
Entwicklung einer einfachen Web-Anwendung zum Hochladen, Anzeigen, Herunterladen und Löschen von Dateien ohne Login-System.

---

## 📂 1. VERZEICHNISSTRUKTUR EINRICHTEN

### 1.1 Projektordner anlegen
```
/var/www/site-8081/
├── app.py                 # Flask Backend
├── requirements.txt       # Python Dependencies
├── static/
│   └── index.html        # Frontend (HTML/CSS/JS)
└── transfer/             # Upload-Ordner (muss existieren)
```

### 1.2 Upload-Ordner vorbereiten
- Ordner `/var/www/site-8081/transfer` erstellen
- Schreibrechte für Webserver setzen: `chmod 755 transfer`
- Prüfen: Webserver-User (z.B. `www-data`) muss Lese-/Schreibrechte haben

---

## 🔧 2. BACKEND ENTWICKELN (Flask/Python)

### 2.1 Dependencies installieren
**Datei:** `requirements.txt`
```
Flask==3.0.0
Flask-CORS==4.0.0
Werkzeug==3.0.1
```

**Installation:**
```bash
pip install -r requirements.txt
```

### 2.2 Backend-Funktionen implementieren

**Datei:** `app.py`

#### 2.2.1 Grundkonfiguration
```python
- Flask-App initialisieren
- CORS aktivieren (für lokale Tests)
- Upload-Ordner definieren: UPLOAD_FOLDER = '/var/www/site-8081/transfer'
- Max. Upload-Größe: 500 MB (MAX_CONTENT_LENGTH = 500 * 1024 * 1024)
- Erlaubte Dateitypen: Whitelist definieren
  ALLOWED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.zip', '.doc', '.docx', '.txt', '.csv', '.xlsx'}
```

#### 2.2.2 API-Endpunkt: Dateiliste abrufen
**Route:** `GET /api/files`

**Funktionalität:**
- Alle Dateien aus `/transfer` einlesen
- Für jede Datei folgende Infos sammeln:
  - Dateiname
  - Dateigröße in Bytes (dann in KB/MB umrechnen für Anzeige)
  - Änderungsdatum (Unix-Timestamp und ISO-Format)
- JSON-Array zurückgeben:
```json
[
  {
    "name": "dokument.pdf",
    "size": 2048576,
    "size_formatted": "2.0 MB",
    "modified": "2025-11-10T14:30:00",
    "modified_timestamp": 1699622400
  }
]
```

**Fehlerbehandlung:**
- Prüfen ob `/transfer` existiert
- Bei Fehler HTTP 500 mit Fehlermeldung

#### 2.2.3 API-Endpunkt: Datei hochladen
**Route:** `POST /api/upload`

**Funktionalität:**
- Multipart-Formular-Upload empfangen
- File-Objekt aus Request extrahieren (Key: `file`)
- Sicherheitsprüfungen:
  1. Prüfen ob Datei vorhanden: `if 'file' not in request.files`
  2. Prüfen ob Dateiname leer: `if file.filename == ''`
  3. Dateiendung validieren gegen Whitelist
  4. Dateinamen mit `secure_filename()` bereinigen (verhindert `../` Attacken)
- Datei speichern: `file.save(os.path.join(UPLOAD_FOLDER, secure_name))`
- Bei Erfolg: JSON mit `{"success": true, "filename": "..."}` zurückgeben
- Bei Fehler: HTTP 400/500 mit Fehlermeldung

**Beispiel Response:**
```json
{
  "success": true,
  "filename": "meine_datei.pdf",
  "message": "Datei erfolgreich hochgeladen"
}
```

#### 2.2.4 API-Endpunkt: Datei herunterladen
**Route:** `GET /download/<filename>`

**Funktionalität:**
- Dateinamen aus URL-Parameter extrahieren
- Mit `secure_filename()` bereinigen (Sicherheit!)
- Prüfen ob Datei in `/transfer` existiert
- Download mit `send_from_directory()` starten
  - Parameter: `as_attachment=True` (erzwingt Download statt Anzeige im Browser)
- Bei nicht-existierender Datei: HTTP 404

**Wichtig:** 
- NIEMALS direkt `filename` aus URL verwenden ohne Bereinigung!
- Verhindert Path Traversal: `/download/../../../etc/passwd`

#### 2.2.5 API-Endpunkt: Datei löschen
**Route:** `DELETE /api/files/<filename>`

**Funktionalität:**
- Dateinamen aus URL-Parameter extrahieren
- Mit `secure_filename()` bereinigen
- Vollständigen Pfad zusammenbauen
- Prüfen ob Datei existiert UND innerhalb von `/transfer` liegt
- Datei löschen: `os.remove(filepath)`
- Bei Erfolg: JSON `{"success": true, "message": "Datei gelöscht"}`
- Bei Fehler: HTTP 404 oder 500

**Sicherheitsprüfung:**
```python
# Verhindere Löschung außerhalb von /transfer
real_path = os.path.realpath(filepath)
if not real_path.startswith(os.path.realpath(UPLOAD_FOLDER)):
    return {"error": "Ungültiger Pfad"}, 403
```

#### 2.2.6 Static Files ausliefern
**Route:** `GET /`

**Funktionalität:**
- `index.html` aus `/static` ausliefern
- Flask's `send_from_directory()` nutzen

---

## 🎨 3. FRONTEND ENTWICKELN (HTML/CSS/JavaScript)

**Datei:** `static/index.html`

### 3.1 HTML-Struktur

#### 3.1.1 Upload-Bereich
```html
<div id="upload-zone">
  <!-- Drag & Drop Zone -->
  <div class="drop-zone">
    <p>Dateien hierher ziehen oder klicken zum Auswählen</p>
    <input type="file" id="file-input" multiple hidden>
  </div>
  
  <!-- Fortschrittsanzeige -->
  <div id="progress-container" style="display:none;">
    <progress id="upload-progress" value="0" max="100"></progress>
    <span id="progress-text">0%</span>
  </div>
</div>
```

#### 3.1.2 Dateiliste
```html
<div id="file-list">
  <h2>Hochgeladene Dateien</h2>
  <table id="files-table">
    <thead>
      <tr>
        <th>Dateiname</th>
        <th>Größe</th>
        <th>Geändert am</th>
        <th>Aktionen</th>
      </tr>
    </thead>
    <tbody id="files-tbody">
      <!-- Wird dynamisch gefüllt -->
    </tbody>
  </table>
</div>
```

### 3.2 JavaScript-Funktionen

#### 3.2.1 Dateiliste laden (beim Seitenaufruf)
```javascript
async function loadFiles() {
  // GET Request an /api/files
  // Response parsen
  // Tabelle leeren
  // Für jede Datei eine Zeile erstellen mit:
    - Dateiname (klickbar für Download)
    - Formatierte Größe
    - Formatiertes Datum
    - Download-Button
    - Löschen-Button
}
```

**Wichtig:** Funktion beim Laden der Seite aufrufen: `window.onload = loadFiles;`

#### 3.2.2 Drag & Drop Funktionalität
```javascript
// Event Listener für Drop-Zone
dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  // Visuelles Feedback: Zone highlighten
});

dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  const files = e.dataTransfer.files;
  uploadFiles(files);
});

// Klick auf Zone öffnet File-Input
dropZone.addEventListener('click', () => {
  fileInput.click();
});

fileInput.addEventListener('change', (e) => {
  uploadFiles(e.target.files);
});
```

#### 3.2.3 Upload-Funktion
```javascript
async function uploadFiles(files) {
  for (let file of files) {
    // FormData erstellen
    const formData = new FormData();
    formData.append('file', file);
    
    // Progress-Bar anzeigen
    // XMLHttpRequest nutzen (für Progress Events)
    const xhr = new XMLHttpRequest();
    
    xhr.upload.addEventListener('progress', (e) => {
      // Fortschritt berechnen: (e.loaded / e.total) * 100
      // Progress-Bar aktualisieren
    });
    
    xhr.addEventListener('load', () => {
      if (xhr.status === 200) {
        // Erfolg: Dateiliste neu laden
        loadFiles();
        // Progress-Bar verstecken
      } else {
        // Fehler anzeigen
      }
    });
    
    xhr.open('POST', '/api/upload');
    xhr.send(formData);
  }
}
```

#### 3.2.4 Download-Funktion
```javascript
function downloadFile(filename) {
  // Einfacher Link-Klick
  window.location.href = `/download/${encodeURIComponent(filename)}`;
}
```

**Alternative (eleganter):**
```javascript
async function downloadFile(filename) {
  const response = await fetch(`/download/${encodeURIComponent(filename)}`);
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  window.URL.revokeObjectURL(url);
}
```

#### 3.2.5 Löschen-Funktion
```javascript
async function deleteFile(filename) {
  // Sicherheitsabfrage
  if (!confirm(`Datei "${filename}" wirklich löschen?`)) {
    return;
  }
  
  // DELETE Request
  const response = await fetch(`/api/files/${encodeURIComponent(filename)}`, {
    method: 'DELETE'
  });
  
  if (response.ok) {
    // Erfolg: Liste neu laden
    loadFiles();
    // Optional: Erfolgsmeldung anzeigen
  } else {
    // Fehler anzeigen
    alert('Fehler beim Löschen der Datei');
  }
}
```

### 3.3 CSS-Styling

#### 3.3.1 Drop-Zone
- Gestrichelter Rahmen
- Zentrierter Text
- Hover-Effekt (z.B. Hintergrundfarbe ändern)
- Drag-over-Effekt (z.B. grüner Rahmen)

#### 3.3.2 Tabelle
- Zebra-Streifen (abwechselnde Zeilenfarben)
- Hover-Effekt auf Zeilen
- Responsive Design (auf Mobilgeräten lesbar)

#### 3.3.3 Buttons
- Download-Button: Blau/Primärfarbe
- Löschen-Button: Rot/Warnfarbe
- Hover-Effekte

#### 3.3.4 Progress-Bar
- Moderne Gestaltung
- Prozentanzeige daneben
- Während Upload sichtbar, danach ausblenden

---

## 🔒 4. SICHERHEIT IMPLEMENTIEREN

### 4.1 Path Traversal verhindern
- ✅ `werkzeug.utils.secure_filename()` für alle Dateinamen verwenden
- ✅ Bei Download/Delete: `os.path.realpath()` prüfen
- ✅ Niemals User-Input direkt in Dateipfade einbauen

### 4.2 Dateiendungen validieren
```python
ALLOWED_EXTENSIONS = {'.pdf', '.png', '.jpg', '.jpeg', '.zip', '.doc', '.docx', '.txt', '.csv', '.xlsx'}

def allowed_file(filename):
    return '.' in filename and \
           os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS
```

### 4.3 Upload-Größe limitieren
- Flask Config: `MAX_CONTENT_LENGTH = 500 * 1024 * 1024`  # 500 MB
- Frontend: Optional Client-seitige Validierung vor Upload

### 4.4 Keine Code-Ausführung
- ✅ Keine `.php`, `.py`, `.sh`, `.exe` Dateien erlauben
- ✅ Upload-Ordner NICHT im Web-Root (falls möglich)
- ✅ Falls doch: `.htaccess` oder Nginx-Config um Ausführung zu verhindern

**Beispiel .htaccess für `/transfer`:**
```apache
<FilesMatch ".*">
    Deny from all
</FilesMatch>
```

---

## 🚀 5. DEPLOYMENT VORBEREITEN

### 5.1 Gunicorn installieren (Produktions-Server)
```bash
pip install gunicorn
```

### 5.2 Startskript erstellen
**Datei:** `start.sh`
```bash
#!/bin/bash
cd /var/www/site-8081
gunicorn --bind 0.0.0.0:8081 --workers 4 app:app
```

**Rechte setzen:**
```bash
chmod +x start.sh
```

### 5.3 Nginx Reverse Proxy (optional)
**Datei:** `/etc/nginx/sites-available/file-uploader`
```nginx
server {
    listen 80;
    server_name deine-domain.de;
    
    client_max_body_size 500M;
    
    location / {
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 5.4 Systemd Service (Auto-Start)
**Datei:** `/etc/systemd/system/file-uploader.service`
```ini
[Unit]
Description=File Uploader Service
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/site-8081
ExecStart=/usr/bin/gunicorn --bind 0.0.0.0:8081 --workers 4 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

**Service aktivieren:**
```bash
systemctl enable file-uploader
systemctl start file-uploader
```

---

## ✅ 6. TESTING-CHECKLISTE

### 6.1 Funktionstests
- [ ] Upload einzelner Datei funktioniert
- [ ] Upload mehrerer Dateien nacheinander funktioniert
- [ ] Drag & Drop funktioniert
- [ ] Dateiliste wird korrekt angezeigt
- [ ] Download-Button startet Download
- [ ] Klick auf Dateiname startet Download
- [ ] Löschen-Button mit Bestätigung funktioniert
- [ ] Nach Upload/Delete: Liste aktualisiert sich automatisch
- [ ] Fortschrittsanzeige während Upload sichtbar

### 6.2 Sicherheitstests
- [ ] Upload von `.php` Datei wird abgelehnt
- [ ] Dateiname mit `../` wird bereinigt
- [ ] Download von `/download/../../../etc/passwd` schlägt fehl
- [ ] Löschen außerhalb von `/transfer` nicht möglich
- [ ] Dateien > 500 MB werden abgelehnt

### 6.3 Edge Cases
- [ ] Upload Datei mit Sonderzeichen im Namen (ä, ö, ü, ß, Leerzeichen)
- [ ] Upload Datei mit sehr langem Namen (> 255 Zeichen)
- [ ] Gleichzeitiger Upload von 10+ Dateien
- [ ] Leerer `/transfer` Ordner zeigt keine Fehler
- [ ] Wiederholter Upload derselben Datei (Überschreiben oder Fehler?)

---

## 📝 7. LIEFERUMFANG

### Was der Programmierer abgeben soll:

1. **Quellcode**
   - `app.py` (vollständig kommentiert)
   - `static/index.html` (vollständig kommentiert)
   - `requirements.txt`

2. **Dokumentation**
   - README.md mit:
     - Installationsanleitung
     - Start-Anleitung für Development (`python app.py`)
     - Start-Anleitung für Production (`gunicorn`)
     - Konfigurationsoptionen (Upload-Größe, erlaubte Dateien ändern)

3. **Deployment-Dateien**
   - `start.sh`
   - Beispiel Nginx-Config
   - Beispiel Systemd-Service

4. **Testing**
   - Liste durchgeführter Tests
   - Screenshots der funktionierenden Anwendung

---

## 🎯 AKZEPTANZKRITERIEN

Die Anwendung ist fertig, wenn:

✅ Ein nicht-technischer Benutzer kann:
  - Dateien per Drag & Drop hochladen
  - Hochgeladene Dateien sehen (mit Größe & Datum)
  - Dateien herunterladen
  - Dateien löschen

✅ Die Anwendung ist sicher:
  - Keine Path Traversal möglich
  - Keine Code-Ausführung möglich
  - Upload-Größe limitiert

✅ Die Anwendung läuft stabil:
  - Keine Abstürze bei normaler Nutzung
  - Fehler werden sauber behandelt
  - Logs für Debugging vorhanden

---

## 🆘 SUPPORT & FRAGEN

Bei Unklarheiten zu dieser Spezifikation:
1. Markiere unklare Punkte
2. Stelle spezifische Fragen
3. Schlage Alternativen vor (mit Begründung)

**Nicht eigenständig abweichen von:**
- Verzeichnisstruktur
- API-Endpunkt-Namen
- Sicherheitsanforderungen
