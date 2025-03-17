"""
DocFlow Hauptrouten
Enthält die Hauptrouten der Anwendung
"""
import os
import uuid
from flask import Blueprint, request, render_template_string, send_file, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
from models.session import Logger
from utils.file_utils import allowed_file, create_zip_file, cleanup_session
from services.converter_service import convert_to_markdown
from services.wikijs_service import upload_to_wikijs, test_wikijs_connection
from config import UPLOAD_FOLDER, RESULT_FOLDER, WIKIJS_URL, WIKIJS_TOKEN

main_bp = Blueprint('main', __name__)
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

@main_bp.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(current_app.root_path, 'static'),
        'favicon.ico',
        mimetype='image/x-icon'
    )

def process_uploads(files, session_id, upload_to_wiki=False, wiki_paths=None, wiki_titles=None, username=None, default_folder=None):
    """Verarbeitet hochgeladene Dateien und konvertiert sie zu Markdown"""
    logger.clear()  # Zurücksetzen der Debug-Logs für jede neue Sitzung
    upload_dir = os.path.join(UPLOAD_FOLDER, session_id)
    result_dir = os.path.join(RESULT_FOLDER, session_id)
    logger.log(f"Neue Upload-Verarbeitung gestartet. Session ID: {session_id}")
    logger.log(f"Benutzer: {username or 'Nicht angegeben'}")
    logger.log(f"Wiki.js-Upload aktiviert: {'Ja' if upload_to_wiki else 'Nein'}")

    # Sicherstellen, dass wiki_paths und wiki_titles Dictionaries sind
    if wiki_paths is None:
        wiki_paths = {}
    if wiki_titles is None:
        wiki_titles = {}

    logger.log(f"Wiki Titel: {wiki_titles}", "info")

    # Create directories if they don't exist
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        logger.log(f"Upload-Verzeichnis erstellt: {upload_dir}")
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)
        logger.log(f"Ergebnis-Verzeichnis erstellt: {result_dir}")

    converted_files = []
    failed_files = []
    wiki_urls = {}

    logger.log(f"{len(files)} Datei(en) für die Verarbeitung empfangen")

    for i, file in enumerate(files):
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            logger.log(f"Verarbeite Datei: {filename}")
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)
            logger.log(f"Datei gespeichert unter: {file_path}")

            output_filename = os.path.splitext(filename)[0] + '.md'
            output_path = os.path.join(result_dir, output_filename)
            logger.log(f"Starte Konvertierung zu: {output_filename}")

            if convert_to_markdown(file_path, output_path):
                logger.log(f"Konvertierung erfolgreich: {output_filename}", "success")
                converted_files.append(output_filename)

                if upload_to_wiki:
                    logger.log(f"Beginne Upload zu Wiki.js: {output_filename}", "api")
                    try:
                        with open(output_path, 'r', encoding='utf-8') as md_file:
                            content = md_file.read()
                            logger.log(f"Markdown-Datei gelesen: {len(content)} Zeichen", "api")

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
                                logger.log(f"Kein Titel angegeben, verwende automatisch sanitierten Dateinamen: '{sanitized_title}'", "info")

                            # Überprüfe, ob der Pfad oder Titel ungültige Zeichen enthält, bevor sie sanitiert werden
                            if custom_path and not sanitize_wikijs_path(custom_path) == custom_path:
                                logger.log(f"Warnung: Benutzerdefinierter Pfad '{custom_path}' enthält ungültige Zeichen und wird sanitiert.", "warning")
                            if custom_title and not sanitize_wikijs_title(custom_title) == custom_title:
                                logger.log(f"Warnung: Benutzerdefinierter Titel '{custom_title}' enthält ungültige Zeichen und wird sanitiert.", "warning")

                            logger.log(f"Benutzerdefinierter Pfad: {custom_path}", "info")
                            logger.log(f"Benutzerdefinierter Titel: {custom_title}", "info")

                            success, wiki_url = upload_to_wikijs(
                                content,
                                output_filename,
                                session_id,
                                custom_path=custom_path,
                                custom_title=custom_title,
                                username=username,
                                default_folder=default_folder,
                                log_debug=logger.log
                            )

                            if success:
                                wiki_urls[output_filename] = wiki_url
                                logger.log(f"Wiki.js Upload erfolgreich: {wiki_url}", "success")
                            else:
                                logger.log(f"Wiki.js Upload fehlgeschlagen für {output_filename}", "error")
                    except Exception as e:
                        logger.log(f"Fehler beim Lesen/Hochladen von {output_filename}: {str(e)}", "error")
            else:
                logger.log(f"Konvertierung fehlgeschlagen: {filename}", "error")
                failed_files.append(filename)
        else:
            if not file:
                logger.log("Leerer Datei-Eintrag übersprungen", "error")
            else:
                logger.log(f"Ungültiges Dateiformat: {file.filename}", "error")

    logger.log(f"Verarbeitung abgeschlossen: {len(converted_files)} konvertiert, {len(failed_files)} fehlgeschlagen")

    return converted_files, failed_files, wiki_urls

@main_bp.route('/', methods=['GET', 'POST'])
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
            load_template(current_app, 'results.html'),
            converted_files=converted_files,
            failed_files=failed_files,
            wiki_urls=wiki_urls,
            session_id=session_id,
            debug_logs=logger.get_logs(),
            wiki_requested=upload_to_wiki,
            wiki_url=WIKIJS_URL,
            api_token_exists=bool(WIKIJS_TOKEN)
        )

    return render_template_string(load_template(current_app, 'index.html'))

@main_bp.route('/download/<session_id>', methods=['GET'])
def download_results(session_id):
    result_dir = os.path.join(RESULT_FOLDER, session_id)
    memory_file = create_zip_file(session_id, result_dir)
    upload_dir = os.path.join(UPLOAD_FOLDER, session_id)
    cleanup_session(session_id, upload_dir, result_dir)

    return send_file(
        memory_file,
        download_name='converted_markdown_files.zip',
        as_attachment=True,
        mimetype='application/zip'
    )

@main_bp.route('/download_single/<session_id>/<filename>', methods=['GET'])
def download_single_file(session_id, filename):
    file_path = os.path.join(RESULT_FOLDER, session_id, filename)

    if not os.path.exists(file_path):
        flash('Datei nicht gefunden')
        return redirect(url_for('main.index'))

    return send_file(
        file_path,
        download_name=filename,
        as_attachment=True,
        mimetype='text/markdown'
    )

@main_bp.route('/test_wikijs_connection', methods=['POST'])
def test_connection():
    logger.clear()  # Zurücksetzen der Debug-Logs
    return test_wikijs_connection(logger.log)
