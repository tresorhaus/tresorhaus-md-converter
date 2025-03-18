#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DocFlow - Markdown Converter for Wiki.js
Created by: Joachim Mild
Copyright (c) 2025 TresorHaus GmbH

Utility functions for DocFlow application
"""

import os
import re
from datetime import datetime
from pathlib import Path

def allowed_file(filename, allowed_extensions):
    """Überprüft, ob die Dateiendung erlaubt ist"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

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

def sanitize_filename(title):
    """
    Sanitizes a string to be used as a filename.
    - Transliterates German special characters (ä→ae, ö→oe, ü→ue, ß→ss)
    - Removes characters that are invalid in filenames
    - Ensures the result is a valid filename
    """
    if not title:
        return "untitled"

    # Transliterate German umlauts properly
    replacements = {
        'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss',
        'Ä': 'Ae', 'Ö': 'Oe', 'Ü': 'Ue',
        # Add other special characters as needed
    }

    for char, replacement in replacements.items():
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

def ensure_static_files_exist(app_root_path):
    """
    Ensures static directory and essential files exist
    """
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
