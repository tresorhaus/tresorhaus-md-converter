# TresorHaus DocFlow

<p align="center">
  <img src="static/tresorhaus-logo.png" alt="TresorHaus Logo" width="300"/>
</p>

TresorHaus DocFlow ist ein leistungsstarker Dokumentenkonverter, der verschiedene Dokumentformate automatisch in Markdown umwandelt. Die Anwendung wurde entwickelt, um die Dokumentenverarbeitung zu optimieren und zu vereinfachen.

## 🚀 Features

- **Vielseitige Formatunterstützung:**
  - Microsoft Office (DOC, DOCX, PPT, PPTX)
  - OpenOffice/LibreOffice (ODT, ODP)
  - Markup & Text (HTML, RTF, LaTeX)
  - E-Books (EPUB)
  - Weitere Formate (RST, Textile, MediaWiki, DocBook, AsciiDoc, Org-mode)

- **Benutzerfreundliche Weboberfläche:**
  - Drag & Drop Upload
  - Mehrfachauswahl von Dateien
  - Übersichtliche Ergebnisanzeige

- **Flexible Ausgabeoptionen:**
  - Einzelne Markdown-Dateien herunterladen
  - Alle konvertierten Dateien als ZIP-Archiv
  - Beibehaltung der ursprünglichen Dateinamen

## 🛠 Installation

### Voraussetzungen

- Python 3.8 oder höher
- pip (Python Package Manager)
- Pandoc (Dokumentenkonverter)

### Schritt-für-Schritt Installation

1. **Repository klonen:**
   ```bash
   git clone https://github.com/tresorhaus/tresorhaus-docflow.git
   cd tresorhaus-docflow
   ```

2. **Python-Umgebung einrichten (optional, aber empfohlen):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Unter Linux/Mac
   # oder
   .\venv\Scripts\activate  # Unter Windows
   ```

3. **Abhängigkeiten installieren:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Pandoc installieren:**
   - Linux (Debian/Ubuntu):
     ```bash
     sudo apt-get install pandoc
     ```
   - macOS:
     ```bash
     brew install pandoc
     ```
   - Windows:
     - Besuchen Sie [pandoc.org/installing.html](https://pandoc.org/installing.html)
     - Laden Sie den Installer herunter und führen Sie ihn aus

## 🚦 Verwendung

1. **Server starten:**
   ```bash
   python app.py
   ```

2. **Zugriff auf die Anwendung:**
   - Öffnen Sie einen Webbrowser
   - Navigieren Sie zu `http://localhost:5000`

3. **Dokumente konvertieren:**
   - Wählen Sie eine oder mehrere Dateien aus
   - Klicken Sie auf "Konvertieren"
   - Laden Sie die konvertierten Markdown-Dateien herunter

## 🔧 Konfiguration

Die Anwendung kann über verschiedene Umgebungsvariablen konfiguriert werden:

- `PORT`: Server-Port (Standard: 5000)
- `HOST`: Host-Adresse (Standard: 0.0.0.0)
- `DEBUG`: Debug-Modus (Standard: True)

## 🔍 Fehlerbehebung

### Häufige Probleme und Lösungen

1. **Pandoc nicht gefunden:**
   - Stellen Sie sicher, dass Pandoc installiert ist
   - Überprüfen Sie, ob Pandoc im System-PATH verfügbar ist

2. **Dateien werden nicht konvertiert:**
   - Überprüfen Sie die Dateiberechtigungen
   - Stellen Sie sicher, dass das Format unterstützt wird

3. **Server startet nicht:**
   - Überprüfen Sie, ob der Port bereits belegt ist
   - Stellen Sie sicher, dass alle Abhängigkeiten installiert sind

## 🤝 Beitragen

Wir freuen uns über Beiträge! So können Sie helfen:

1. Fork des Repositories erstellen
2. Feature-Branch erstellen (`git checkout -b feature/AmazingFeature`)
3. Änderungen committen (`git commit -m 'Add some AmazingFeature'`)
4. Branch pushen (`git push origin feature/AmazingFeature`)
5. Pull Request erstellen

## 📝 Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert - siehe die [LICENSE](LICENSE) Datei für Details.

## 📮 Kontakt

TresorHaus GmbH - [Website](https://www.tresorhaus.de)

Projektlink: [https://github.com/tresorhaus/tresorhaus-docflow](https://github.com/tresorhaus/tresorhaus-docflow)

---

<p align="center">
  Entwickelt mit ❤️ von TresorHaus
</p>
