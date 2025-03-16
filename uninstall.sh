#!/bin/bash

# TresorHaus DocFlow Uninstaller
# Author: Joachim Mild
# For Debian 12

# Farben für Ausgaben
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Logging-Funktion
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Prüfen, ob Script als root läuft
if [ "$EUID" -ne 0 ]; then
    error "Bitte als root ausführen (sudo ./uninstall.sh)"
    exit 1
fi

# Konfiguration
INSTALL_DIR="/opt/tresorhaus-docflow"
SERVICE_NAME="tresorhaus-docflow"
SERVICE_USER="docflow"

# Service stoppen und deaktivieren
log "Stoppe und deaktiviere Service..."
systemctl stop $SERVICE_NAME
systemctl disable $SERVICE_NAME

# Service-Datei entfernen
log "Entferne Service-Datei..."
rm -f /etc/systemd/system/$SERVICE_NAME.service
systemctl daemon-reload

# Installationsverzeichnis entfernen
log "Entferne Installationsverzeichnis..."
rm -rf $INSTALL_DIR

# Benutzer entfernen
log "Entferne Service-Benutzer..."
userdel $SERVICE_USER

log "Deinstallation abgeschlossen!"
