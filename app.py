"""
TresorHaus DocFlow
Ein Dokumentenkonverter für verschiedene Dateiformate zu Markdown mit Wiki.js Integration

Author: Joachim Mild
Created: 2025
Company: TresorHaus GmbH
"""

import os
import tempfile
import subprocess
import uuid
import shutil
from pathlib import Path
from flask import Flask, request, render_template_string, send_file, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
import zipfile
import io
import requests
from datetime import datetime
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

app = Flask(__name__, static_folder='static')
app.secret_key = os.urandom(24)

# Konfiguration
UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), 'doc_converter_uploads')
RESULT_FOLDER = os.path.join(tempfile.gettempdir(), 'doc_converter_results')
ALLOWED_EXTENSIONS = {
    'doc', 'docx', 'odt', 'rtf', 'tex', 'html', 'htm', 'epub',
    'ppt', 'pptx', 'odp',
    'rst', 'textile', 'wiki', 'dbk', 'xml', 'adoc', 'asciidoc', 'org'
}

# Wiki.js Konfiguration
WIKIJS_URL = os.getenv('WIKIJS_URL')
WIKIJS_TOKEN = os.getenv('WIKIJS_TOKEN')

# Format-Mapping für Pandoc
FORMAT_MAPPING = {
    'doc': 'docx',
    'docx': 'docx',
    'odt': 'odt',
    'rtf': 'rtf',
    'tex': 'latex',
    'html': 'html',
    'htm': 'html',
    'epub': 'epub',
    'ppt': 'pptx',
    'pptx': 'pptx',
    'odp': 'odp',
    'rst': 'rst',
    'textile': 'textile',
    'wiki': 'mediawiki',
    'dbk': 'docbook',
    'xml': 'docbook',
    'adoc': 'asciidoc',
    'asciidoc': 'asciidoc',
    'org': 'org'
}

