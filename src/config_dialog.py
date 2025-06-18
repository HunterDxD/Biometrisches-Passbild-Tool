from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QPushButton, QGroupBox, QMessageBox,
                           QToolButton, QWidget, QScrollArea)
from PyQt5.QtCore import Qt
from config import DEFAULT_CONFIG  # Assuming DEFAULT_CONFIG is defined in config.py

HELP_TEXTS = {
    "face_detection": {
        "title": "Gesichtserkennung",
        "description": """Diese Einstellungen beeinflussen, wie Gesichter erkannt und zugeschnitten werden.""",
        "scale_factor": """Skalierungsfaktor für die Gesichtserkennung.
Ein höherer Wert (z.B. 1.5) macht die Erkennung schneller, aber weniger genau.
Ein niedrigerer Wert (z.B. 1.1) macht die Erkennung genauer, aber langsamer.
Empfohlener Bereich: 1.1 - 1.5""",
        "min_neighbors": """Minimale Anzahl benachbarter Detektionen für ein gültiges Gesicht.
Ein höherer Wert reduziert Falscherkennungen, kann aber Gesichter übersehen.
Ein niedrigerer Wert erkennt mehr Gesichter, aber mit mehr Falscherkennungen.
Empfohlener Bereich: 3 - 6""",
        "head_height_factor": """Faktor für die Kopfhöhe relativ zur Gesichtshöhe.
1.4 bedeutet 40% mehr Platz über dem Gesicht für Haare/Kopf.
Empfohlener Bereich: 1.3 - 1.5""",
        "total_height_factor": """Faktor für die Gesamthöhe des Bildes relativ zur Gesichtshöhe.
1.8 bedeutet 80% mehr Platz für Schultern und Kopf.
Empfohlener Bereich: 1.7 - 2.0""",
        "width_ratio": """Verhältnis von Breite zu Höhe des finalen Bildes.
0.75 entspricht dem Standard-Passbildformat (3:4).
Empfohlener Wert: 0.75"""
    },
    "biometric_checks": {
        "title": "Biometrische Prüfungen",
        "description": """Diese Einstellungen definieren die Toleranzen für biometrische Anforderungen.""",
        "chin_to_eye_factor": """Verhältnis zwischen Kinn und Augenhöhe. Wird für die Platzierung des Gesichts genutzt.""",
        "min_face_hight": """Minimale Gesichtshöhe in Prozent der Bildhöhe.
Das Gesicht muss mindestens diesen Anteil des Bildes einnehmen.
Empfohlender Bereich: 86.02%.""",
        "max_face_height": """Maximale Gesichtsbereich in Prozent der Bildhöhe.
Das Gesicht darf maximal diesen Anteil des Bildes einnehmen.
Empfohlender Bereich: 94.85%.""",
        "chin_hight": """Abstand des Kinns vom unteren Bildrand in Prozent.
Das Kinn wird exakt auf diese Höhe positioniert.
Empfohlender Bereich: 13.82%.""",
        "min_eye_hight": """Minimale Augenhöhe in Prozent der Bildhöhe.
Die Augen müssen mindestens so weit vom unteren Rand entfernt sein.
Empfohlender Bereich: 48.77%.""",
        "max_eye_hight": """Maximale Augenhöhe in Prozent der Bildhöhe.
Die Augen dürfen maximal so weit vom unteren Rand entfernt sein.
Empfohlender Bereich: 71.04%.""",
        "after_scale": """Faktor für eine optionale Nachskalierung nach dem automatischen Zuschnitt.
Erlaubt manuelles Nachjustieren.
Empfohlender Bereich: 1.03""",
        "side_ratio_tolerance": """Toleranz für die Symmetrie des Gesichts (frontale Ausrichtung).
0.15 bedeutet 15% Toleranz in der Seitenansicht.
Empfohlener Bereich: 0.1 - 0.2""",
        "max_head_tilt": """Maximale erlaubte Kopfneigung in Grad.
Ein Wert von 8.0 erlaubt eine Neigung von ±8 Grad.
Empfohlener Bereich: 5 - 10""",
        "min_eye_ratio": """Minimales Verhältnis der Augenöffnung.
Erkennt geschlossene oder stark zusammengekniffene Augen.
Empfohlener Bereich: 0.15 - 0.25""",
        "max_mouth_gap": """Maximaler Abstand zwischen Ober- und Unterlippe in Pixeln.
Erkennt geöffnete Münder.
Empfohlener Bereich: 10 - 20"""
    },
    "image_quality": {
        "title": "Bildqualität",
        "description": """Diese Einstellungen steuern die JPEG-Kompression für die Dateigröße.""",
        "min_jpeg_quality": """Minimale JPEG-Qualität (1-100).
Unter diesem Wert wird das Bild nicht weiter komprimiert.
Empfohlener Bereich: 30 - 50""",
        "start_jpeg_quality": """Anfängliche JPEG-Qualität (1-100).
Von diesem Wert aus wird die Kompression schrittweise erhöht.
Empfohlener Wert: 95""",
        "quality_step": """Schrittweite der Qualitätsreduzierung.
Größere Schritte = schnellere Verarbeitung, aber gröbere Abstufung.
Empfohlener Bereich: 3 - 5"""
    }
}

