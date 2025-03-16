#!/bin/bash

# TresorHaus DocFlow Installer
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

# SystemD Service Definition
SERVICE_CONTENT="[Unit]
Description=TresorHaus DocFlow Service
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

# Kopiere Anwendungsdateien
log "Kopiere Anwendungsdateien..."
cp app.py $INSTALL_DIR/
cp -r static/* $INSTALL_DIR/static/

# Erstelle requirements.txt falls nicht vorhanden
if [ ! -f "requirements.txt" ]; then
    log "Erstelle requirements.txt..."
    echo "Flask==2.3.3" > requirements.txt
    echo "Werkzeug==2.3.7" >> requirements.txt
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
echo -e "\n${GREEN}=== TresorHaus DocFlow Installation ====${NC}"
echo -e "Installationsverzeichnis: $INSTALL_DIR"
echo -e "Service-Name: $SERVICE_NAME"
echo -e "Service-Benutzer: $SERVICE_USER"
echo -e "Web-Interface: http://localhost:5000"
echo -e "\nBefehle für die Verwaltung:"
echo -e "  Status anzeigen:    sudo systemctl status $SERVICE_NAME"
echo -e "  Service neustarten: sudo systemctl restart $SERVICE_NAME"
echo -e "  Logs anzeigen:      sudo journalctl -u $SERVICE_NAME -f"