# HTML-Templates
INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>TresorHaus DocFlow - Dokumentenkonverter</title>
    <link rel="icon" type="image/png" href="{{ url_for('static', filename='favicon.ico') }}">
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            background-color: #f5f5f5;
        }
        .logo-container {
            text-align: center;
            margin: 20px 0;
        }
        .logo {
            max-width: 300px;
            height: auto;
            margin: 0 auto;
        }
        .app-title {
            text-align: center;
            color: #C4A962;
            margin: 20px 0;
            font-size: 2em;
            font-weight: bold;
        }
        .app-subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 1.2em;
        }
        .container {
            border: 1px solid #ddd;
            padding: 20px;
            border-radius: 8px;
            background-color: #fff;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .form-group {
            margin-bottom: 20px;
        }
        .btn {
            background-color: #C4A962;
            color: white;
            padding: 12px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            transition: background-color 0.3s ease;
        }
        .btn:hover {
            background-color: #B39855;
        }
        .flash-messages {
            color: #d9534f;
            margin-bottom: 15px;
            padding: 10px;
            border-radius: 4px;
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
        }
        .format-info {
            background-color: #e7f3fe;
            border-left: 6px solid #2196F3;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 4px;
        }
        .format-list {
            columns: 3;
            -webkit-columns: 3;
            -moz-columns: 3;
            list-style-type: none;
            padding-left: 0;
            margin-top: 10px;
        }
        .format-list li {
            margin-bottom: 8px;
            color: #555;
        }
        input[type="file"] {
            padding: 10px;
            border: 2px dashed #C4A962;
            border-radius: 4px;
            width: 100%;
            margin-top: 5px;
        }
        .checkbox-container {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
        }
        .checkbox-container input[type="checkbox"] {
            margin-right: 10px;
        }
        .author-info {
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
            border-top: 1px solid #eee;
        }
        .debug-container {
            margin-top: 20px;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            background-color: #f8f9fa;
            max-height: 200px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 12px;
        }
        .debug-container h4 {
            margin-top: 0;
            color: #333;
        }
        .debug-log {
            margin: 0;
            padding: 0;
            list-style-type: none;
        }
        .debug-log li {
            margin-bottom: 5px;
            padding: 3px 0;
            border-bottom: 1px dotted #eee;
        }
        .debug-toggle {
            background-color: #f1f1f1;
            border: none;
            color: #666;
            padding: 5px 10px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 12px;
            margin: 4px 2px;
            cursor: pointer;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="logo-container">
        <img src="{{ url_for('static', filename='tresorhaus-logo.png') }}" alt="TresorHaus Logo" class="logo">
    </div>

    <div class="app-title">TresorHaus DocFlow</div>
    <div class="app-subtitle">Dokumentenkonverter</div>

    <div class="container">
        <div class="format-info">
            <h3>Unterstützte Dateiformate:</h3>
            <ul class="format-list">
                <li>.doc, .docx (Word)</li>
                <li>.odt (OpenOffice/LibreOffice)</li>
                <li>.rtf (Rich Text Format)</li>
                <li>.tex (LaTeX)</li>
                <li>.html, .htm (HTML)</li>
                <li>.epub (E-Book)</li>
                <li>.ppt, .pptx (PowerPoint)</li>
                <li>.odp (Impress)</li>
                <li>.rst (reStructuredText)</li>
                <li>.textile (Textile)</li>
                <li>.wiki (MediaWiki)</li>
                <li>.dbk, .xml (DocBook)</li>
                <li>.adoc, .asciidoc (AsciiDoc)</li>
                <li>.org (Org-mode)</li>
            </ul>
        </div>

        {% if get_flashed_messages() %}
        <div class="flash-messages">
            {% for message in get_flashed_messages() %}
                <p>{{ message }}</p>
            {% endfor %}
        </div>
        {% endif %}

        <form method="post" enctype="multipart/form-data">
            <div class="form-group">
                <label for="files">Wähle Dateien zum Konvertieren aus:</label>
                <input type="file" name="files" id="files" multiple>
            </div>
            <div class="checkbox-container">
                <input type="checkbox" name="upload_to_wiki" id="upload_to_wiki" value="1">
                <label for="upload_to_wiki">In Wiki.js hochladen</label>
                <button type="button" id="test-api" class="btn-secondary" style="margin-left: 10px;">API-Verbindung testen</button>
                <span id="api-test-result" style="margin-left: 10px;"></span>
            </div>
            <div class="form-group">
                <button type="submit" class="btn">Konvertieren</button>
            </div>
        </form>

        <button id="debug-toggle" class="debug-toggle">Debug-Informationen anzeigen</button>
        <div id="debug-container" class="debug-container" style="display: none;">
            <h4>Debug-Log</h4>
            <ul id="debug-log" class="debug-log"></ul>
        </div>

        <script>
        // API-Test Funktionalität
        document.getElementById('test-api').addEventListener('click', async () => {
            const resultSpan = document.getElementById('api-test-result');
            const debugLog = document.getElementById('debug-log');

            resultSpan.textContent = 'Teste Verbindung...';
            resultSpan.style.color = 'gray';

            // Log debug info
            debugLog.innerHTML += `<li>${new Date().toLocaleTimeString()}: Starte API-Verbindungstest...</li>`;

            try {
                const response = await fetch('/test_wikijs_connection', {
                    method: 'POST',
                });
                const data = await response.json();

                resultSpan.textContent = data.message;
                resultSpan.style.color = data.success ? '#4CAF50' : '#f44336';

                // Log response details
                debugLog.innerHTML += `<li>${new Date().toLocaleTimeString()}: API-Test Antwort: ${data.success ? 'Erfolg' : 'Fehlgeschlagen'}</li>`;
                debugLog.innerHTML += `<li>${new Date().toLocaleTimeString()}: Nachricht: ${data.message}</li>`;
            } catch (error) {
                resultSpan.textContent = 'Fehler beim Testen der Verbindung';
                resultSpan.style.color = '#f44336';

                // Log error
                debugLog.innerHTML += `<li>${new Date().toLocaleTimeString()}: Fehler beim API-Test: ${error.message}</li>`;
            }
        });

        // Form submission with debug logging
        document.querySelector('form').addEventListener('submit', function() {
            const debugLog = document.getElementById('debug-log');
            const uploadToWiki = document.getElementById('upload_to_wiki').checked;

            debugLog.innerHTML += `<li>${new Date().toLocaleTimeString()}: Formular wird abgesendet...</li>`;
            debugLog.innerHTML += `<li>${new Date().toLocaleTimeString()}: Wiki.js Upload aktiviert: ${uploadToWiki ? 'Ja' : 'Nein'}</li>`;

            const files = document.getElementById('files').files;
            if (files.length > 0) {
                debugLog.innerHTML += `<li>${new Date().toLocaleTimeString()}: ${files.length} Datei(en) ausgewählt: ${Array.from(files).map(f => f.name).join(', ')}</li>`;
            } else {
                debugLog.innerHTML += `<li>${new Date().toLocaleTimeString()}: Keine Dateien ausgewählt</li>`;
            }
        });

        // Toggle debug panel
        document.getElementById('debug-toggle').addEventListener('click', function() {
            const debugContainer = document.getElementById('debug-container');
            if (debugContainer.style.display === 'none') {
                debugContainer.style.display = 'block';
                this.textContent = 'Debug-Informationen ausblenden';
            } else {
                debugContainer.style.display = 'none';
                this.textContent = 'Debug-Informationen anzeigen';
            }
        });
        </script>

        <style>
        .btn-secondary {
            background-color: #666;
            color: white;
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: background-color 0.3s ease;
        }
        .btn-secondary:hover {
            background-color: #555;
        }
        #api-test-result {
            display: inline-block;
            font-size: 14px;
            font-weight: bold;
        }
        </style>
    </div>

    <div class="author-info">
        Entwickelt von Joachim Mild für TresorHaus GmbH © 2025
    </div>
