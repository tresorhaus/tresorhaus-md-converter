"""
DocFlow
Ein Dokumentenkonverter für verschiedene Dateiformate zu Markdown mit Wiki.js Integration
Author: Joachim Mild
Created: 2025
Company: TresorHaus GmbH
"""
import os
import sys
from flask import Flask

# Add the project root to the path to enable absolute imports
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Use absolute imports instead of relative imports
from config import SECRET_KEY
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
