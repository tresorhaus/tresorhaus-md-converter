# DocFlow - Markdown Konverter für Wiki.js

<p align="center">
  <img src="static/logo-tresorhaus.svg" alt="TresorHaus Logo" width="300"/>
</p>

DocFlow ist ein leistungsstarker Dokumentenkonverter, der verschiedene Dokumentformate automatisch in Markdown umwandelt und nahtlos mit Wiki.js integriert. Die Anwendung optimiert die Dokumentenverwaltung und vereinfacht den Workflow zwischen verschiedenen Systemen.

## 🚀 Funktionen

### Dokumentkonvertierung
- **Umfangreiche Formatunterstützung:**
  - Microsoft Office (DOC, DOCX, PPT, PPTX)
  - OpenOffice/LibreOffice (ODT, ODP)
  - Markup & Text (HTML, RTF, LaTeX)
  - E-Books (EPUB)
  - Weitere Formate (RST, Textile, MediaWiki, DocBook, AsciiDoc, Org-mode)

- **KI-gestützte Dokumentenkonvertierung:**
  - Unterstützung für verschiedene Dateiformate (PPTX, PPT, DOCX, DOC)
  - Intelligente Konvertierung mit Claude 3.7 Sonnet API
  - Präzise Inhaltsübertragung und Strukturerhaltung
  - Fortschrittliche Erkennung von Tabellen, Diagrammen und komplexen Layouts
  - Hochwertige Markdown-Ausgabe mit optimaler Formatierung

- **Intuitive Weboberfläche:**
  - Drag & Drop Upload
  - Mehrfachauswahl von Dateien
  - Übersichtliche Ergebnisanzeige
  - Benutzerspezifische Einstellungen
  - Dark Mode für angenehmes Arbeiten

- **Flexible Ausgabeoptionen:**
  - Einzelne Markdown-Dateien herunterladen
  - Alle konvertierten Dateien als ZIP-Archiv
  - Beibehaltung der ursprünglichen Dateinamen

### Wiki.js Integration
- **Dokument zu Wiki.js:**
  - Direktes Hochladen konvertierter Dokumente in Wiki.js
  - Verzeichnisstruktur-Browser für einfache Navigation
  - Anpassbare Pfade für jedes Dokument
  - Benutzerdefinierte Titel für Wiki.js-Seiten
  - Automatische Bereinigung von Konvertierungsartefakten

- **Wiki.js zu Dokument:**
  - Export von Wiki.js-Seiten in verschiedene Dokumentformate
  - Unterstützte Formate: DOCX, ODT, RTF, PDF, HTML, TEX, EPUB, PPTX
  - Filterfunktion für Wiki.js-Seiten
  - Mehrere Seiten gleichzeitig exportieren
  - ZIP-Download aller exportierten Dateien

## 🛠 Installation

### Voraussetzungen

- Debian 12 oder Ubuntu 22.04+
- Sudo-Rechte
- Internetverbindung
- Pandoc (wird automatisch installiert)
- Python 3.8+ (wird automatisch installiert)
- Claude API Key (für die KI-gestützte Dokumentenkonvertierung)

### Automatische Installation

1. **Repository klonen:**
   ```bash
   git clone https://github.com/tresorhaus/tresorhaus-docflow.git
   cd tresorhaus-docflow
   ```

2. **Installationsskript ausführen:**
   ```bash
   chmod +x install.sh
   sudo ./install.sh
   ```

   Während der Installation werden Sie nach folgenden Informationen gefragt:
   - Wiki.js URL
   - Wiki.js API Token
   - Wiki.js External URL
   - Claude API Key
   - Claude Dateitypen (Standard: pptx,ppt,docx,doc)

### Manuelle Installation

1. **Python-Umgebung einrichten:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Abhängigkeiten installieren:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Pandoc installieren:**
   ```bash
   sudo apt-get install pandoc
   ```

4. **Konfigurationsdatei erstellen (.env):**
   ```
   WIKIJS_URL=https://ihr-wiki.js-url
   WIKIJS_TOKEN=ihr-api-token
   WIKIJS_EXTERNAL_URL=https://ihre-externe-wiki-url
   CLAUDE_API_KEY=ihr-claude-api-key
   CLAUDE_FILE_TYPES=pptx,ppt,docx,doc
   ```

## 🚦 Verwendung

### Dokumentkonvertierung

1. Navigieren Sie zu `http://localhost:5000`
2. Richten Sie optional Ihre Benutzereinstellungen ein
3. Wählen Sie eine oder mehrere Dateien aus
4. Aktivieren Sie "Direkt in Wiki.js hochladen", wenn gewünscht
5. Klicken Sie auf "Konvertieren"

#### KI-gestützte Dokumentenkonvertierung

Bei der Konvertierung von Dokumenten mit Claude AI:
1. Stellen Sie sicher, dass ein gültiger Claude API Key konfiguriert ist
2. Die App konvertiert Dateien automatisch unter Einsatz der Claude KI:
   - Dokumente werden zur Claude API gesendet
   - Die KI analysiert und interpretiert den Inhalt intelligent
   - Ergebnis ist ein präzise strukturiertes Markdown-Dokument
3. Der Prozess läuft transparent im Hintergrund
4. Bei Fehlern werden detaillierte Diagnoseinformationen angezeigt

## 🔧 Konfiguration

Die Anwendung kann über verschiedene Umgebungsvariablen konfiguriert werden:

- `WIKIJS_URL`: URL zur Wiki.js API (erforderlich für Wiki.js-Integration)
- `WIKIJS_TOKEN`: API-Schlüssel für Wiki.js (erforderlich für Wiki.js-Integration)
- `WIKIJS_EXTERNAL_URL`: Externe URL für Wiki.js (für korrekte Links, optional)
- `CLAUDE_API_KEY`: API-Schlüssel für Claude (erforderlich für KI-gestützte Konvertierung)
- `CLAUDE_FILE_TYPES`: Kommaseparierte Liste von Dateiformaten, die mit Claude konvertiert werden sollen (Standard: pptx,ppt,docx,doc)

Diese Konfigurationen können in der `.env`-Datei im Installationsverzeichnis angepasst werden.

## 🔍 Fehlerbehebung

### Häufige Probleme und Lösungen

1. **Claude API Fehler bei der Konvertierung:**
   - Überprüfen Sie, ob der Claude API Key korrekt in der .env-Datei konfiguriert ist
   - Stellen Sie sicher, dass Sie über ausreichend API-Guthaben verfügen
   - Prüfen Sie die Internetverbindung, die API-Calls erfordern eine stabile Verbindung
   - Bei großen Dokumenten kann die Dateigrößenbeschränkung der API überschritten werden

2. **Service startet nicht:**
   ```bash
   sudo systemctl status tresorhaus-docflow
   sudo journalctl -u tresorhaus-docflow -n 50
   ```

## 👨‍💻 Autor

Entwickelt von Joachim Mild für TresorHaus GmbH

---

<p align="center">
  <strong>DocFlow</strong> - Effiziente Dokumentenkonvertierung und nahtlose Wiki.js-Integration
</p> 