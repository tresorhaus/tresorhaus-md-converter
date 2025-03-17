"""
DocFlow Markdown-Hilfsfunktionen
Enthält Funktionen für Markdown-Verarbeitung
"""
import re

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
