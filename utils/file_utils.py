"""
DocFlow Datei-Hilfsfunktionen
Enthält Funktionen für Dateioperationen
"""
import os
import shutil
import zipfile
import io
from werkzeug.utils import secure_filename
import re
from config import ALLOWED_EXTENSIONS, FORMAT_MAPPING

def allowed_file(filename):
    """Überprüft, ob die Dateiendung erlaubt ist"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_input_format(filename):
    """Bestimmt das Eingabeformat für Pandoc basierend auf der Dateiendung"""
    ext = filename.rsplit('.', 1)[1].lower()
    return FORMAT_MAPPING.get(ext, 'docx')

def create_zip_file(session_id, result_dir):
    """Erstellt eine ZIP-Datei mit allen konvertierten Markdown-Dateien"""
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(result_dir):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, result_dir)
                zf.write(file_path, rel_path)
    memory_file.seek(0)
    return memory_file

def cleanup_session(session_id, upload_dir, result_dir):
    """Bereinigt die temporären Dateien einer Session"""
    if os.path.exists(upload_dir):
        shutil.rmtree(upload_dir)
    if os.path.exists(result_dir):
        shutil.rmtree(result_dir)

def ensure_static_files_exist(app_root_path):
    """Stellt sicher, dass statische Dateien und Verzeichnisse existieren"""
    static_dir = os.path.join(app_root_path, 'static')
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
        print(f"Static directory created: {static_dir}")

    # Check if logo exists, if not create a placeholder
    logo_path = os.path.join(static_dir, 'logo-tresorhaus.svg')
    if not os.path.exists(logo_path):
        try:
            # Create a simple placeholder SVG logo
            with open(logo_path, 'w') as f:
                f.write('''<svg width="180" height="60" xmlns="http://www.w3.org/2000/svg">
                    <rect width="180" height="60" fill="#3498db"/>
                    <text x="90" y="35" font-family="Arial" font-size="18" text-anchor="middle" fill="white">TresorHaus GmbH</text>
                </svg>''')
            print(f"Created placeholder logo at {logo_path}")
        except Exception as e:
            print(f"Warning: Could not create logo file at {logo_path}. Error: {str(e)}")

    # Check if favicon exists, if not create a placeholder
    favicon_path = os.path.join(static_dir, 'favicon.ico')
    if not os.path.exists(favicon_path):
        print(f"Warning: Favicon file not found at {favicon_path}. Please add a favicon file.")

def sanitize_filename(title):
    """
    Sanitizes a title to be safely used as a filename
    - Converts umlauts properly (ä→ae, ö→oe, ü→ue, ß→ss)
    - Removes invalid filename characters
    - Ensures the result is a valid filename
    """
    if not title:
        return "untitled"

    # First handle German umlauts properly
    transliterations = {
        'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss',
        'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue',
        # Add other special characters as needed
    }
    for char, replacement in transliterations.items():
        title = title.replace(char, replacement)

    # Replace characters that are invalid in filenames
    # This is more restrictive than the Wiki.js path requirements
    invalid_chars = r'[<>:"/\\|?*\x00-\x1F]'
    title = re.sub(invalid_chars, '_', title)

    # Trim and ensure we don't have periods at start/end which can cause issues
    title = title.strip().strip('.')

    # If after all this we have an empty string, use a default
    if not title:
        return "untitled"

    return title
