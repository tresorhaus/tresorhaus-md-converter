#!/bin/bash

# TresorHaus DocFlow Updater
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
    error "Bitte als root ausführen (sudo ./update.sh)"
    exit 1
fi

# Konfiguration
INSTALL_DIR="/opt/tresorhaus-docflow"
VENV_DIR="$INSTALL_DIR/venv"
SERVICE_NAME="tresorhaus-docflow"
BACKUP_DIR="/opt/tresorhaus-docflow-backup-$(date +%Y%m%d_%H%M%S)"
TEMPLATES_DIR="$INSTALL_DIR/templates"

# Wiki.js Konfiguration aktualisieren?
read -p "Wiki.js Konfiguration aktualisieren? (j/n): " UPDATE_WIKIJS
if [[ $UPDATE_WIKIJS =~ ^[Jj]$ ]]; then
    read -p "Neue Wiki.js URL eingeben (leer lassen für keine Änderung): " NEW_WIKIJS_URL
    read -p "Neuen Wiki.js API Token eingeben (leer lassen für keine Änderung): " NEW_WIKIJS_TOKEN
fi

# Backup erstellen
log "Erstelle Backup..."
mkdir -p $BACKUP_DIR
cp -r $INSTALL_DIR/* $BACKUP_DIR/
cp $INSTALL_DIR/.env $BACKUP_DIR/ 2>/dev/null || true

# Service stoppen
log "Stoppe Service..."
systemctl stop $SERVICE_NAME

# Aktualisiere Anwendungsdateien
log "Aktualisiere Anwendungsdateien..."
cp app.py $INSTALL_DIR/
cp -r static/* $INSTALL_DIR/static/

# Aktualisiere Template-Dateien
log "Aktualisiere Template-Dateien..."
if [ -d "templates" ]; then
    # Stelle sicher, dass das Zielverzeichnis existiert
    mkdir -p $TEMPLATES_DIR
    cp -r templates/* $TEMPLATES_DIR/
    log "Templates aktualisiert."
else
    warning "Keine Template-Dateien im Quellverzeichnis gefunden."
fi

# Aktualisiere Wiki.js Konfiguration wenn gewünscht
if [[ $UPDATE_WIKIJS =~ ^[Jj]$ ]]; then
    if [ -f "$INSTALL_DIR/.env" ]; then
        source "$INSTALL_DIR/.env"
    fi

    if [ ! -z "$NEW_WIKIJS_URL" ]; then
        WIKIJS_URL=$NEW_WIKIJS_URL
    fi
    if [ ! -z "$NEW_WIKIJS_TOKEN" ]; then
        WIKIJS_TOKEN=$NEW_WIKIJS_TOKEN
    fi

    log "Aktualisiere Wiki.js Konfiguration..."
    cat > $INSTALL_DIR/.env << EOF
WIKIJS_URL=$WIKIJS_URL
WIKIJS_TOKEN=$WIKIJS_TOKEN
EOF
    chmod 600 $INSTALL_DIR/.env
fi

# Aktualisiere Python-Pakete
log "Aktualisiere Python-Pakete..."
$VENV_DIR/bin/pip install --upgrade pip
$VENV_DIR/bin/pip install -r requirements.txt --upgrade

# Berechtigungen aktualisieren
log "Aktualisiere Berechtigungen..."
chown -R docflow:docflow $INSTALL_DIR
chmod -R 755 $INSTALL_DIR
chmod 600 $INSTALL_DIR/.env
chmod -R 755 $TEMPLATES_DIR

# Service neustarten
log "Starte Service neu..."
systemctl daemon-reload
systemctl start $SERVICE_NAME

# Status überprüfen
if systemctl is-active --quiet $SERVICE_NAME; then
    log "Update erfolgreich abgeschlossen!"
    log "Service läuft unter: http://localhost:5000"
    log "Service-Status: $(systemctl status $SERVICE_NAME | grep Active)"
    log "Backup wurde erstellt unter: $BACKUP_DIR"
else
    error "Service konnte nicht gestartet werden!"
    error "Stelle Backup wieder her..."
    cp -r $BACKUP_DIR/* $INSTALL_DIR/
    cp $BACKUP_DIR/.env $INSTALL_DIR/ 2>/dev/null || true
    systemctl start $SERVICE_NAME
    error "Bitte überprüfen Sie: 'systemctl status $SERVICE_NAME'"
fi