class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hilfe zur Konfiguration")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.initUI()
    
    def initUI(self):
        layout = QVBoxLayout()
        
        # Scrollbereich für den Hilfetext
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        help_widget = QWidget()
        help_layout = QVBoxLayout()
        
        # Allgemeine Anleitung
        general_help = QLabel("""
        <h2>Anleitung zur Biometrischen Bildverarbeitung</h2>
        <p>Diese Software verarbeitet Fotos nach biometrischen Standards für offizielle Dokumente.</p>
        
        <h3>Grundlegende Schritte:</h3>
        <ol>
            <li>Wählen Sie einen Eingabeordner mit Ihren Fotos</li>
            <li>Wählen Sie einen Ausgabeordner für die verarbeiteten Bilder</li>
            <li>Aktivieren Sie den Debug-Modus für eine Vorschau</li>
            <li>Passen Sie die Einstellungen nach Bedarf an</li>
        </ol>
        
        <h3>Wichtige Hinweise:</h3>
        <ul>
            <li>Verwenden Sie Fotos mit frontaler Ansicht</li>
            <li>Stellen Sie gute Beleuchtung sicher</li>
            <li>Vermeiden Sie starke Schatten</li>
            <li>Person sollte neutral schauen</li>
        </ul>
        
        <h3>Konfigurationseinstellungen:</h3>
        """)
        general_help.setWordWrap(True)
        help_layout.addWidget(general_help)
        
        # Hilfe für jede Kategorie
        for section, content in HELP_TEXTS.items():
            group = QGroupBox(content["title"])
            group_layout = QVBoxLayout()
            
            description = QLabel(content["description"])
            description.setWordWrap(True)
            group_layout.addWidget(description)
            
            # Parameter der Kategorie
            for param, help_text in content.items():
                if param not in ["title", "description"]:
                    param_label = QLabel(f"<b>{param}:</b>")
                    param_label.setWordWrap(True)
                    help_label = QLabel(help_text)
                    help_label.setWordWrap(True)
                    group_layout.addWidget(param_label)
                    group_layout.addWidget(help_label)
                    group_layout.addSpacing(10)
            
            group.setLayout(group_layout)
            help_layout.addWidget(group)
        
        help_widget.setLayout(help_layout)
        scroll.setWidget(help_widget)
        layout.addWidget(scroll)
        
        # Schließen Button
        close_btn = QPushButton("Schließen")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)

class ConfigDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle('Erweiterte Konfiguration')
        layout = QVBoxLayout()
        
        # Gesichtserkennung
        face_group = QGroupBox("Gesichtserkennung")
        face_layout = QVBoxLayout()
        
        self.scale_factor = self.add_config_field(face_layout, 
            "Skalierungsfaktor:", "face_detection", "scale_factor")
        self.min_neighbors = self.add_config_field(face_layout,
            "Minimale Nachbarn:", "face_detection", "min_neighbors")
        self.head_height = self.add_config_field(face_layout,
            "Kopfhöhenfaktor:", "face_detection", "head_height_factor")
        self.total_height = self.add_config_field(face_layout,
            "Gesamthöhenfaktor:", "face_detection", "total_height_factor")
        self.width_ratio = self.add_config_field(face_layout,
            "Breitenverhältnis:", "face_detection", "width_ratio")
            
        face_group.setLayout(face_layout)
        layout.addWidget(face_group)
        
        # Biometrische Prüfungen
        bio_group = QGroupBox("Biometrische Prüfungen")
        bio_layout = QVBoxLayout()
        
        self.chin_to_eye = self.add_config_field(bio_layout,
            "Kinn zu Auge Faktor:", "biometric_checks", "chin_to_eye_factor")
        self.min_face_height = self.add_config_field(bio_layout,
            "Min. Gesichtshöhe (Prozent):", "biometric_checks", "min_face_hight")
        self.max_face_height = self.add_config_field(bio_layout,
            "Max. Gesichtshöhe (Prozent):", "biometric_checks", "max_face_height")
        self.chin_height = self.add_config_field(bio_layout,
            "Kinnhöhe (Prozent):", "biometric_checks", "chin_hight")
        self.min_eye_height = self.add_config_field(bio_layout,
            "Min. Augenhöhe (Prozent):", "biometric_checks", "min_eye_hight")
        self.max_eye_height = self.add_config_field(bio_layout,
            "Max. Augenhöhe (Prozent):", "biometric_checks", "max_eye_hight")
        self.after_scale = self.add_config_field(bio_layout,
            "Nachskalierungsfaktor:", "biometric_checks", "after_scale")
        self.side_ratio = self.add_config_field(bio_layout,
            "Seitenverhältnis-Toleranz:", "biometric_checks", "side_ratio_tolerance")
        self.head_tilt = self.add_config_field(bio_layout,
            "Max. Kopfneigung (Grad):", "biometric_checks", "max_head_tilt")
        self.eye_ratio = self.add_config_field(bio_layout,
            "Min. Augenöffnung:", "biometric_checks", "min_eye_ratio")
        self.mouth_gap = self.add_config_field(bio_layout,
            "Max. Mundöffnung (Pixel):", "biometric_checks", "max_mouth_gap")
            
        bio_group.setLayout(bio_layout)
        layout.addWidget(bio_group)
        
        # Bildqualität
        quality_group = QGroupBox("Bildqualität")
        quality_layout = QVBoxLayout()
        
        self.min_quality = self.add_config_field(quality_layout,
            "Min. JPEG-Qualität:", "image_quality", "min_jpeg_quality")
        self.start_quality = self.add_config_field(quality_layout,
            "Start JPEG-Qualität:", "image_quality", "start_jpeg_quality")
        self.quality_step = self.add_config_field(quality_layout,
            "Qualitätsschritte:", "image_quality", "quality_step")
            
        quality_group.setLayout(quality_layout)
        layout.addWidget(quality_group)
        
        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Speichern")
        save_btn.clicked.connect(self.save_settings)
        reset_btn = QPushButton("Zurücksetzen")
        reset_btn.clicked.connect(self.reset_settings)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(reset_btn)
        
        # Hilfe-Button hinzufügen
        help_btn = QPushButton("Hilfe")
        help_btn.clicked.connect(self.show_help)
        btn_layout.addWidget(help_btn)
        
        layout.addLayout(btn_layout)
        
        # Hinweis zur Hilfe
        help_hint = QLabel(
            "<b>Tipp:</b> Klicken Sie auf <i>Hilfe</i>, um eine ausführliche Erklärung aller Einstellungen zu erhalten."
        )
        help_hint.setWordWrap(True)
        layout.addWidget(help_hint)
        
        self.setLayout(layout)
    
    def add_config_field(self, layout, label, section, key):
        """Fügt ein Konfigurationsfeld hinzu"""
        field_layout = QHBoxLayout()
        field_layout.addWidget(QLabel(label))
        edit = QLineEdit(str(self.config.get(section, key)))
        edit.setObjectName(f"{section}.{key}")
        field_layout.addWidget(edit)
        layout.addLayout(field_layout)
        return edit
    
    def save_settings(self):
        """Speichert alle Einstellungen"""
        try:
            for widget in self.findChildren(QLineEdit):
                if widget.objectName():
                    section, key = widget.objectName().split('.')
                    value = float(widget.text())
                    self.config.set(section, key, value)
            self.config.save_config()
            QMessageBox.information(self, "Erfolg", 
                "Einstellungen wurden gespeichert!")
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "Fehler", 
                "Bitte geben Sie gültige Zahlen ein!")
    
    def reset_settings(self):
        """Setzt alle Einstellungen zurück"""
        if QMessageBox.question(self, "Zurücksetzen", 
            "Möchten Sie alle Einstellungen auf die Standardwerte zurücksetzen?",
            QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            from config import DEFAULT_CONFIG  # Make sure this import points to where DEFAULT_CONFIG is defined
            self.config.settings = DEFAULT_CONFIG.copy()
            self.config.save_config()
            self.accept()
    
    def show_help(self):
        help_dialog = HelpDialog(self)
        help_dialog.exec_()