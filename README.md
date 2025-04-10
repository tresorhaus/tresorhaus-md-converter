# DocFlow - Markdown Converter for Wiki.js

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

- **PowerPoint (PPTX) Konvertierung:**
  - Spezielle zweistufige Konvertierung für PowerPoint-Präsentationen
  - Wandelt PPTX-Dateien zunächst in HTML um (mit LibreOffice)
  - Konvertiert dann HTML in strukturiertes Markdown
  - Optimierte Fehlerbehandlung mit detaillierten Diagnosen

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

- **Zusätzliche Features:**
  - Verbindungstest zur Wiki.js API
  - Detaillierte Debug-Informationen
  - Automatische Sanitierung von Pfaden und Titeln für Wiki.js

## 🛠 Installation

### Voraussetzungen

- Debian 12 oder Ubuntu 22.04+
- Sudo-Rechte
- Internetverbindung
- Pandoc (wird automatisch installiert)
- Python 3.8+ (wird automatisch installiert, falls nicht vorhanden)
- LibreOffice (wird für PPTX-Konvertierung benötigt)

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
   - Wiki.js URL (z.B. http://wiki.example.com)
   - Wiki.js API Token
   - Wiki.js External URL (für Links, meist identisch mit Wiki.js URL)

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

4. **LibreOffice installieren (für PPTX-Konvertierung):**
   ```bash
   sudo apt-get install libreoffice
   ```

5. **Konfigurationsdatei erstellen (.env):**
   ```
   WIKIJS_URL=https://ihr-wiki.js-url
   WIKIJS_TOKEN=ihr-api-token
   WIKIJS_EXTERNAL_URL=https://ihre-externe-wiki-url
   ```

## 🔄 Aktualisierung

So aktualisieren Sie die Anwendung:

```bash
sudo ./update.sh
```

Das Update-Skript erstellt automatisch ein Backup und bietet die Möglichkeit, die Wiki.js-Konfiguration zu aktualisieren.

## 🗑 Deinstallation

So entfernen Sie die Anwendung:

```bash
sudo ./uninstall.sh
```

Das Deinstallationsskript bietet die Option, ein finales Backup zu erstellen, bevor alle Komponenten entfernt werden.

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
source venv/bin/activate  # Virtuelle Umgebung aktivieren
python app.py
```

### Dokumentkonvertierung (Dokument zu Wiki.js)

1. Navigieren Sie zu `http://localhost:5000`
2. Richten Sie optional Ihre Benutzereinstellungen ein
3. Wählen Sie eine oder mehrere Dateien aus
4. Aktivieren Sie "Direkt in Wiki.js hochladen", wenn gewünscht
5. Konfigurieren Sie Wiki.js-Pfade und Titel nach Bedarf
6. Klicken Sie auf "Konvertieren"
7. Auf der Ergebnisseite können Sie:
   - Alle Dateien als ZIP herunterladen
   - Einzelne Dateien herunterladen
   - Links zu hochgeladenen Wiki.js-Seiten öffnen
   - Debug-Informationen einsehen

#### PowerPoint (PPTX) Konvertierung

Bei der Konvertierung von PowerPoint-Präsentationen:
1. Stellen Sie sicher, dass LibreOffice installiert ist
2. Die App konvertiert PPTX-Dateien automatisch in zwei Schritten:
   - PPTX → HTML (mit LibreOffice)
   - HTML → Markdown (mit Pandoc)
3. Der Prozess läuft transparent im Hintergrund
4. Bei Fehlern werden detaillierte Diagnoseinformationen angezeigt

### Wiki.js Export (Wiki.js zu Dokument)

1. Navigieren Sie zu `http://localhost:5000/export`
2. Wählen Sie die gewünschten Ausgabeformate
3. Wählen Sie die zu exportierenden Wiki.js-Seiten
4. Klicken Sie auf "Exportieren"
5. Auf der Ergebnisseite können Sie:
   - Alle exportierten Dateien als ZIP herunterladen
   - Einzelne Dateien herunterladen
   - Debug-Informationen einsehen

## 🔧 Konfiguration

Die Anwendung kann über verschiedene Umgebungsvariablen konfiguriert werden:

- `WIKIJS_URL`: URL zur Wiki.js API (erforderlich für Wiki.js-Integration)
- `WIKIJS_TOKEN`: API-Schlüssel für Wiki.js (erforderlich für Wiki.js-Integration)
- `WIKIJS_EXTERNAL_URL`: Externe URL für Wiki.js (für korrekte Links, optional)
- `PORT`: Server-Port (Standard: 5000)
- `HOST`: Host-Adresse (Standard: 0.0.0.0)
- `DEBUG`: Debug-Modus (Standard: True)

Diese Konfigurationen können in der `.env`-Datei im Installationsverzeichnis angepasst werden.

## 📁 Projektstruktur
```
tresorhaus-docflow/
├── app.py                 # Hauptanwendung
├── wikijs.py              # Wiki.js API Integration
├── export.py              # Exportfunktionalität
├── utils.py               # Hilfsfunktionen
├── requirements.txt       # Python-Abhängigkeiten
├── install.sh             # Installationsskript
├── update.sh              # Update-Skript
├── uninstall.sh           # Deinstallationsskript
├── templates/             # HTML-Vorlagen
│   ├── index.html         # Hauptseite
│   ├── results.html       # Ergebnisseite
│   ├── export.html        # Export-Seite
│   └── export_results.html # Export-Ergebnisseite
├── static/                # Statische Dateien
│   ├── styles.css         # CSS-Stile
│   └── logo-tresorhaus.svg # Logo
├── README.md              # Dokumentation
└── LICENSE                # Lizenzinformationen
```

## 🔍 Fehlerbehebung

### Häufige Probleme und Lösungen

1. **PPTX-Konvertierung schlägt fehl:**
   - Stellen Sie sicher, dass LibreOffice installiert ist: `sudo apt-get install libreoffice`
   - Überprüfen Sie die Debug-Informationen für detaillierte Fehlermeldungen
   - Versuchen Sie, die PPTX-Datei in einem neueren PowerPoint-Format zu speichern

2. **Service startet nicht:**
   ```bash
   sudo journalctl -u tresorhaus-docflow -n 50
   ```

3. **Konvertierung schlägt fehl:**
   - Überprüfen Sie die Pandoc-Installation: `pandoc --version`
   - Überprüfen Sie die Dateiberechtigungen
   - Stellen Sie sicher, dass das Dateiformat unterstützt wird

4. **Webinterface nicht erreichbar:**
   - Überprüfen Sie die Firewall-Einstellungen
   - Überprüfen Sie den Service-Status: `sudo systemctl status tresorhaus-docflow`
   - Stellen Sie sicher, dass der konfigurierte Port nicht blockiert ist

5. **Wiki.js-Verbindungsprobleme:**
   - Überprüfen Sie die API-URL und den API-Schlüssel in der `.env`-Datei
   - Stellen Sie sicher, dass die Wiki.js-Instanz erreichbar ist
   - Überprüfen Sie die Berechtigungen des API-Schlüssels in Wiki.js

## 📮 Support

Bei Problemen oder Fragen:
1. Erstellen Sie ein Issue im GitHub Repository
2. Konsultieren Sie die [Dokumentation](https://github.com/tresorhaus/tresorhaus-docflow/wiki)
3. Kontaktieren Sie den Support unter [support@tresorhaus.de](mailto:support@tresorhaus.de)

## 📝 Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert - siehe die [LICENSE](LICENSE) Datei für Details.

## 👨‍💻 Autor

Entwickelt von Joachim Mild für TresorHaus GmbH

---

<p align="center">
  <strong>DocFlow</strong> - Effiziente Dokumentenkonvertierung und nahtlose Wiki.js-Integration
</p>
