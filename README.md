# DocFlow

<p align="center">
  <img src="static/logo-tresorhaus.svg" alt="TresorHaus Logo" width="300"/>
</p>

 DocFlow ist ein leistungsstarker Dokumentenkonverter, der verschiedene Dokumentformate automatisch in Markdown umwandelt. Die Anwendung wurde speziell entwickelt, um die Dokumentenverwaltung zu optimieren und den Workflow zwischen verschiedenen Systemen zu vereinfachen.

## Autor
Entwickelt von Joachim Mild für TresorHaus GmbH

## 🚀 Funktionen

- **Umfangreiche Formatunterstützung:**
  - Microsoft Office (DOC, DOCX, PPT, PPTX)
  - OpenOffice/LibreOffice (ODT, ODP)
  - Markup & Text (HTML, RTF, LaTeX)
  - E-Books (EPUB)
  - Weitere Formate (RST, Textile, MediaWiki, DocBook, AsciiDoc, Org-mode)

- **Intuitive Weboberfläche:**
  - Drag & Drop Upload
  - Mehrfachauswahl von Dateien
  - Übersichtliche Ergebnisanzeige
  - Benutzerspezifische Einstellungen

- **Flexible Ausgabeoptionen:**
  - Einzelne Markdown-Dateien herunterladen
  - Alle konvertierten Dateien als ZIP-Archiv
  - Beibehaltung der ursprünglichen Dateinamen

- **Wiki.js Integration:**
  - Direktes Hochladen in Wiki.js
  - Verzeichnisstruktur-Browser
  - Anpassbare Pfade für jedes Dokument
  - Verbindungstest zur Wiki.js API

## 🛠 Installation

### Voraussetzungen

- Debian 12 oder Ubuntu 22.04+
- Sudo-Rechte
- Internetverbindung

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

## 🔄 Aktualisierung

So aktualisieren Sie die Anwendung:

```bash
sudo ./update.sh
```

## 🗑 Deinstallation

So entfernen Sie die Anwendung:

```bash
sudo ./uninstall.sh
```

## 🚦 Verwendung

### Als Service
Nach der Installation ist die Anwendung automatisch als Service eingerichtet und unter `http://localhost:5000` erreichbar.

### Service-Verwaltung
```bash
# Status anzeigen
sudo systemctl status tresorhaus-docflow

# Service neustarten
sudo systemctl restart tresorhaus-docflow

# Logs anzeigen
sudo journalctl -u tresorhaus-docflow -f
```

### Manuelle Ausführung
```bash
python app.py
```

## 🔧 Konfiguration

Die Anwendung kann über verschiedene Umgebungsvariablen konfiguriert werden:

- `PORT`: Server-Port (Standard: 5000)
- `HOST`: Host-Adresse (Standard: 0.0.0.0)
- `DEBUG`: Debug-Modus (Standard: True)
- `WIKI_API_URL`: URL zur Wiki.js API
- `WIKI_API_KEY`: API-Schlüssel für Wiki.js

## 📁 Projektstruktur
```
tresorhaus-docflow/
├── app.py                 # Hauptanwendung
├── requirements.txt       # Python-Abhängigkeiten
├── install.sh             # Installationsskript
├── update.sh              # Update-Skript
├── uninstall.sh           # Deinstallationsskript
├── templates/             # HTML-Vorlagen
│   ├── index.html         # Hauptseite
│   └── results.html       # Ergebnisseite
├── static/                # Statische Dateien
│   ├── styles.css         # CSS-Stile
│   └── logo-tesorhaus.svg # Logo
├── README.md              # Dokumentation
└── LICENSE                # Lizenzinformationen
```

## 🔍 Fehlerbehebung

### Häufige Probleme und Lösungen

1. **Service startet nicht:**
   ```bash
   sudo journalctl -u tresorhaus-docflow -n 50
   ```

2. **Konvertierung schlägt fehl:**
   - Überprüfen Sie die Pandoc-Installation
   - Überprüfen Sie die Dateiberechtigungen
   - Stellen Sie sicher, dass das Dateiformat unterstützt wird

3. **Webinterface nicht erreichbar:**
   - Überprüfen Sie die Firewall-Einstellungen
   - Überprüfen Sie den Service-Status
   - Stellen Sie sicher, dass der konfigurierte Port nicht blockiert ist

4. **Wiki.js-Verbindungsprobleme:**
   - Überprüfen Sie die API-URL und den API-Schlüssel
   - Stellen Sie sicher, dass die Wiki.js-Instanz erreichbar ist
   - Überprüfen Sie die Berechtigungen des API-Schlüssels in Wiki.js

## 📮 Support

Bei Problemen oder Fragen:
1. Erstellen Sie ein Issue im GitHub Repository
2. Konsultieren Sie die [Dokumentation](https://github.com/tresorhaus/tresorhaus-docflow/wiki)
3. Kontaktieren Sie den Support unter [support@tresorhaus.de](mailto:support@tresorhaus.de)

## 📝 Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert - siehe die [LICENSE](LICENSE) Datei für Details.

---

<p align="center">
  Entwickelt mit ❤️ von Joachim Mild für TresorHaus
</p>
