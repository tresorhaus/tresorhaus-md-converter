"""
 DocFlow
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
from datetime import datetime
from dotenv import load_dotenv
import re

# Import utils functions
from utils import (
    allowed_file, sanitize_wikijs_path, sanitize_wikijs_title,
    sanitize_filename, clean_markdown_content, ensure_static_files_exist
)

# Import modules for Wiki.js and export functionality
import wikijs
import export

# Lade Umgebungsvariablen
load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
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
WIKIJS_EXTERNAL_URL = os.getenv('WIKIJS_EXTERNAL_URL')
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

# Add OUTPUT_FORMAT_MAPPING after the existing FORMAT_MAPPING
OUTPUT_FORMAT_MAPPING = {
    'docx': 'docx',
    'odt': 'odt',
    'rtf': 'rtf',
    'pdf': 'pdf',
    'html': 'html',
    'tex': 'latex',
    'epub': 'epub',
    'pptx': 'pptx'
}

# HTML-Templates werden jetzt aus Dateien geladen
def load_template(filename):
    """Lädt ein Template aus einer Datei"""
    template_path = os.path.join(app.template_folder, filename)
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Fehler beim Laden des Templates {filename}: {e}")
        return f"<h1>Fehler beim Laden des Templates {filename}</h1>"

# Favicon Route
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'favicon.ico',
        mimetype='image/x-icon'
    )

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

def process_uploads(files, session_id, upload_to_wiki=False, wiki_paths=None, wiki_titles=None, username=None, default_folder=None):
    """Verarbeitet hochgeladene Dateien und konvertiert sie zu Markdown"""
    global debug_logs
    debug_logs = []  # Zurücksetzen der Debug-Logs für jede neue Sitzung

    upload_dir = os.path.join(UPLOAD_FOLDER, session_id)
    result_dir = os.path.join(RESULT_FOLDER, session_id)

    log_debug(f"Neue Upload-Verarbeitung gestartet. Session ID: {session_id}")
    log_debug(f"Benutzer: {username or 'Nicht angegeben'}")
    log_debug(f"Wiki.js-Upload aktiviert: {'Ja' if upload_to_wiki else 'Nein'}")

    # Sicherstellen, dass wiki_paths und wiki_titles Dictionaries sind
    if wiki_paths is None:
        wiki_paths = {}
    if wiki_titles is None:
        wiki_titles = {}

    log_debug(f"Wiki Titel: {wiki_titles}", "info")

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

    for i, file in enumerate(files):
        if file and allowed_file(file.filename, ALLOWED_EXTENSIONS):
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
                            log_debug(f"Markdown-Datei gelesen: {len(content)} Zeichen", "api")

                            # Hole benutzerdefinierte Pfad und Titel für diese Datei
                            custom_path = wiki_paths.get(f"path_{i}", "")
                            custom_title = wiki_titles.get(f"title_{i}", "")

                            # Für Titel: Wenn ein benutzerdefinierter Titel vorhanden ist, verwende diesen,
                            # ansonsten verwende den bereinigten Dateinamen ohne Erweiterung
                            if not custom_title or custom_title.strip() == "":
                                # Extrahiere den Dateinamen ohne Erweiterung
                                base_title = os.path.splitext(filename)[0]
                                # Sanitiere den Titel automatisch
                                sanitized_title = sanitize_wikijs_title(base_title)
                                custom_title = sanitized_title
                                log_debug(f"Kein Titel angegeben, verwende automatisch sanitierten Dateinamen: '{sanitized_title}'", "info")

                            # Überprüfe, ob der Pfad oder Titel ungültige Zeichen enthält, bevor sie sanitiert werden
                            if custom_path and not sanitize_wikijs_path(custom_path) == custom_path:
                                log_debug(f"Warnung: Benutzerdefinierter Pfad '{custom_path}' enthält ungültige Zeichen und wird sanitiert.", "warning")

                            if custom_title and not sanitize_wikijs_title(custom_title) == custom_title:
                                log_debug(f"Warnung: Benutzerdefinierter Titel '{custom_title}' enthält ungültige Zeichen und wird sanitiert.", "warning")

                            log_debug(f"Benutzerdefinierter Pfad: {custom_path}", "info")
                            log_debug(f"Benutzerdefinierter Titel: {custom_title}", "info")

                            # Verwende die WikiJS-Funktion für den Upload
                            success, wiki_url = wikijs.upload_content(
                                content,
                                output_filename,
                                session_id,
                                WIKIJS_URL,
                                WIKIJS_TOKEN,
                                custom_path=custom_path,
                                custom_title=custom_title,
                                username=username,
                                default_folder=default_folder,
                                debug_logger=log_debug,
                                external_url=WIKIJS_EXTERNAL_URL,
                                sanitize_wikijs_path_fn=sanitize_wikijs_path,
                                sanitize_wikijs_title_fn=sanitize_wikijs_title,
                                clean_markdown_content_fn=clean_markdown_content
                            )

                            if success:
                                wiki_urls[output_filename] = wiki_url
                                log_debug(f"Wiki.js Upload erfolgreich: {wiki_url}", "success")
                            else:
                                log_debug(f"Wiki.js Upload fehlgeschlagen für {output_filename}", "error")
                    except Exception as e:
                        log_debug(f"Fehler beim Lesen/Hochladen von {output_filename}: {str(e)}", "error")
            else:
                log_debug(f"Konvertierung fehlgeschlagen: {filename}", "error")
                failed_files.append(filename)
        else:
            if not file:
                log_debug("Leerer Datei-Eintrag übersprungen", "error")
            else:
                log_debug(f"Ungültiges Dateiformat: {file.filename}", "error")

    log_debug(f"Verarbeitung abgeschlossen: {len(converted_files)} konvertiert, {len(failed_files)} fehlgeschlagen")
    return converted_files, failed_files, wiki_urls

def cleanup_session(session_id):
    """Bereinigt die temporären Dateien einer Session"""
    upload_dir = os.path.join(UPLOAD_FOLDER, session_id)
    result_dir = os.path.join(RESULT_FOLDER, session_id)

    if os.path.exists(upload_dir):
        shutil.rmtree(upload_dir)
    if os.path.exists(result_dir):
        shutil.rmtree(result_dir)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'files' not in request.files:
            flash('Keine Dateien ausgewählt')
            return redirect(request.url)

        files = request.files.getlist('files')
        upload_to_wiki = 'upload_to_wiki' in request.form

        if not files or files[0].filename == '':
            flash('Keine Dateien ausgewählt')
            return redirect(request.url)

        session_id = str(uuid.uuid4())

        # Get username and default folder
        username = request.form.get('username', '')
        default_folder = request.form.get('default_folder', '')

        # Sammle benutzerdefinierte Wiki.js Pfade und Titel
        wiki_paths = {}
        wiki_titles = {}

        for key, value in request.form.items():
            if key.startswith('wiki_path_'):
                index = key.replace('wiki_path_', '')
                wiki_paths[f"path_{index}"] = value
            elif key.startswith('wiki_title_'):
                index = key.replace('wiki_title_', '')
                wiki_titles[f"title_{index}"] = value

        converted_files, failed_files, wiki_urls = process_uploads(
            files,
            session_id,
            upload_to_wiki,
            wiki_paths=wiki_paths,
            wiki_titles=wiki_titles,
            username=username,
            default_folder=default_folder
        )

        if not converted_files and not failed_files:
            flash('Keine gültigen Dateien zum Konvertieren gefunden')
            return redirect(request.url)

        return render_template_string(
            load_template('results.html'),
            converted_files=converted_files,
            failed_files=failed_files,
            wiki_urls=wiki_urls,
            session_id=session_id,
            debug_logs=debug_logs,
            wiki_requested=upload_to_wiki,
            wiki_url=WIKIJS_URL,
            api_token_exists=bool(WIKIJS_TOKEN)
        )

    return render_template_string(load_template('index.html'))

@app.route('/download/<session_id>', methods=['GET'])
def download_results(session_id):
    memory_file = export.create_zip_file(session_id, RESULT_FOLDER)
    cleanup_session(session_id)

    return send_file(
        memory_file,
        download_name='converted_markdown_files.zip',
        as_attachment=True,
        mimetype='application/zip'
    )

@app.route('/download_single/<session_id>/<filename>', methods=['GET'])
def download_single_file(session_id, filename):
    file_path = os.path.join(RESULT_FOLDER, session_id, filename)

    if not os.path.exists(file_path):
        flash('Datei nicht gefunden')
        return redirect(url_for('index'))

    return send_file(
        file_path,
        download_name=filename,
        as_attachment=True,
        mimetype='text/markdown'
    )

@app.route('/test_wikijs_connection', methods=['POST'])
def test_wikijs_connection():
    global debug_logs
    debug_logs = []  # Zurücksetzen der Debug-Logs

    # Use the wikijs module function for testing connection
    result = wikijs.test_connection(WIKIJS_URL, WIKIJS_TOKEN, log_debug)
    return result

@app.route('/get_wikijs_directories', methods=['GET'])
def get_wikijs_directories():
    """Retrieves a list of all directories from Wiki.js"""
    # Use the wikijs module function
    return wikijs.get_directories(WIKIJS_URL, WIKIJS_TOKEN, log_debug)

@app.route('/export', methods=['GET', 'POST'], endpoint='export')
def export_route():
    if request.method == 'POST':
        selected_pages = request.form.getlist('pages')
        selected_formats = request.form.getlist('formats')

        if not selected_pages:
            flash('Bitte wählen Sie mindestens eine Wiki.js-Seite aus.')
            return redirect(request.url)

        if not selected_formats:
            flash('Bitte wählen Sie mindestens ein Ausgabeformat aus.')
            return redirect(request.url)

        session_id = str(uuid.uuid4())

        # Reset debug logs for this session
        global debug_logs
        debug_logs = []

        # Use the export module function
        converted_files, failed_files, debug_data = export.export_pages_to_formats(
            selected_pages,
            selected_formats,
            session_id,
            RESULT_FOLDER,
            WIKIJS_URL,
            WIKIJS_TOKEN,
            OUTPUT_FORMAT_MAPPING,
            sanitize_filename,
            wikijs.fetch_page_content,
            log_debug
        )

        return render_template_string(
            load_template('export_results.html'),
            converted_files=converted_files,
            failed_files=failed_files,
            session_id=session_id,
            debug_logs=debug_logs,
            debug_data=debug_data
        )

    # GET request: Show the export interface
    pages, error = wikijs.fetch_pages(WIKIJS_URL, WIKIJS_TOKEN, limit=200, debug_logger=log_debug)

    return render_template_string(
        load_template('export.html'),
        pages=pages,
        error=error,
        output_formats=OUTPUT_FORMAT_MAPPING.keys(),
        wiki_url=WIKIJS_URL
    )

@app.route('/download_exported_file/<session_id>/<filename>', methods=['GET'])
def download_exported_file(session_id, filename):
    """Download a single exported file"""
    session_result_dir = os.path.join(RESULT_FOLDER, session_id)
    return send_from_directory(session_result_dir, filename, as_attachment=True)

@app.route('/download_exported_zip/<session_id>', methods=['GET'])
def download_exported_zip(session_id):
    """Download all exported files as a ZIP archive"""
    memory_file = export.create_exported_zip(session_id, RESULT_FOLDER)

    if not memory_file:
        flash('Fehler: Sitzungsdaten nicht gefunden')
        return redirect(url_for('export_route'))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    return send_file(
        memory_file,
        download_name=f'exported_wiki_pages_{timestamp}.zip',
        as_attachment=True
    )

if __name__ == '__main__':
    # Stelle sicher, dass das Templates-Verzeichnis existiert
    templates_dir = os.path.join(app.root_path, 'templates')
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
        print(f"Templates-Verzeichnis erstellt: {templates_dir}")

    # Ensure static files exist
    ensure_static_files_exist(app.root_path)

    app.run(debug=True, host='0.0.0.0', port=5000)
