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
import re

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

def sanitize_wikijs_path(path):
    """
    Sanitiert einen Wiki.js-Pfad, indem unerlaubte Zeichen entfernt oder ersetzt werden.
    - Leerzeichen werden durch Bindestriche ersetzt
    - Deutsche Umlaute werden transliteriert (ä → ae, ö → oe, ü → ue, ß → ss)
    - Punkte werden entfernt (außer als Dateierweiterungen)
    - Unsichere URL-Zeichen werden entfernt
    """
    if not path:
        return ""

    # Transliterate German special characters
    for old, new in [('ä', 'ae'), ('ö', 'oe'), ('ü', 'ue'), ('ß', 'ss'),
                      ('Ä', 'Ae'), ('Ö', 'Oe'), ('Ü', 'Ue')]:
        path = path.replace(old, new)

    # Teilen Sie den Pfad in Segmente auf
    segments = path.split('/')
    sanitized_segments = []

    for segment in segments:
        if segment:
            # Leerzeichen durch Bindestriche ersetzen
            segment = segment.replace(" ", "-")

            # Entferne oder ersetze unerlaubte Zeichen im Segment
            # Erlaubt: Alphanumerische Zeichen, Bindestriche, Unterstriche
            # Entferne unsichere URL-Zeichen wie Satzzeichen, Anführungszeichen usw.
            sanitized = re.sub(r'[^a-zA-Z0-9\-_]', '', segment)
            if sanitized:  # Nur hinzufügen, wenn nach der Bereinigung noch etwas übrig ist
                sanitized_segments.append(sanitized)

    # Pfad aus bereinigten Segmenten erstellen
    return '/'.join(sanitized_segments)

def sanitize_wikijs_title(title):
    """
    Sanitiert einen Wiki.js-Seitentitel, indem unerlaubte Zeichen entfernt oder ersetzt werden.
    - Leerzeichen werden beibehalten (erlaubt in Titeln)
    - Deutsche Umlaute werden transliteriert (ä → ae, ö → oe, ü → ue, ß → ss)
    - Punkte werden entfernt (außer als Dateierweiterungen)
    - Unsichere URL-Zeichen werden ersetzt oder entfernt
    """
    if not title:
        return ""

    # Transliterate German special characters
    for old, new in [('ä', 'ae'), ('ö', 'oe'), ('ü', 'ue'), ('ß', 'ss'),
                      ('Ä', 'Ae'), ('Ö', 'Oe'), ('Ü', 'Ue')]:
        title = title.replace(old, new)

    # Ersetze unsichere Zeichen, behalte aber Leerzeichen bei
    # Erlaubt: Alphanumerische Zeichen, Leerzeichen, Bindestriche, Unterstriche
    sanitized = re.sub(r'[^a-zA-Z0-9 \-_]', '', title)

    # Entferne führende und nachfolgende Leerzeichen
    sanitized = sanitized.strip()

    return sanitized

def clean_markdown_content(content):
    """
    Bereinigt Markdown von typischen Konvertierungsartefakten.
    Entfernt:
    - '>' am Beginn von Zeilen (Zitate, die keine sein sollten)
    - '> ' am Beginn von Zeilen
    - "**\" Sonderzeichen
    - "Seite X von X" Marker
    - Andere häufige Artefakte
    """
    # Entferne "Seite X von X" Marker mit unterschiedlichen Formatierungen
    content = re.sub(r'([Ss]eite\s+\d+\s+von\s+\d+)', '', content)

    # Entferne ">" und "> " am Beginn von Zeilen
    content = re.sub(r'^>\s*', '', content, flags=re.MULTILINE)

    # Entferne "**\" Artefakte
    content = re.sub(r'\*\*\\', '', content)

    # Entferne doppelte Leerzeilen
    while "\n\n\n" in content:
        content = content.replace("\n\n\n", "\n\n")

    # Entferne Leerzeilen am Anfang und Ende
    content = content.strip()

    return content

