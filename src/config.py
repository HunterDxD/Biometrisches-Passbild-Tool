import json
from pathlib import Path
import sys

# Standard-Konfiguration für das Programm
DEFAULT_CONFIG = {
    "face_detection": {
        "scale_factor": 1.3,  # Skalierungsfaktor für Gesichtserkennung
        "min_neighbors": 5,   # Mindestanzahl Nachbarn für Gesicht
        "head_height_factor": 1.4,  # Faktor für Kopfhöhe
        "total_height_factor": 1.8, # Faktor für Gesamthöhe
        "width_ratio": 0.75         # Breitenverhältnis des Bildes
    },
    "biometric_checks": {
        "chin_to_eye_factor": 2.2,      # Verhältnis Kinn zu Augen
        "min_face_hight": 86.02,        # Minimale Gesichtshöhe in %
        "max_face_height": 94.85,       # Maximale Gesichtshöhe in %
        "chin_hight": 13.82,            # Kinnhöhe in %
        "min_eye_hight": 48.77,         # Minimale Augenhöhe in %
        "max_eye_hight": 71.04,         # Maximale Augenhöhe in %
        "after_scale": 1.03,            # Nachskalierungsfaktor
        "side_ratio_tolerance": 0.15,   # Toleranz für Seitenverhältnis
        "max_head_tilt": 8.0,           # Maximale Kopfneigung in Grad
        "min_eye_ratio": 0.2,           # Minimale Augenöffnung
        "max_mouth_gap": 15,            # Maximale Mundöffnung in Pixel
        "name_extension": "biometric_"  # Präfix für Dateinamen
    },
    "image_quality": {
        "min_jpeg_quality": 30,     # Minimale JPEG-Qualität
        "start_jpeg_quality": 95,   # Startwert für JPEG-Qualität
        "quality_step": 5           # Schrittweite für Qualitätsreduktion
    },
}

class Config:
    """Verwaltet das Laden und Speichern der Konfiguration"""
    def __init__(self):
        self.base_path = self._get_base_path()  # Basisverzeichnis bestimmen
        self.config_file = self.base_path / "settings.json"  # Pfad zur Konfigurationsdatei
        self.load_config()

    def _get_base_path(self):
        # Ermittelt das Basisverzeichnis (auch für PyInstaller)
        if getattr(sys, 'frozen', False):
            return Path(sys.executable).parent
        else:
            return Path(__file__).parent
    
    def load_config(self):
        """Lädt die Konfiguration aus der JSON-Datei"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.settings = json.load(f)
        else:
            self.settings = DEFAULT_CONFIG
            self.save_config()
    
    def save_config(self):
        """Speichert die Konfiguration in die JSON-Datei"""
        with open(self.config_file, 'w') as f:
            json.dump(self.settings, f, indent=4, ensure_ascii=False)
    
    def get(self, section, key):
        """Gibt einen Konfigurationswert zurück"""
        return self.settings[section][key]
    
    def set(self, section, key, value):
        """Setzt einen Konfigurationswert"""
        if section not in self.settings:
            self.settings[section] = {}
        self.settings[section][key] = value