</body>
</html>
'''
RESULT_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>TresorHaus DocFlow - Konvertierungsergebnisse</title>
    <link rel="icon" type="image/png" href="{{ url_for('static', filename='favicon.png') }}">
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            background-color: #f5f5f5;
        }
        .logo-container {
            text-align: center;
            margin: 20px 0;
        }
        .logo {
            max-width: 300px;
            height: auto;
            margin: 0 auto;
        }
        .app-title {
            text-align: center;
            color: #C4A962;
            margin: 20px 0;
            font-size: 2em;
            font-weight: bold;
        }
        .app-subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 1.2em;
        }
        .container {
            border: 1px solid #ddd;
            padding: 20px;
            border-radius: 8px;
            background-color: #fff;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .btn {
            background-color: #C4A962;
            color: white;
            padding: 12px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            text-decoration: none;
            display: inline-block;
            margin-top: 10px;
            transition: background-color 0.3s ease;
        }
        .btn:hover {
            background-color: #B39855;
        }
        .file-list {
            list-style-type: none;
            padding: 0;
        }
        .file-list li {
            padding: 12px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .file-list li:last-child {
            border-bottom: none;
        }
        .file-link {
            color: #C4A962;
            text-decoration: none;
            padding: 6px 12px;
            border: 1px solid #C4A962;
            border-radius: 4px;
            transition: all 0.3s ease;
            margin-left: 10px;
        }
        .file-link:hover {
            background-color: #C4A962;
            color: white;
        }
        .wiki-link {
            background-color: #4CAF50;
            color: white !important;
            border-color: #4CAF50;
        }
        .wiki-link:hover {
            background-color: #45a049;
        }
        .error-list {
            color: #d9534f;
        }
        h1, h2 {
            color: #333;
            margin-bottom: 20px;
        }
        .action-buttons {
            display: flex;
            gap: 10px;
        }
        .author-info {
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
            border-top: 1px solid #eee;
        }
        .debug-container {
            margin-top: 20px;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            background-color: #f8f9fa;
            max-height: 300px;
            overflow-y: auto;
            font-family: monospace;
            font-size: 12px;
        }
        .debug-container h4 {
            margin-top: 0;
            color: #333;
        }
        .debug-log {
            margin: 0;
            padding: 0;
            list-style-type: none;
        }
        .debug-log li {
            margin-bottom: 5px;
            padding: 3px 0;
            border-bottom: 1px dotted #eee;
        }
        .api-log-entry {
            color: #0066cc;
        }
        .error-log-entry {
            color: #cc0000;
        }
        .success-log-entry {
            color: #009900;
        }
        .debug-toggle {
            background-color: #f1f1f1;
            border: none;
            color: #666;
            padding: 5px 10px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 12px;
            margin: 4px 2px;
            cursor: pointer;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="logo-container">
        <img src="{{ url_for('static', filename='tresorhaus-logo.png') }}" alt="TresorHaus Logo" class="logo">
    </div>

    <div class="app-title">TresorHaus DocFlow</div>
    <div class="app-subtitle">Konvertierungsergebnisse</div>

    <div class="container">
        {% if converted_files %}
        <h2>Erfolgreich konvertierte Dateien:</h2>
        <ul class="file-list">
            {% for file in converted_files %}
            <li>
                <span>{{ file }}</span>
                <div class="action-buttons">
                    <a href="{{ url_for('download_single_file', session_id=session_id, filename=file) }}"
                       class="file-link">Herunterladen</a>
                    {% if file in wiki_urls %}
                    <a href="{{ wiki_urls[file] }}"
                       class="file-link wiki-link"
                       target="_blank">In Wiki.js ansehen</a>
                    {% endif %}
                </div>
            </li>
            {% endfor %}
        </ul>
        <a href="{{ url_for('download_results', session_id=session_id) }}" class="btn">Alle als ZIP herunterladen</a>
        {% endif %}

        {% if failed_files %}
        <h2>Fehler bei der Konvertierung:</h2>
        <ul class="file-list error-list">
            {% for file in failed_files %}
            <li>{{ file }}</li>
            {% endfor %}
        </ul>
        {% endif %}

        <button id="debug-toggle" class="debug-toggle">Debug-Informationen anzeigen</button>
        <div id="debug-container" class="debug-container" style="display: none;">
            <h4>API und Konvertierungs-Log</h4>
            <ul class="debug-log">
                <li><strong>Session ID:</strong> {{ session_id }}</li>
                <li><strong>Upload zu Wiki.js:</strong> {{ 'Aktiviert' if wiki_requested else 'Deaktiviert' }}</li>
                {% for log in debug_logs %}
                <li class="{{ log.type }}-log-entry">{{ log.time }}: {{ log.message }}</li>
                {% endfor %}
            </ul>
        </div>

        <script>
        document.getElementById('debug-toggle').addEventListener('click', function() {
            const debugContainer = document.getElementById('debug-container');
            if (debugContainer.style.display === 'none') {
                debugContainer.style.display = 'block';
                this.textContent = 'Debug-Informationen ausblenden';
            } else {
                debugContainer.style.display = 'none';
                this.textContent = 'Debug-Informationen anzeigen';
            }
        });
        </script>
    </div>

    <a href="{{ url_for('index') }}" class="btn">Zurück zur Startseite</a>

    <div class="author-info">
        Entwickelt von Joachim Mild für TresorHaus GmbH © 2025
    </div>
</body>
</html>
'''