def upload_to_wikijs(content, title, session_id, custom_path=None, custom_title=None, username=None, default_folder=None):
    """Lädt eine Markdown-Datei in Wiki.js hoch"""
    if not WIKIJS_URL or not WIKIJS_TOKEN:
        log_debug("Wiki.js URL oder Token nicht konfiguriert", "error")
        return False, None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    date_with_time = datetime.now().strftime("%Y-%m-%d-%H%M")

    # Entferne .md Erweiterung aus dem Titel wenn vorhanden
    title_without_extension = title
    if title.lower().endswith('.md'):
        title_without_extension = title[:-3]

    # Verwende den benutzerdefinierten Titel, wenn angegeben, und sanitiere ihn
    if custom_title and custom_title.strip():
        original_title = custom_title.strip()
        title_without_extension = sanitize_wikijs_title(original_title)
        if original_title != title_without_extension:
            log_debug(f"Titel wurde sanitiert: '{original_title}' → '{title_without_extension}'", "info")
    else:
        title_without_extension = sanitize_wikijs_title(title_without_extension)

    # Für die Verwendung im Pfad: Ersetze Leerzeichen mit Bindestrichen
    title_for_path = title_without_extension.replace(" ", "-")

    # Berechnete Standardpfad mit Username und Datum
    safe_username = sanitize_wikijs_path(username) if username else "anonymous"
    base_folder = "DocFlow"  # Standard-Basis-Ordner
    default_path = f"{base_folder}/{safe_username}/{date_with_time}"
    sanitized_default_path = sanitize_wikijs_path(default_path)

    # Verwende den benutzerdefinierten Pfad, wenn angegeben, sonst den Standard-Pfad, und sanitiere ihn
    if custom_path and custom_path.strip():
        # Entferne führende und folgende Schrägstriche für Konsistenz
        original_path = custom_path.strip().strip('/')
        path = sanitize_wikijs_path(original_path)
        if original_path != path:
            log_debug(f"Pfad wurde sanitiert: '{original_path}' → '{path}'", "info")

        # Wenn ein benutzerdefinierter Pfad angegeben ist, verwende diesen direkt
        # Füge nur den Titel hinzu, wenn er nicht bereits Teil des Pfades ist
        if not path.endswith(f"/{title_for_path}") and not path.endswith(title_for_path):
            path = f"{path}/{title_for_path}"
            log_debug(f"Vollständiger Pfad mit Titel: {path}", "info")
    else:
        # Wenn kein benutzerdefinierter Pfad angegeben ist...
        if default_folder and default_folder.strip():
            # Wenn ein Standard-Ordner ausgewählt wurde, verwende diesen direkt ohne Username/Datum
            base_folder = sanitize_wikijs_path(default_folder.strip())
            path = f"{base_folder}/{title_for_path}"
            log_debug(f"Verwende Standard-Ordner direkt: {path}", "info")
        else:
            # Erstelle einen Standard-Pfad mit Benutzernamen und Datum+Uhrzeit
            path = f"{sanitized_default_path}/{title_for_path}"
            log_debug(f"Kein spezifischer Pfad angegeben. Verwende Standard-Pfad: {sanitized_default_path}/{title_for_path}", "info")
            log_debug(f"Info: Falls Sie keinen Pfad angeben, werden Ihre Dateien unter '{sanitized_default_path}/[Dateiname]' gespeichert.", "info")

    # Endgültige Prüfung und Sanitierung des Pfades
    path = sanitize_wikijs_path(path)

    # Bereinige den Markdown-Inhalt von typischen Konvertierungsartefakten
    cleaned_content = clean_markdown_content(content)
    log_debug(f"Markdown-Inhalt bereinigt. {len(content) - len(cleaned_content)} Zeichen entfernt.", "info")

    log_debug(f"Starte Upload zu Wiki.js: {title_without_extension}", "api")
    log_debug(f"Ziel-Pfad: {path}", "api")

    headers = {
        'Authorization': f'Bearer {WIKIJS_TOKEN}',
        'Content-Type': 'application/json'
    }

    # Aktualisierte GraphQL mutation basierend auf dem funktionierenden curl-Beispiel
    mutation = """
    mutation Page ($content: String!, $description: String!, $editor: String!, $isPublished: Boolean!, $isPrivate: Boolean!, $locale: String!, $path: String!, $tags: [String]!, $title: String!) {
      pages {
        create (content: $content, description: $description, editor: $editor, isPublished: $isPublished, isPrivate: $isPrivate, locale: $locale, path: $path, tags: $tags, title: $title) {
          responseResult {
            succeeded,
            errorCode,
            slug,
            message
          },
          page {
            id,
            path,
            title
          }
        }
      }
    }
    """

    variables = {
        'content': cleaned_content,  # Verwende den bereinigten Inhalt statt des Originals
        'description': f'Automatisch erstellt durch TresorHaus DocFlow am {timestamp}',
        'editor': 'markdown',
        'isPublished': True,
        'isPrivate': False,  # Hinzugefügt entsprechend dem curl-Beispiel
        'locale': 'de',
        'path': path,
        'tags': ['DocFlow', 'Automatisch'],
        'title': title_without_extension
    }

    # Erstelle die vollständige Request-Payload für Debug-Zwecke
    request_payload = {
        'query': mutation,
        'variables': variables
    }

    # Log vollständige Request-Details für Debugging
    log_debug(f"Wiki.js URL: {WIKIJS_URL}", "api")
    log_debug(f"GraphQL Mutation: {mutation.strip()}", "api")

    # Logge Variablen mit limitiertem Content für Übersichtlichkeit
    debug_variables = variables.copy()
    if len(content) > 200:
        debug_variables['content'] = content[:200] + '... [gekürzt]'
    log_debug(f"Variablen: {debug_variables}", "api")

    # Logge die ersten 200 Zeichen des Inhalts
    log_debug(f"Inhalt (gekürzt): {content[:200]}...", "api")

    # Logge die vollständige Länge des Inhalts
    log_debug(f"Gesamte Inhaltslänge: {len(content)} Zeichen", "api")

    try:
        log_debug(f"Sende Wiki.js Request an: {WIKIJS_URL}/graphql", "api")

        # POST mit json payload für die Mutation
        response = requests.post(
            f'{WIKIJS_URL}/graphql',
            headers=headers,
            json=request_payload
        )

        log_debug(f"Status Code: {response.status_code}", "api")

        # Versuchen, den Response-Body zu loggen
        try:
            response_text = response.text
            if len(response_text) > 500:
                log_debug(f"Response (gekürzt): {response_text[:500]}...", "api")
            else:
                log_debug(f"Response: {response_text}", "api")
        except:
            log_debug("Konnte Response-Body nicht lesen", "error")

        response.raise_for_status()
        data = response.json()

        if 'errors' in data:
            error_msg = str(data['errors'])
            log_debug(f"GraphQL Fehler: {error_msg}", "error")
            return False, None

        # Aktualisierte Überprüfung der Antwort basierend auf dem curl-Beispiel
        result = data.get('data', {}).get('pages', {}).get('create', {}).get('responseResult', {})
        if result.get('succeeded'):
            # Extrahiere die page_id und den tatsächlichen Pfad aus der Antwort
            page = data.get('data', {}).get('pages', {}).get('create', {}).get('page', {})
            page_id = page.get('id')
            actual_path = page.get('path')

            # Konstruiere die vollständige Wiki.js URL zur Seite mit der externen URL statt der API-URL
            wiki_url = f"{WIKIJS_EXTERNAL_URL}/{actual_path}"
            log_debug(f"Wiki.js Seite erfolgreich erstellt: {wiki_url} (ID: {page_id})", "success")
            return True, wiki_url
        else:
            error_message = result.get('message', 'Unbekannter Fehler')
            error_code = result.get('errorCode', 'Kein Code')
            log_debug(f"Wiki.js Fehler: {error_message} (Code: {error_code})", "error")
            return False, None

    except Exception as e:
        log_debug(f"Fehler beim Upload zu Wiki.js: {str(e)}", "error")
        log_debug(f"Exception Details: {type(e).__name__}", "error")
        import traceback
        log_debug(f"Traceback: {traceback.format_exc()}", "error")
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

                            success, wiki_url = upload_to_wikijs(
                                content,
                                output_filename,
                                session_id,
                                custom_path=custom_path,
                                custom_title=custom_title,
                                username=username,
                                default_folder=default_folder
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

def create_zip_file(session_id):
    """Erstellt eine ZIP-Datei mit allen konvertierten Markdown-Dateien"""
    result_dir = os.path.join(RESULT_FOLDER, session_id)
    memory_file = io.BytesIO()

    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(result_dir):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, result_dir)
                zf.write(file_path, rel_path)

    memory_file.seek(0)
    return memory_file

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
    memory_file = create_zip_file(session_id)
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

    if not WIKIJS_URL or not WIKIJS_TOKEN:
        log_debug("Wiki.js URL oder Token nicht konfiguriert", "error")
        return {'success': False, 'message': 'Wiki.js URL oder Token nicht konfiguriert'}

    # Test connection using pages list query
    try:
        # Use a simple query to list pages
        test_query = "{pages{list{id,title,path,contentType}}}"
        log_debug(f"Teste Wiki.js Verbindung zu: {WIKIJS_URL}", "api")

        # URL encode the query parameter
        import urllib.parse
        encoded_query = urllib.parse.quote(test_query)

        headers = {
            'Authorization': f'Bearer {WIKIJS_TOKEN}'
        }
        log_debug(f"Sende GET-Anfrage an: {WIKIJS_URL}/graphql/pages/list", "api")

        # Use GET request to the pages list endpoint with query as URL parameter
        response = requests.get(
            f'{WIKIJS_URL}/graphql/pages/list?query={encoded_query}',
            headers=headers
        )

        # Log detailed debug info
        log_debug(f"Status Code: {response.status_code}", "api")

        response.raise_for_status()
        data = response.json()

        if 'errors' in data:
            error_msg = data['errors'][0].get('message', 'Unbekannter GraphQL-Fehler')
            log_debug(f"API-Fehler: {error_msg}", "error")
            return {
                'success': False,
                'message': f"API-Fehler: {error_msg}\nBitte überprüfen Sie den API-Token."
            }

        # Check if we got a valid response with pages data
        if 'data' in data and 'pages' in data['data'] and 'list' in data['data']['pages']:
            page_count = len(data['data']['pages']['list'])
            log_debug(f"Verbindung erfolgreich! {page_count} Seiten gefunden.", "success")
            return {'success': True, 'message': f'Verbindung zu Wiki.js erfolgreich hergestellt! {page_count} Seiten gefunden.'}
        else:
            log_debug("Unerwartetes Antwortformat von Wiki.js", "error")
            return {
                'success': False,
                'message': 'Unerwartetes Antwortformat von Wiki.js. Bitte überprüfen Sie die API-Konfiguration.'
            }

    except requests.exceptions.ConnectionError:
        log_debug(f"Verbindungsfehler: Server nicht erreichbar unter {WIKIJS_URL}", "error")
        return {
            'success': False,
            'message': f'Verbindungsfehler: Server nicht erreichbar unter {WIKIJS_URL}'
        }
    except requests.exceptions.HTTPError as e:
        log_debug(f"HTTP-Fehler {e.response.status_code}: {e.response.text}", "error")
        if e.response.status_code == 401:
            return {
                'success': False,
                'message': 'Authentifizierungsfehler: Ungültiger API-Token'
            }
        elif e.response.status_code == 400:
            return {
                'success': False,
                'message': 'API-Fehler: Ungültige Anfrage. Bitte überprüfen Sie die Wiki.js-URL und den API-Token'
            }
        return {
            'success': False,
            'message': f'HTTP-Fehler {e.response.status_code}: {e.response.text}'
        }
    except Exception as e:
        log_debug(f"Unerwarteter Fehler: {str(e)}", "error")
        return {
            'success': False,
            'message': f'Unerwarteter Fehler: {str(e)}\nBitte überprüfen Sie die Konsole für weitere Details.'
        }

