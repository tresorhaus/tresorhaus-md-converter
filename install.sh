#!/bin/bash

#  DocFlow Installer
# Author: Joachim Mild
# For Debian 12

# Farben für Ausgaben
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging-Funktion
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

# Prüfen, ob Script als root läuft
if [ "$EUID" -ne 0 ]; then
    error "Bitte als root ausführen (sudo ./install.sh)"
    exit 1
fi

# Installationsverzeichnis
INSTALL_DIR="/opt/tresorhaus-docflow"
VENV_DIR="$INSTALL_DIR/venv"
SERVICE_NAME="tresorhaus-docflow"
SERVICE_USER="docflow"
TEMPLATES_DIR="$INSTALL_DIR/templates"

# Wiki.js Konfiguration abfragen
read -p "Wiki.js URL eingeben (z.B. http://wiki.example.com): " WIKIJS_URL
read -p "Wiki.js API Token eingeben: " WIKIJS_TOKEN
read -p "Wiki.js External URL eingeben (für Links, meist identisch mit Wiki.js URL): " WIKIJS_EXTERNAL_URL

# Wenn keine externe URL angegeben wurde, die normale URL verwenden
if [ -z "$WIKIJS_EXTERNAL_URL" ]; then
    WIKIJS_EXTERNAL_URL="$WIKIJS_URL"
    warning "Keine externe URL angegeben. Verwende Wiki.js URL als externe URL."
fi

# SystemD Service Definition
SERVICE_CONTENT="[Unit]
Description= DocFlow Service
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$VENV_DIR/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=$VENV_DIR/bin/python $INSTALL_DIR/app.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target"

# Benötigte Pakete installieren
log "Installiere benötigte System-Pakete..."
apt-get update
apt-get install -y python3-venv python3-pip pandoc

# Benutzer erstellen
log "Erstelle Service-Benutzer..."
if id "$SERVICE_USER" &>/dev/null; then
    warning "Benutzer $SERVICE_USER existiert bereits"
else
    useradd -r -s /bin/false $SERVICE_USER
fi

# Installationsverzeichnis erstellen
log "Erstelle Installationsverzeichnis..."
mkdir -p $INSTALL_DIR
mkdir -p $INSTALL_DIR/static
mkdir -p $TEMPLATES_DIR

# Kopiere Anwendungsdateien
log "Kopiere Anwendungsdateien..."
cp app.py $INSTALL_DIR/
cp utils.py $INSTALL_DIR/  # Kopieren der neuen utils.py Datei
cp -r static/* $INSTALL_DIR/static/ 2>/dev/null || warning "Keine statischen Dateien gefunden."

# Kopiere Template-Dateien, falls vorhanden
log "Kopiere Template-Dateien..."
if [ -d "templates" ]; then
    # Prüfen der neuen Export-Funktionalitäts-Dateien
    if [ -f "templates/export.html" ] && [ -f "templates/export_results.html" ]; then
        log "Neue Export-Funktionalität erkannt."
    else
        warning "Die neuen Export-Template-Dateien fehlen. Die Export-Funktionalität könnte beeinträchtigt sein."
    fi
    cp -r templates/* $TEMPLATES_DIR/
else
    warning "Keine Template-Dateien gefunden. Erstelle leeres Template-Verzeichnis."
fi

# Erstelle .env Datei
log "Erstelle .env Datei..."
cat > $INSTALL_DIR/.env << EOF
WIKIJS_URL=$WIKIJS_URL
WIKIJS_TOKEN=$WIKIJS_TOKEN
WIKIJS_EXTERNAL_URL=$WIKIJS_EXTERNAL_URL
EOF

# Erstelle requirements.txt falls nicht vorhanden
if [ ! -f "requirements.txt" ]; then
    log "Erstelle requirements.txt..."
    cat > requirements.txt << EOF
Flask==2.3.3
Werkzeug==2.3.7
requests==2.31.0
python-dotenv==1.0.0
EOF
fi

# Python Virtual Environment erstellen
log "Erstelle Python Virtual Environment..."
python3 -m venv $VENV_DIR

# Abhängigkeiten installieren
log "Installiere Python-Abhängigkeiten..."
$VENV_DIR/bin/pip install --upgrade pip
$VENV_DIR/bin/pip install -r requirements.txt

# Berechtigungen setzen
log "Setze Berechtigungen..."
chown -R $SERVICE_USER:$SERVICE_USER $INSTALL_DIR
chmod -R 755 $INSTALL_DIR
chmod 600 $INSTALL_DIR/.env
chmod -R 755 $TEMPLATES_DIR

# SystemD Service erstellen
log "Erstelle SystemD Service..."
echo "$SERVICE_CONTENT" > /etc/systemd/system/$SERVICE_NAME.service

# SystemD Service aktivieren und starten
log "Aktiviere und starte Service..."
systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl start $SERVICE_NAME

# Status überprüfen
if systemctl is-active --quiet $SERVICE_NAME; then
    log "Installation erfolgreich abgeschlossen!"
    log "Service läuft unter: http://localhost:5000"
    log "Service-Status: $(systemctl status $SERVICE_NAME | grep Active)"
else
    error "Service konnte nicht gestartet werden!"
    error "Bitte überprüfen Sie: 'systemctl status $SERVICE_NAME'"
fi

# Cleanup
log "Räume auf..."
apt-get clean
apt-get autoremove -y

# Installations-Zusammenfassung
echo -e "\n${GREEN}===  DocFlow Installation ====${NC}"
echo -e "Installationsverzeichnis: $INSTALL_DIR"
echo -e "Service-Name: $SERVICE_NAME"
echo -e "Service-Benutzer: $SERVICE_USER"
echo -e "Web-Interface: http://localhost:5000"
echo -e "Wiki.js URL: $WIKIJS_URL"
echo -e "Wiki.js External URL: $WIKIJS_EXTERNAL_URL"
echo -e "Templates-Verzeichnis: $TEMPLATES_DIR"
echo -e "\nBefehle für die Verwaltung:"
echo -e "  Status anzeigen:    sudo systemctl status $SERVICE_NAME"
echo -e "  Service neustarten: sudo systemctl restart $SERVICE_NAME"
echo -e "  Logs anzeigen:      sudo journalctl -u $SERVICE_NAME -f"
echo -e "\nWiki.js Konfiguration:"
echo -e "  Konfigurationsdatei: $INSTALL_DIR/.env"
echo -e "\nFunktionen:"
echo -e "  - Dokument zu Wiki.js: Konvertierung von Dokumenten zu Markdown mit Upload zu Wiki.js"
echo -e "  - Wiki.js zu Dokument: Export von Wiki.js-Seiten in verschiedene Dokumentformate"
