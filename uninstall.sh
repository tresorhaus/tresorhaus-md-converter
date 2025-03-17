#!/bin/bash

#  DocFlow Uninstaller
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
    error "Bitte als root ausführen (sudo ./uninstall.sh)"
    exit 1
fi

# Konfiguration
INSTALL_DIR="/opt/tresorhaus-docflow"
SERVICE_NAME="tresorhaus-docflow"
SERVICE_USER="docflow"

# Backup vor Deinstallation?
read -p "Backup vor der Deinstallation erstellen? (j/n): " CREATE_BACKUP
if [[ $CREATE_BACKUP =~ ^[Jj]$ ]]; then
    BACKUP_DIR="/opt/tresorhaus-docflow-backup-final-$(date +%Y%m%d_%H%M%S)"
    log "Erstelle Backup unter $BACKUP_DIR..."
    mkdir -p $BACKUP_DIR
    cp -r $INSTALL_DIR/* $BACKUP_DIR/
    cp $INSTALL_DIR/.env $BACKUP_DIR/ 2>/dev/null || true
fi

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

if [[ $CREATE_BACKUP =~ ^[Jj]$ ]]; then
    log "Deinstallation abgeschlossen! Backup wurde erstellt unter: $BACKUP_DIR"
else
    log "Deinstallation abgeschlossen!"
fi

warning "Hinweis: Wenn Sie die Anwendung komplett neu installieren möchten, führen Sie 'install.sh' aus."
