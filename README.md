# TresorHaus DocFlow

<p align="center">
  <img src="static/tresorhaus-logo.png" alt="TresorHaus Logo" width="300"/>
</p>

TresorHaus DocFlow ist ein leistungsstarker Dokumentenkonverter, der verschiedene Dokumentformate automatisch in Markdown umwandelt. Die Anwendung wurde entwickelt, um die Dokumentenverarbeitung zu optimieren und zu vereinfachen.

## Author
Entwickelt von Joachim Mild für TresorHaus GmbH

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

- Debian 12
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

## 🔄 Update

Um die Anwendung zu aktualisieren:

```bash
sudo ./update.sh
```

## 🗑 Deinstallation

Um die Anwendung zu entfernen:

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

## 📁 Projektstruktur
```
tresorhaus-docflow/
├── app.py                 # Hauptanwendung
├── requirements.txt       # Python-Abhängigkeiten
├── install.sh            # Installationsskript
├── update.sh             # Update-Skript
├── uninstall.sh          # Deinstallationsskript
├── README.md             # Dokumentation
├── static/               # Statische Dateien
│   └── tresorhaus-logo.png
└── LICENSE               # Lizenzinformationen
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

3. **Webinterface nicht erreichbar:**
   - Überprüfen Sie die Firewall-Einstellungen
   - Überprüfen Sie den Service-Status

## 📮 Support

Bei Problemen oder Fragen:
1. Erstellen Sie ein Issue im GitHub Repository
2. Kontaktieren Sie den Support unter [support@tresorhaus.de](mailto:support@tresorhaus.de)

## 📝 Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert - siehe die [LICENSE](LICENSE) Datei für Details.

---

<p align="center">
  Entwickelt mit ❤️ von Joachim Mild für TresorHaus
</p>
