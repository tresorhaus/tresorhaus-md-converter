"""
DocFlow
Ein Dokumentenkonverter für verschiedene Dateiformate zu Markdown mit Wiki.js Integration
Author: Joachim Mild
Created: 2025
Company: TresorHaus GmbH
"""
import os
import sys
import tempfile
from flask import Flask
from dotenv import load_dotenv

# Add the project root to the path to enable absolute imports
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Lade Umgebungsvariablen
# Versuche sowohl lokale .env als auch systemweite Umgebungsvariablen zu laden
env_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=env_path)

# Allgemeine Konfiguration
UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), 'doc_converter_uploads')
RESULT_FOLDER = os.path.join(tempfile.gettempdir(), 'doc_converter_results')
SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(24))

# Stellen Sie sicher, dass die Upload- und Result-Ordner existieren
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

# Erlaubte Dateiformate
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

# Ausgabeformat-Mapping
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

# Import routes after config is defined to avoid circular imports
from routes.main_routes import main_bp
from routes.export_routes import export_bp
from utils.file_utils import ensure_static_files_exist

def create_app():
    """Erstellt und konfiguriert die Flask-App"""
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.secret_key = SECRET_KEY

    # Stelle sicher, dass das Templates-Verzeichnis existiert
    templates_dir = os.path.join(app.root_path, 'templates')
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)
        print(f"Templates-Verzeichnis erstellt: {templates_dir}")

    # Stelle sicher, dass statische Dateien existieren
    ensure_static_files_exist(app.root_path)

    # Registriere Blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(export_bp)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
