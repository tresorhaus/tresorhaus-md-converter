"""
DocFlow Exportrouten
Enthält die Routen für den Export von Wiki.js-Seiten
"""
import os
import uuid
import io
import zipfile
from datetime import datetime
from flask import Blueprint, request, render_template_string, send_file, redirect, url_for, flash, send_from_directory, current_app
from models.session import Logger
from services.wikijs_service import fetch_wikijs_pages, fetch_wikijs_page_content
from services.converter_service import export_pages_to_formats
from utils.file_utils import sanitize_filename
from config import RESULT_FOLDER, OUTPUT_FORMAT_MAPPING, WIKIJS_URL

export_bp = Blueprint('export', __name__)
logger = Logger()

def load_template(app, filename):
    """Lädt ein Template aus einer Datei"""
    template_path = os.path.join(app.template_folder, filename)
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Fehler beim Laden des Templates {filename}: {e}")
        return f"<h1>Fehler beim Laden des Templates {filename}</h1>"

@export_bp.route('/export', methods=['GET', 'POST'])
def export():
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

        converted_files, failed_files = export_pages_to_formats(
            selected_pages,
            selected_formats,
            session_id,
            RESULT_FOLDER,
            lambda page_path: fetch_wikijs_page_content(page_path, logger.log),
            logger.log,
            sanitize_filename
        )

        return render_template_string(
            load_template(current_app, 'export_results.html'),
            converted_files=converted_files,
            failed_files=failed_files,
            session_id=session_id,
            debug_logs=logger.get_logs()
        )

    # GET request: Show the export interface
    pages, error = fetch_wikijs_pages(limit=200, log_debug=logger.log)

    return render_template_string(
        load_template(current_app, 'export.html'),
        pages=pages,
        error=error,
        output_formats=OUTPUT_FORMAT_MAPPING.keys(),
        wiki_url=WIKIJS_URL
    )

@export_bp.route('/download_exported_file/<session_id>/<filename>', methods=['GET'])
def download_exported_file(session_id, filename):
    """Download a single exported file"""
    session_result_dir = os.path.join(RESULT_FOLDER, session_id)
    return send_from_directory(session_result_dir, filename, as_attachment=True)

@export_bp.route('/download_exported_zip/<session_id>', methods=['GET'])
def download_exported_zip(session_id):
    """Download all exported files as a ZIP archive"""
    session_result_dir = os.path.join(RESULT_FOLDER, session_id)

    if not os.path.exists(session_result_dir):
        flash('Fehler: Sitzungsdaten nicht gefunden')
        return redirect(url_for('export.export'))

    memory_file = io.BytesIO()

    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(session_result_dir):
            for file in files:
                if file.endswith(('.md', '.docx', '.odt', '.rtf', '.pdf', '.html', '.tex', '.epub', '.pptx')):
                    zipf.write(
                        os.path.join(root, file),
                        os.path.basename(file)
                    )

    memory_file.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    return send_file(
        memory_file,
        attachment_filename=f'exported_wiki_pages_{timestamp}.zip',
        as_attachment=True
    )