# Favicon Route
@app.route('/static/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.png',
        mimetype='image/png'
    )

def allowed_file(filename):
    """Überprüft, ob die Dateiendung erlaubt ist"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_input_format(filename):
    """Bestimmt das Eingabeformat für Pandoc basierend auf der Dateiendung"""
    ext = filename.rsplit('.', 1)[1].lower()
    return FORMAT_MAPPING.get(ext, 'docx')

# Globale Variable für Debug-Logs
debug_logs = []

def log_debug(message, log_type='info'):
    """Fügt eine Debug-Nachricht zum Log hinzu"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    debug_logs.append({
        'time': timestamp,
        'message': message,
        'type': log_type
    })
    print(f"[{timestamp}] {log_type.upper()}: {message}")

def upload_to_wikijs(content, title, session_id):
    """Lädt eine Markdown-Datei in Wiki.js hoch"""
    if not WIKIJS_URL or not WIKIJS_TOKEN:KEN:
        log_debug("Wiki.js URL oder Token nicht konfiguriert", "error")
        return False, None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"DocFlow/{session_id}_{timestamp}/{title}"
    # Entferne .md Erweiterung aus dem Titel und dem Pfad
    # Entferne .md Erweiterung aus dem Titel wenn vorhanden
    title_without_extension = title):
    if title.lower().endswith('.md'):le[:-3]
        title_without_extension = title[:-3]
    # Verwende den Titel ohne .md Erweiterung im Pfad
    log_debug(f"Starte Upload zu Wiki.js: {title_without_extension}", "api")
    log_debug(f"Ziel-Pfad: {path}", "api")
    log_debug(f"Starte Upload zu Wiki.js: {title_without_extension}", "api")
    log_debug(f"Ziel-Pfad: {path}", "api")

    headers = {
        'Authorization': f'Bearer {WIKIJS_TOKEN}',
        'Content-Type': 'application/json'
    }

    # Vereinfachte GraphQL mutation für das Erstellen einer neuen Seite
    # Basierend auf dem bereitgestellten curl-Beispiel
    mutation = """
    mutation ($content: String!, $description: String!, $editor: String!, $isPublished: Boolean!, $locale: String!, $path: String!, $tags: [String]!, $title: String!) {
      pages {
        create(content: $content, description: $description, editor: $editor, isPublished: $isPublished, locale: $locale, path: $path, tags: $tags, title: $title) {
          responseResult {
            succeeded
            message
          }
        }
      }
    }
    """

    variables = {
        'content': content,
        'description': f'Automatisch erstellt durch TresorHaus DocFlow am {timestamp}',
        'editor': 'markdown',
        'isPublished': True,
        'locale': 'de',  # Kann je nach Bedarf auf 'en' geändert werden
        'path': path,
        'tags': ['DocFlow', 'Automatisch'],
        'title': title_without_extension  # Immer ohne .md Erweiterung
    }

    try:
        log_debug(f"Sende Wiki.js Request an: {WIKIJS_URL}/graphql", "api")

        # POST mit json payload für die Mutation
        response = requests.post(
            f'{WIKIJS_URL}/graphql',  # Direkter /graphql Endpunkt wie im curl-Beispiel
            headers=headers,
            json={
                'query': mutation,
                'variables': variables
            }
        )

        log_debug(f"Status Code: {response.status_code}", "api")

        response.raise_for_status()
        data = response.json()

        if 'errors' in data:
            error_msg = str(data['errors'])
            log_debug(f"GraphQL Fehler: {error_msg}", "error")
            return False, None

        # Vereinfachter Zugriff auf das Ergebnis entsprechend der curl-Beispielstruktur
        result = data.get('data', {}).get('pages', {}).get('create', {}).get('responseResult', {})
        if result.get('succeeded'):
            # Konstruiere die vollständige Wiki.js URL zur Seite
            wiki_url = f"{WIKIJS_URL}/{path}"
            log_debug(f"Wiki.js Seite erfolgreich erstellt: {wiki_url}", "success")
            return True, wiki_url
        else:
            error_message = result.get('message', 'Unbekannter Fehler')
            log_debug(f"Wiki.js Fehler: {error_message}", "error")
            return False, None

    except Exception as e:
        log_debug(f"Fehler beim Upload zu Wiki.js: {str(e)}", "error")
        return False, None