@app.route('/get_wikijs_directories', methods=['GET'])
def get_wikijs_directories():
    """Retrieves a list of all directories from Wiki.js"""
    if not WIKIJS_URL or not WIKIJS_TOKEN:
        return {'success': False, 'message': 'Wiki.js URL oder Token nicht konfiguriert', 'directories': []}

    try:
        # GraphQL query to get all pages which will be used to extract unique directories
        query = """
        {
          pages {
            list {
              path
            }
          }
        }
        """

        headers = {
            'Authorization': f'Bearer {WIKIJS_TOKEN}',
            'Content-Type': 'application/json'
        }

        response = requests.post(
            f'{WIKIJS_URL}/graphql',
            headers=headers,
            json={'query': query}
        )

        response.raise_for_status()
        data = response.json()

        if 'errors' in data:
            error_msg = str(data['errors'])
            return {'success': False, 'message': f'GraphQL Error: {error_msg}', 'directories': []}

        # Extract all paths from the pages
        pages = data.get('data', {}).get('pages', {}).get('list', [])
        all_paths = [page['path'] for page in pages if 'path' in page]

        # Extract unique directories from paths
        directories = set()
        for path in all_paths:
            # Split the path and reconstruct directories
            parts = path.split('/')
            for i in range(1, len(parts)):
                directories.add('/'.join(parts[:i]))

        # Convert set to list and sort
        directory_list = sorted(list(directories))

        # Add root directory if it doesn't exist
        if '' not in directory_list:
            directory_list.insert(0, '')

        return {'success': True, 'directories': directory_list}

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        return {
            'success': False,
            'message': f'Error fetching directories: {str(e)}',
            'error_details': error_trace,
            'directories': []
        }

# Ensure static directory and essential files exist
def ensure_static_files_exist():
    static_dir = os.path.join(app.root_path, 'static')
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
        print(f"Static directory created: {static_dir}")

    # Check if logo exists, if not create a placeholder
    logo_path = os.path.join(static_dir, 'tresorhaus-logo.png')
    if not os.path.exists(logo_path):
        print(f"Warning: Logo file not found at {logo_path}. Please add a logo file.")

    # Check if favicon exists, if not create a placeholder
    favicon_path = os.path.join(static_dir, 'favicon.ico')
    if not os.path.exists(favicon_path):
        print(f"Warning: Favicon file not found at {favicon_path}. Please add a favicon file.")

if __name__ == '__main__':
    # Stelle sicher, dass das Templates-Verzeichnis existiert
    templates_dir = os.path.join(app.root_path, 'templates')
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
        print(f"Templates-Verzeichnis erstellt: {templates_dir}")

    # Ensure static files exist
    ensure_static_files_exist()

    app.run(debug=True, host='0.0.0.0', port=5000)
