import os
import tempfile
import subprocess
import uuid
import shutil
from pathlib import Path
from flask import Flask, request, render_template_string, send_file, redirect, url_for, flash
from werkzeug.utils import secure_filename
import zipfile
import io

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
    </style>
</head>
<body>
    <div class="app-title">TresorHaus DocFlow</div>
    <div class="app-subtitle">Markdownkonverter</div>

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
            <div class="form-group">
                <button type="submit" class="btn">Konvertieren</button>
            </div>
        </form>
    </div>
</body>
</html>
'''

RESULT_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>TresorHaus DocFlow - Konvertierungsergebnisse</title>
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
        }
        .file-link:hover {
            background-color: #C4A962;
            color: white;
        }
        .error-list {
            color: #d9534f;
        }
        h1, h2 {
            color: #333;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="app-title">TresorHaus DocFlow</div>
    <div class="app-subtitle">Konvertierungsergebnisse</div>

    <div class="container">
        {% if converted_files %}
        <h2>Erfolgreich konvertierte Dateien:</h2>
        <ul class="file-list">
            {% for file in converted_files %}
            <li>
                {{ file }}
                <a href="{{ url_for('download_single_file', session_id=session_id, filename=file) }}" class="file-link">Herunterladen</a>
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
</body>
</html>
'''

# Stellen Sie sicher, dass die Verzeichnisse existieren
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Überprüft, ob die Dateiendung erlaubt ist"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_input_format(filename):
    """Bestimmt das Eingabeformat für Pandoc basierend auf der Dateiendung"""
    ext = filename.rsplit('.', 1)[1].lower()
    return FORMAT_MAPPING.get(ext, 'docx')

def convert_to_markdown(input_path, output_path):
    """Konvertiert eine Datei in Markdown mithilfe von pandoc"""
    input_format = get_input_format(input_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

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

def process_uploads(files, session_id):
    """Verarbeitet hochgeladene Dateien und konvertiert sie zu Markdown"""
    upload_dir = os.path.join(UPLOAD_FOLDER, session_id)
    result_dir = os.path.join(RESULT_FOLDER, session_id)

    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(result_dir, exist_ok=True)

    converted_files = []
    failed_files = []

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)

            output_filename = os.path.splitext(filename)[0] + '.md'
            output_path = os.path.join(result_dir, output_filename)

            if convert_to_markdown(file_path, output_path):
                converted_files.append(output_filename)
            else:
                failed_files.append(filename)

    return converted_files, failed_files

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

        if not files or files[0].filename == '':
            flash('Keine Dateien ausgewählt')
            return redirect(request.url)

        session_id = str(uuid.uuid4())
        converted_files, failed_files = process_uploads(files, session_id)

        if not converted_files and not failed_files:
            flash('Keine gültigen Dateien zum Konvertieren gefunden')
            return redirect(request.url)

        return render_template_string(RESULT_TEMPLATE,
                               converted_files=converted_files,
                               failed_files=failed_files,
                               session_id=session_id)

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
