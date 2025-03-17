"""
DocFlow Konfigurationsdatei
Enthält alle Konfigurationsvariablen und Einstellungen
"""
import os
import tempfile
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

# Allgemeine Konfiguration
UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), 'doc_converter_uploads')
RESULT_FOLDER = os.path.join(tempfile.gettempdir(), 'doc_converter_results')
SECRET_KEY = os.urandom(24)

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