def convert_to_markdown(input_path, output_path):
    """Konvertiert eine Datei in Markdown mithilfe von pandoc"""
    input_format = get_input_format(input_path)

    # Create directory if it doesn't exist
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        subprocess.run([
            'pandoc',
            input_path,
            '-f', input_format,
            '-t', 'markdown',
            '-o', output_path
        ], check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Fehler bei der Konvertierung von {input_path}: {e}")
        return False

def process_uploads(files, session_id, upload_to_wiki=False):
    """Verarbeitet hochgeladene Dateien und konvertiert sie zu Markdown"""
    global debug_logs
    debug_logs = []  # Zurücksetzen der Debug-Logs für jede neue Sitzung

    upload_dir = os.path.join(UPLOAD_FOLDER, session_id)
    result_dir = os.path.join(RESULT_FOLDER, session_id)

    log_debug(f"Neue Upload-Verarbeitung gestartet. Session ID: {session_id}")
    log_debug(f"Wiki.js-Upload aktiviert: {'Ja' if upload_to_wiki else 'Nein'}")

    # Create directories if they don't exist
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        log_debug(f"Upload-Verzeichnis erstellt: {upload_dir}")
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)
        log_debug(f"Ergebnis-Verzeichnis erstellt: {result_dir}")

    converted_files = []
    failed_files = []
    wiki_urls = {}

    log_debug(f"{len(files)} Datei(en) für die Verarbeitung empfangen")

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            log_debug(f"Verarbeite Datei: {filename}")

            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)
            log_debug(f"Datei gespeichert unter: {file_path}")

            output_filename = os.path.splitext(filename)[0] + '.md'
            output_path = os.path.join(result_dir, output_filename)

            log_debug(f"Starte Konvertierung zu: {output_filename}")
            if convert_to_markdown(file_path, output_path):
                log_debug(f"Konvertierung erfolgreich: {output_filename}", "success")
                converted_files.append(output_filename)

                if upload_to_wiki:
                    log_debug(f"Beginne Upload zu Wiki.js: {output_filename}", "api")
                    try:
                        with open(output_path, 'r', encoding='utf-8') as md_file:
                            content = md_file.read()
                            log_debug(f"Markdown-Datei gelesen: {len(content)} Zeichen", "api")ki_url = upload_to_wikijs(content, output_filename, session_id)
                            success, wiki_url = upload_to_wikijs(content, output_filename, session_id)
                            if success:
                                wiki_urls[output_filename] = wiki_urlog_debug(f"Wiki.js Upload erfolgreich: {wiki_url}", "success")
                                log_debug(f"Wiki.js Upload erfolgreich: {wiki_url}", "success")
                            else:f"Wiki.js Upload fehlgeschlagen für {output_filename}", "error")
                                log_debug(f"Wiki.js Upload fehlgeschlagen für {output_filename}", "error")
                    except Exception as e:       log_debug(f"Fehler beim Lesen/Hochladen von {output_filename}: {str(e)}", "error")
                        log_debug(f"Fehler beim Lesen/Hochladen von {output_filename}: {str(e)}", "error")
            else:lgeschlagen: {filename}", "error")
                log_debug(f"Konvertierung fehlgeschlagen: {filename}", "error")   failed_files.append(filename)
                failed_files.append(filename)
        else:
            if not file:og_debug("Leerer Datei-Eintrag übersprungen", "error")
                log_debug("Leerer Datei-Eintrag übersprungen", "error")
            else:                log_debug(f"Ungültiges Dateiformat: {file.filename}", "error")
                log_debug(f"Ungültiges Dateiformat: {file.filename}", "error")
