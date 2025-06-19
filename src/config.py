import json
from pathlib import Path
import sys

DEFAULT_CONFIG = {
    "face_detection": {
        "scale_factor": 1.3,
        "min_neighbors": 5,
        "head_height_factor": 1.4,
        "total_height_factor": 1.8,
        "width_ratio": 0.75
    },
    "biometric_checks": {
        "chin_to_eye_factor": 2.2,
        "min_face_hight": 86.02,
        "max_face_height": 94.85,
        "chin_hight": 13.82,
        "min_eye_hight": 48.77,
        "max_eye_hight": 71.04,
        "after_scale": 1.03,
        "side_ratio_tolerance": 0.15,
        "max_head_tilt": 8.0,
        "min_eye_ratio": 0.2,
        "max_mouth_gap": 15,
        "name_extension": "biometric_"
    },
    "image_quality": {
        "min_jpeg_quality": 30,
        "start_jpeg_quality": 95,
        "quality_step": 5
    },

}

class Config:
    def __init__(self):
        self.base_path = self._get_base_path()
        self.config_file = self.base_path / "settings.json"
        self.load_config()

    def _get_base_path(self):
        if getattr(sys, 'frozen', False):  # PyInstaller-EXE
            return Path(sys.executable).parent
        else:  # Normaler Python-Modus
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