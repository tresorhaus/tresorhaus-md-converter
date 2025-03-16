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

        <script>
        document.getElementById('test-api').addEventListener('click', async () => {
            const resultSpan = document.getElementById('api-test-result');
            resultSpan.textContent = 'Teste Verbindung...';
            resultSpan.style.color = 'gray';

            try {
                const response = await fetch('/test_wikijs_connection', {
                    method: 'POST',
                });
                const data = await response.json();

                resultSpan.textContent = data.message;
                resultSpan.style.color = data.success ? '#4CAF50' : '#f44336';
            } catch (error) {
                resultSpan.textContent = 'Fehler beim Testen der Verbindung';
                resultSpan.style.color = '#f44336';
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
    </div>

    <a href="{{ url_for('index') }}" class="btn">Zurück zur Startseite</a>

    <div class="author-info">
        Entwickelt von Joachim Mild für TresorHaus GmbH © 2025
    </div>
</body>
</html>
'''

# Favicon Route
@app.route('/favicon.ico')
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

def upload_to_wikijs(content, title, session_id):
    """Lädt eine Markdown-Datei in Wiki.js hoch"""
    if not WIKIJS_URL or not WIKIJS_TOKEN:
        print("Wiki.js URL oder Token nicht konfiguriert")
        return False, None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"DocFlow/{session_id}_{timestamp}/{title}"

    headers = {
        'Authorization': f'Bearer {WIKIJS_TOKEN}',
        'Content-Type': 'application/json'
    }

    # GraphQL mutation für das Erstellen einer neuen Seite
    mutation = """
    mutation CreatePage(
        $content: String!
        $description: String
        $editor: String!
        $isPrivate: Boolean!
        $isPublished: Boolean!
        $locale: String!
        $path: String!
        $tags: [String]!
        $title: String!
    ) {
        pages {
            create(
                content: $content
                description: $description
                editor: $editor
                isPrivate: $isPrivate
                isPublished: $isPublished
                locale: $locale
                path: $path
                tags: $tags
                title: $title
            ) {
                responseResult {
                    succeeded
                    errorCode
                    slug
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
        'isPrivate': False,
        'isPublished': True,
        'locale': 'de',
        'path': path,
        'tags': ['DocFlow', 'Automatisch'],
        'title': title
    }

    try:
        # For mutations, we need to use POST with json payload
        response = requests.post(
            f'{WIKIJS_URL}/graphql',
            headers=headers,
            json={
                'query': mutation,
                'variables': variables
            }
        )
        response.raise_for_status()
        data = response.json()

        if 'errors' in data:
            print(f"GraphQL Fehler: {data['errors']}")
            return False, None

        result = data.get('data', {}).get('pages', {}).get('create', {}).get('responseResult', {})
        if result.get('succeeded'):
            return True, f"{WIKIJS_URL}/{path}"
        else:
            print(f"Wiki.js Fehler: {result.get('message')}")
            return False, None

    except Exception as e:
        print(f"Fehler beim Upload zu Wiki.js: {str(e)}")
        return False, None

def convert_to_markdown(input_path, output_path):
    """Konvertiert eine Datei in Markdown mithilfe von pandoc"""
    input_format = get_input_format(input_path)
    os.makedirs(os.path.dirname(output_path), exist_okay=True)

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
    upload_dir = os.path.join(UPLOAD_FOLDER, session_id)
    result_dir = os.path.join(RESULT_FOLDER, session_id)

    os.makedirs(upload_dir, exist_okay=True)
    os.makedirs(result_dir, exist_okay=True)

    converted_files = []
    failed_files = []
    wiki_urls = {}

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)

            output_filename = os.path.splitext(filename)[0] + '.md'
            output_path = os.path.join(result_dir, output_filename)

            if convert_to_markdown(file_path, output_path):
                converted_files.append(output_filename)

                if upload_to_wiki:
                    with open(output_path, 'r', encoding='utf-8') as md_file:
                        content = md_file.read()
                        success, wiki_url = upload_to_wikijs(content, output_filename, session_id)
                        if success:
                            wiki_urls[output_filename] = wiki_url
            else:
                failed_files.append(filename)

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
        converted_files, failed_files, wiki_urls = process_uploads(files, session_id, upload_to_wiki)

        if not converted_files and not failed_files:
            flash('Keine gültigen Dateien zum Konvertieren gefunden')
            return redirect(request.url)

        return render_template_string(
            RESULT_TEMPLATE,
            converted_files=converted_files,
            failed_files=failed_files,
            wiki_urls=wiki_urls,
            session_id=session_id
        )

    return render_template_string(INDEX_TEMPLATE)

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
    if not WIKIJS_URL or not WIKIJS_TOKEN:
        return {'success': False, 'message': 'Wiki.js URL oder Token nicht konfiguriert'}

    # Test connection using pages list query
    try:
        # Use a simple query to list pages
        test_query = "{pages{list{id,title,path,contentType}}}"

        # URL encode the query parameter
        import urllib.parse
        encoded_query = urllib.parse.quote(test_query)

        headers = {
            'Authorization': f'Bearer {WIKIJS_TOKEN}'
        }

        # Use GET request to the pages list endpoint with query as URL parameter
        response = requests.get(
            f'{WIKIJS_URL}/graphql/pages/list?query={encoded_query}',
            headers=headers
        )

        # Print detailed debug info
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        print(f"Response Content: {response.text}")

        response.raise_for_status()
        data = response.json()

        if 'errors' in data:
            error_msg = data['errors'][0].get('message', 'Unbekannter GraphQL-Fehler')
            return {
                'success': False,
                'message': f"API-Fehler: {error_msg}\nBitte überprüfen Sie den API-Token."
            }

        # Check if we got a valid response with pages data
        if 'data' in data and 'pages' in data['data'] and 'list' in data['data']['pages']:
            return {'success': True, 'message': 'Verbindung zu Wiki.js erfolgreich hergestellt!'}
        else:
            return {
                'success': False,
                'message': 'Unerwartetes Antwortformat von Wiki.js. Bitte überprüfen Sie die API-Konfiguration.'
            }

    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'message': f'Verbindungsfehler: Server nicht erreichbar unter {WIKIJS_URL}'
        }
    except requests.exceptions.HTTPError as e:
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
        return {
            'success': False,
            'message': f'Unerwarteter Fehler: {str(e)}\nBitte überprüfen Sie die Konsole für weitere Details.'
        }

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
