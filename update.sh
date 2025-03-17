#!/bin/bash

#  DocFlow Updater
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

# Funktion zum Verwalten der Backups (max 3)
manage_backups() {
    local base_dir="/opt/tresorhaus-docflow-backup"
    local backup_count=$(find /opt -maxdepth 1 -name "tresorhaus-docflow-backup-*" -type d | wc -l)

    # Wenn mehr als 3 Backups vorhanden sind, lösche die ältesten
    if [ "$backup_count" -gt 3 ]; then
        log "Es sind mehr als 3 Backups vorhanden. Lösche die ältesten..."
        find /opt -maxdepth 1 -name "tresorhaus-docflow-backup-*" -type d | sort | head -n -3 | xargs rm -rf
        log "Alte Backups wurden gelöscht. Nur die 3 neuesten werden behalten."
    fi
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
    read -p "Neue Wiki.js External URL eingeben (leer lassen für keine Änderung): " NEW_WIKIJS_EXTERNAL_URL
fi

# Backup erstellen
log "Erstelle Backup..."
mkdir -p $BACKUP_DIR
cp -r $INSTALL_DIR/* $BACKUP_DIR/
cp $INSTALL_DIR/.env $BACKUP_DIR/ 2>/dev/null || true

# Verwalte Backups (behält nur die neuesten 3)
manage_backups

# Service stoppen
log "Stoppe Service..."
systemctl stop $SERVICE_NAME

# Aktualisiere Anwendungsdateien
log "Aktualisiere Anwendungsdateien..."
cp app.py $INSTALL_DIR/
cp -r static/* $INSTALL_DIR/static/ 2>/dev/null || warning "Keine statischen Dateien gefunden."

# Aktualisiere Template-Dateien
log "Aktualisiere Template-Dateien..."
if [ -d "templates" ]; then
    # Prüfe ob die neuen Export-Funktionalitäts-Templates existieren
    if [ -f "templates/export.html" ] && [ -f "templates/export_results.html" ]; then
        log "Neue Export-Funktionalität erkannt."
    else
        warning "Die neuen Export-Template-Dateien fehlen. Die Export-Funktionalität könnte beeinträchtigt sein."
    fi

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

    if [ ! -z "$NEW_WIKIJS_EXTERNAL_URL" ]; then
        WIKIJS_EXTERNAL_URL=$NEW_WIKIJS_EXTERNAL_URL
    elif [ -z "$WIKIJS_EXTERNAL_URL" ]; then
        # Wenn keine externe URL gesetzt ist und keine neue angegeben wurde, verwende die URL
        WIKIJS_EXTERNAL_URL=$WIKIJS_URL
        warning "Keine Wiki.js External URL gefunden. Verwende Wiki.js URL als External URL."
    fi

    log "Schreibe aktualisierte .env Datei..."
    cat > $INSTALL_DIR/.env << EOF
WIKIJS_URL=$WIKIJS_URL
WIKIJS_TOKEN=$WIKIJS_TOKEN
WIKIJS_EXTERNAL_URL=$WIKIJS_EXTERNAL_URL
EOF
fi

# Aktualisiere Python-Abhängigkeiten
log "Aktualisiere Python-Abhängigkeiten..."
if [ -f "requirements.txt" ]; then
    $VENV_DIR/bin/pip install --upgrade -r requirements.txt
else
    warning "requirements.txt nicht gefunden. Überspringe Abhängigkeiten-Update."
fi

# Berechtigungen aktualisieren
log "Aktualisiere Berechtigungen..."
chown -R docflow:docflow $INSTALL_DIR
chmod -R 755 $INSTALL_DIR
chmod 600 $INSTALL_DIR/.env

# Service neu starten
log "Starte Service neu..."
systemctl start $SERVICE_NAME
sleep 2

# Status prüfen
if systemctl is-active --quiet $SERVICE_NAME; then
    log "Update erfolgreich abgeschlossen!"
    log "Service-Status: $(systemctl status $SERVICE_NAME | grep Active)"
else
    error "Service konnte nicht gestartet werden!"
    error "Bitte überprüfen Sie: 'systemctl status $SERVICE_NAME'"
    error "Falls nötig, stellen Sie das Backup von $BACKUP_DIR wieder her."
fi

# Zusammenfassung
echo -e "\n${GREEN}=== DocFlow Update ====${NC}"
echo -e "Update-Zeitpunkt: $(date)"
echo -e "Backup-Verzeichnis: $BACKUP_DIR"
echo -e "Web-Interface: http://localhost:5000"

if [[ $UPDATE_WIKIJS =~ ^[Jj]$ ]]; then
    echo -e "Wiki.js URL wurde aktualisiert: $WIKIJS_URL"
    echo -e "Wiki.js External URL: $WIKIJS_EXTERNAL_URL"
    if [ ! -z "$NEW_WIKIJS_TOKEN" ]; then
        echo -e "Wiki.js API Token wurde aktualisiert."
    fi
fi

echo -e "\nNeue Funktionen:"
echo -e "  - Dokument zu Wiki.js: Konvertierung von Dokumenten zu Markdown mit Upload zu Wiki.js"
echo -e "  - Wiki.js zu Dokument: Export von Wiki.js-Seiten in verschiedene Dokumentformate"
