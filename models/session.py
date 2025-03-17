"""
DocFlow Sitzungsmodell
Enthält Funktionen für die Sitzungsverwaltung
"""
from datetime import datetime

class Logger:
    """Klasse für das Logging von Debug-Nachrichten"""

    def __init__(self):
        self.logs = []

    def log(self, message, log_type='info'):
        """Fügt eine Debug-Nachricht zum Log hinzu"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs.append({
            'time': timestamp,
            'message': message,
            'type': log_type
        })
        print(f"[{timestamp}] {log_type.upper()}: {message}")

    def clear(self):
        """Löscht alle Logs"""
        self.logs = []

    def get_logs(self):
        """Gibt alle Logs zurück"""
        return self.logs