nverted_files)} konvertiert, {len(failed_files)} fehlgeschlagen")
    log_debug(f"Verarbeitung abgeschlossen: {len(converted_files)} konvertiert, {len(failed_files)} fehlgeschlagen")    return converted_files, failed_files, wiki_urls
    return converted_files, failed_files, wiki_urls

def create_zip_file(session_id):arkdown-Dateien"""
    """Erstellt eine ZIP-Datei mit allen konvertierten Markdown-Dateien"""RESULT_FOLDER, session_id)
    result_dir = os.path.join(RESULT_FOLDER, session_id)    memory_file = io.BytesIO()
    memory_file = io.BytesIO()
.ZIP_DEFLATED) as zf:
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:os.walk(result_dir):
        for root, _, files in os.walk(result_dir):
            for file in files:
                file_path = os.path.join(root, file)le_path, result_dir)
                rel_path = os.path.relpath(file_path, result_dir)                zf.write(file_path, rel_path)
                zf.write(file_path, rel_path)
)
    memory_file.seek(0)    return memory_file
    return memory_file

def cleanup_session(session_id):
    """Bereinigt die temporären Dateien einer Session"""
    upload_dir = os.path.join(UPLOAD_FOLDER, session_id)    result_dir = os.path.join(RESULT_FOLDER, session_id)
    result_dir = os.path.join(RESULT_FOLDER, session_id)
:
    if os.path.exists(upload_dir):
        shutil.rmtree(upload_dir):
    if os.path.exists(result_dir):        shutil.rmtree(result_dir)
        shutil.rmtree(result_dir)
/', methods=['GET', 'POST'])
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'files' not in request.files:hlt')
            flash('Keine Dateien ausgewählt')            return redirect(request.url)
            return redirect(request.url)

        files = request.files.getlist('files')        upload_to_wiki = 'upload_to_wiki' in request.form
        upload_to_wiki = 'upload_to_wiki' in request.form
'':
        if not files or files[0].filename == '':hlt')
            flash('Keine Dateien ausgewählt')            return redirect(request.url)
            return redirect(request.url)

        session_id = str(uuid.uuid4())        converted_files, failed_files, wiki_urls = process_uploads(files, session_id, upload_to_wiki)
        converted_files, failed_files, wiki_urls = process_uploads(files, session_id, upload_to_wiki)

        if not converted_files und nicht failed_files:n zum Konvertieren gefunden')
            flash('Keine gültigen Dateien zum Konvertieren gefunden')            return redirect(request.url)
            return redirect(request.url)
te_string(
        return render_template_string(
            RESULT_TEMPLATE,files,
            converted_files=converted_files,files,
            failed_files=failed_files,
            wiki_urls=wiki_urls,
            session_id=session_id,
            debug_logs=debug_logs,   wiki_requested=upload_to_wiki
            wiki_requested=upload_to_wiki        )
        )
    return render_template_string(INDEX_TEMPLATE)
    return render_template_string(INDEX_TEMPLATE)
>', methods=['GET'])
@app.route('/download/<session_id>', methods=['GET'])
def download_results(session_id):le(session_id)
    memory_file = create_zip_file(session_id)    cleanup_session(session_id)
    cleanup_session(session_id)
(
    return send_file(
        memory_file,erted_markdown_files.zip',
        download_name='converted_markdown_files.zip',
        as_attachment=True,   mimetype='application/zip'
        mimetype='application/zip'    )
    )
name>', methods=['GET'])
@app.route('/download_single/<session_id>/<filename>', methods=['GET'])
def download_single_file(session_id, filename):    file_path = os.path.join(RESULT_FOLDER, session_id, filename)
    file_path = os.path.join(RESULT_FOLDER, session_id, filename)

    if not os.path.exists(file_path):
        flash('Datei nicht gefunden')        return redirect(url_for('index'))
        return redirect(url_for('index'))
le(
    return send_file(
        file_path,ame,
        download_name=filename,
        as_attachment=True,   mimetype='text/markdown'
        mimetype='text/markdown'    )
    )
ection', methods=['POST'])
@app.route('/test_wikijs_connection', methods=['POST'])ction():
def test_wikijs_connection():
    global debug_logs    debug_logs = []  # Zurücksetzen der Debug-Logs
    debug_logs = []  # Zurücksetzen der Debug-Logs

    if not WIKIJS_URL oder nicht WIKIJS_TOKEN:
        log_debug("Wiki.js URL oder Token nicht konfiguriert", "error")        return {'success': False, 'message': 'Wiki.js URL oder Token nicht konfiguriert'}
        return {'success': False, 'message': 'Wiki.js URL oder Token nicht konfiguriert'}
st connection using pages list query
    # Test connection using pages list query
    try:
        # Use a simple query to list pages
        test_query = "{pages{list{id,title,path,contentType}}}"        log_debug(f"Teste Wiki.js Verbindung zu: {WIKIJS_URL}", "api")
        log_debug(f"Teste Wiki.js Verbindung zu: {WIKIJS_URL}", "api")
ery parameter
        # URL encode the query parameter
        import urllib.parse        encoded_query = urllib.parse.quote(test_query)
        encoded_query = urllib.parse.quote(test_query)

        headers = {   'Authorization': f'Bearer {WIKIJS_TOKEN}'
            'Authorization': f'Bearer {WIKIJS_TOKEN}'
        }        log_debug(f"Sende GET-Anfrage an: {WIKIJS_URL}/graphql/pages/list", "api")
        log_debug(f"Sende GET-Anfrage an: {WIKIJS_URL}/graphql/pages/list", "api")
 pages list endpoint with query as URL parameter
        # Use GET request to the pages list endpoint with query as URL parameter
        response = requests.get(graphql/pages/list?query={encoded_query}',
            f'{WIKIJS_URL}/graphql/pages/list?query={encoded_query}',   headers=headers
            headers=headers        )
        )

        # Log detailed debug info        log_debug(f"Status Code: {response.status_code}", "api")
        log_debug(f"Status Code: {response.status_code}", "api")
tus()
        response.raise_for_status()        data = response.json()
        data = response.json()

        if 'errors' in data:Unbekannter GraphQL-Fehler')
            error_msg = data['errors'][0].get('message', 'Unbekannter GraphQL-Fehler')g(f"API-Fehler: {error_msg}", "error")
            log_debug(f"API-Fehler: {error_msg}", "error")
            return {
                'success': False,   'message': f"API-Fehler: {error_msg}\nBitte überprüfen Sie den API-Token."
                'message': f"API-Fehler: {error_msg}\nBitte überprüfen Sie den API-Token."            }
            }

        # Check if we got a valid response with pages datalist' in data['data']['pages']:
        if 'data' in data und 'pages' in data['data'] und 'list' in data['data']['pages']:
            page_count = len(data['data']['pages']['list'])
            log_debug(f"Verbindung erfolgreich! {page_count} Seiten gefunden.", "success")eturn {'success': True, 'message': f'Verbindung zu Wiki.js erfolgreich hergestellt! {page_count} Seiten gefunden.'}
            return {'success': True, 'message': f'Verbindung zu Wiki.js erfolgreich hergestellt! {page_count} Seiten gefunden.'}
        else:g("Unerwartetes Antwortformat von Wiki.js", "error")
            log_debug("Unerwartetes Antwortformat von Wiki.js", "error")
            return {
                'success': False,   'message': 'Unerwartetes Antwortformat von Wiki.js. Bitte überprüfen Sie die API-Konfiguration.'
                'message': 'Unerwartetes Antwortformat von Wiki.js. Bitte überprüfen Sie die API-Konfiguration.'            }
            }

    except requests.exceptions.ConnectionError:g(f"Verbindungsfehler: Server nicht erreichbar unter {WIKIJS_URL}", "error")
        log_debug(f"Verbindungsfehler: Server nicht erreichbar unter {WIKIJS_URL}", "error")
        return {
            'success': False,   'message': f'Verbindungsfehler: Server nicht erreichbar unter {WIKIJS_URL}'
            'message': f'Verbindungsfehler: Server nicht erreichbar unter {WIKIJS_URL}'
        }
    except requests.exceptions.HTTPError as e:se.status_code}: {e.response.text}", "error")
        log_debug(f"HTTP-Fehler {e.response.status_code}: {e.response.text}", "error")e.status_code == 401:
        if e.response.status_code == 401:
            return {
                'success': False,   'message': 'Authentifizierungsfehler: Ungültiger API-Token'
                'message': 'Authentifizierungsfehler: Ungültiger API-Token'
            }nse.status_code == 400:
        elif e.response.status_code == 400:
            return {
                'success': False,   'message': 'API-Fehler: Ungültige Anfrage. Bitte überprüfen Sie die Wiki.js-URL und den API-Token'
                'message': 'API-Fehler: Ungültige Anfrage. Bitte überprüfen Sie die Wiki.js-URL und den API-Token'
            }
        return {
            'success': False,   'message': f'HTTP-Fehler {e.response.status_code}: {e.response.text}'
            'message': f'HTTP-Fehler {e.response.status_code}: {e.response.text}'
        }
    except Exception as e:g(f"Unerwarteter Fehler: {str(e)}", "error")
        log_debug(f"Unerwarteter Fehler: {str(e)}", "error")
        return {
            'success': False,   'message': f'Unerwarteter Fehler: {str(e)}\nBitte überprüfen Sie die Konsole für weitere Details.'
            'message': f'Unerwarteter Fehler: {str(e)}\nBitte überprüfen Sie die Konsole für weitere Details.'        }
        }

if __name__ == '__main__':    app.run(debug=True, host='0.0.0.0', port=5000)


    app.run(debug=True, host='0.0.0.0', port=5000)
