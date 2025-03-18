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

list_files() {
    local dir="$1"
    echo "Dateien in $dir:"
    ls -la "$dir" | while read -r line; do
        echo "  $line"
    done
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

# Überprüfe, ob die Installation existiert
if [ ! -d "$INSTALL_DIR" ]; then
    warning "Installationsverzeichnis $INSTALL_DIR existiert nicht."
    read -p "Möchten Sie trotzdem fortfahren? (j/n): " CONTINUE
    if [[ ! $CONTINUE =~ ^[Jj]$ ]]; then
        log "Deinstallation abgebrochen."
        exit 0
    fi
fi

# Backup vor Deinstallation?
read -p "Backup vor der Deinstallation erstellen? (j/n): " CREATE_BACKUP
if [[ $CREATE_BACKUP =~ ^[Jj]$ ]]; then
    BACKUP_DIR="/opt/tresorhaus-docflow-backup-final-$(date +%Y%m%d_%H%M%S)"
    log "Erstelle Backup unter $BACKUP_DIR..."

    if [ -d "$INSTALL_DIR" ]; then
        mkdir -p $BACKUP_DIR
        cp -r $INSTALL_DIR/* $BACKUP_DIR/
        cp $INSTALL_DIR/.env $BACKUP_DIR/ 2>/dev/null || true

        # Zeige Liste der gesicherten Dateien
        log "Folgende Dateien wurden gesichert:"
        list_files "$BACKUP_DIR"
    else
        warning "Kann kein Backup erstellen, da $INSTALL_DIR nicht existiert."
    fi
fi

# Service stoppen und deaktivieren
log "Stoppe und deaktiviere Service..."
if systemctl is-active --quiet $SERVICE_NAME; then
    systemctl stop $SERVICE_NAME
    log "Service gestoppt."
fi

if systemctl is-enabled --quiet $SERVICE_NAME; then
    systemctl disable $SERVICE_NAME
    log "Service deaktiviert."
fi

# Service-Datei entfernen
if [ -f "/etc/systemd/system/$SERVICE_NAME.service" ]; then
    log "Entferne Service-Datei..."
    rm -f /etc/systemd/system/$SERVICE_NAME.service
    systemctl daemon-reload
    log "Service-Datei entfernt."
else
    warning "Service-Datei nicht gefunden."
fi

# Installationsverzeichnis entfernen
if [ -d "$INSTALL_DIR" ]; then
    log "Entferne Installationsverzeichnis..."
    log "Inhalt von $INSTALL_DIR vor dem Löschen:"
    list_files "$INSTALL_DIR"
    rm -rf $INSTALL_DIR
    log "Installationsverzeichnis entfernt."
else
    warning "Installationsverzeichnis existiert nicht."
fi

# Benutzer entfernen
if id "$SERVICE_USER" &>/dev/null; then
    log "Entferne Service-Benutzer..."
    userdel $SERVICE_USER
    log "Service-Benutzer entfernt."
else
    warning "Service-Benutzer $SERVICE_USER existiert nicht."
fi

if [[ $CREATE_BACKUP =~ ^[Jj]$ ]] && [ -d "$BACKUP_DIR" ]; then
    log "Deinstallation abgeschlossen! Backup wurde erstellt unter: $BACKUP_DIR"
else
    log "Deinstallation abgeschlossen!"
fi

warning "Hinweis: Wenn Sie die Anwendung komplett neu installieren möchten, führen Sie 'install.sh' aus."
