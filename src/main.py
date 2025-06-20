from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QLineEdit, QComboBox, 
                           QCheckBox, QPushButton, QFileDialog, QGroupBox, QSizePolicy, QMessageBox)
from PyQt5.QtCore import Qt
import sys
from pathlib import Path
from image_processor import BiometricImageProcessor
from config import Config
from config_dialog import ConfigDialog

import os
import urllib.request
import bz2
import shutil

class BiometricProcessorGUI(QMainWindow):
    """Hauptfenster für das biometrische Passbild-Tool"""
    def __init__(self):
        super().__init__()
        self.config = Config()  # Konfiguration laden
        self.initUI()
        
    def initUI(self):
        """Initialisiert das GUI"""
        self.setWindowTitle('Biometrisches Passbild-Tool')
        self.setGeometry(100, 100, 600, 400)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        
        # Gruppierung für Ordnerauswahl
        folder_group = QGroupBox("Ordner-Einstellungen")
        folder_layout = QVBoxLayout()

        # Eingabeordner
        input_layout = QHBoxLayout()
        self.input_path = QLineEdit()  # Pfad für Eingabeordner
        self.input_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        input_button = QPushButton("Eingabeordner wählen")
        input_button.clicked.connect(self.select_input_folder)
        input_layout.addWidget(QLabel("Eingabeordner:"))
        input_layout.addWidget(self.input_path)
        input_layout.addWidget(input_button)

        # Ausgabeordner
        output_layout = QHBoxLayout()
        self.output_path = QLineEdit()  # Pfad für Ausgabeordner
        self.output_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        output_button = QPushButton("Ausgabeordner wählen")
        output_button.clicked.connect(self.select_output_folder)
        output_layout.addWidget(QLabel("Ausgabeordner:"))
        output_layout.addWidget(self.output_path)
        output_layout.addWidget(output_button)
        folder_layout.addLayout(input_layout)
        folder_layout.addLayout(output_layout)
        folder_group.setLayout(folder_layout)
        layout.addWidget(folder_group)

        # Gruppierung für Bildeinstellungen
        settings_group = QGroupBox("Bildeinstellungen")
        settings_layout = QVBoxLayout()
        
        # Dateigröße
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel('Dateigröße (KB):'))
        self.file_size = QLineEdit('500')  # Maximale Dateigröße
        self.file_size.setFixedWidth(100)
        size_layout.addWidget(self.file_size)
        size_layout.addStretch()
        settings_layout.addLayout(size_layout)
        
        # Auflösung
        res_layout = QHBoxLayout()
        res_layout.addWidget(QLabel('Auflösung:'))
        self.width_input = QLineEdit('413')  # Zielbreite
        self.width_input.setFixedWidth(60)
        res_layout.addWidget(self.width_input)
        res_layout.addWidget(QLabel('x'))
        self.height_input = QLineEdit('531')  # Zielhöhe
        self.height_input.setFixedWidth(60)
        res_layout.addWidget(self.height_input)
        res_layout.addStretch()
        settings_layout.addLayout(res_layout)
        
        # Voreinstellungen für Auflösung
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel('Voreinstellung:'))
        self.preset_combo = QComboBox()  # Auswahl für Standardformate
        self.preset_combo.addItems([
            "35x45mm (413x531)",
            "35x45mm 600dpi (600x771)"
        ])
        preset_layout.addWidget(self.preset_combo)
        preset_layout.addStretch()
        settings_layout.addLayout(preset_layout)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Namenserweiterung für Ausgabedateien
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel('Namenserweiterung:'))
        self.name_extension = QLineEdit('biometric_')  # Präfix für Dateinamen
        self.name_extension.setFixedWidth(150)
        name_layout.addWidget(self.name_extension)
        name_layout.addStretch()
        settings_layout.addLayout(name_layout)

        # Gruppierung für Optionen
        options_group = QGroupBox("Optionen")
        options_layout = QVBoxLayout()
        
        self.debug_check = QCheckBox('Debug-Modus')  # Zeigt Vorschau und Hilfslinien
        self.debug_check.setChecked(False) 
        options_layout.addWidget(self.debug_check)
        
        self.scal_check = QCheckBox('Korrektur der Skalierung')  # Erlaubt Nachjustierung
        self.scal_check.setChecked(True)
        options_layout.addWidget(self.scal_check)
        
        self.rotate_check = QCheckBox('Automatische Rotation')  # Bildausrichtung automatisch korrigieren
        self.rotate_check.setChecked(True)
        options_layout.addWidget(self.rotate_check)

        self.eye_check = QCheckBox('Biometrische Prüfung (Augen zu)')  # Prüft, ob Augen offen sind
        self.eye_check.setChecked(True)
        options_layout.addWidget(self.eye_check)

        self.mouth_check = QCheckBox('Biometrische Prüfung (Mund offen - Fehleranfällig bei Bartträgern)')  # Prüft, ob Mund geschlossen ist
        self.mouth_check.setChecked(False)
        options_layout.addWidget(self.mouth_check)

        self.side_ratio_check = QCheckBox('Biometrische Prüfung (Kopfneigung)')  # Prüft frontale Ausrichtung
        self.side_ratio_check.setChecked(True)
        options_layout.addWidget(self.side_ratio_check)

        self.head_tilt_check = QCheckBox('Biometrische Prüfung (Kopfdrehung)')  # Prüft Kopfneigung
        self.head_tilt_check.setChecked(True)
        options_layout.addWidget(self.head_tilt_check)

        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Button für erweiterte Einstellungen
        config_button = QPushButton('Erweiterte Einstellungen')
        config_button.clicked.connect(self.show_config_dialog)
        layout.addWidget(config_button)
        
        # Start-Button für die Verarbeitung
        self.start_button = QPushButton('Verarbeitung starten')
        self.start_button.clicked.connect(self.start_processing)
        layout.addWidget(self.start_button)
        
        # Fußzeile mit Urheber
        footer = QLabel("Created by Jan Schneider © 2025")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: gray; font-size: 10pt; margin-top: 20px;")
        layout.addWidget(footer)

        # Events für automatische Berechnung der Auflösung
        self.width_input.textChanged.connect(self.calculate_height)
        self.height_input.textChanged.connect(self.calculate_width)
        self.preset_combo.currentIndexChanged.connect(self.update_resolution)
        
        main_widget.setLayout(layout)
    
    def calculate_height(self):
        """Berechnet die Höhe automatisch anhand der Breite"""
        try:
            width = int(self.width_input.text())
            height = int(width / 0.778)
            self.height_input.blockSignals(True)
            self.height_input.setText(str(height))
            self.height_input.blockSignals(False)
        except ValueError:
            pass
    
    def calculate_width(self):
        """Berechnet die Breite automatisch anhand der Höhe"""
        try:
            height = int(self.height_input.text())
            width = int(height * 0.778)
            self.width_input.blockSignals(True)
            self.width_input.setText(str(width))
            self.width_input.blockSignals(False)
        except ValueError:
            pass
    
    def update_resolution(self, index):
        """Setzt die Auflösung anhand der Voreinstellung"""
        if "413x531" in self.preset_combo.currentText():
            self.width_input.setText("413")
            self.height_input.setText("531")
        elif "600dpi" in self.preset_combo.currentText():
            self.width_input.setText("600")
            self.height_input.setText("771")
    
    def select_input_folder(self):
        """Öffnet Dialog zur Auswahl des Eingabeordners"""
        folder = QFileDialog.getExistingDirectory(self, "Eingabeordner wählen")
        if folder:
            self.input_path.setText(folder)

    def select_output_folder(self):
        """Öffnet Dialog zur Auswahl des Ausgabeordners"""
        folder = QFileDialog.getExistingDirectory(self, "Ausgabeordner wählen")
        if folder:
            self.output_path.setText(folder)

    def show_config_dialog(self):
        """Zeigt das Fenster für erweiterte Einstellungen"""
        dialog = ConfigDialog(self.config, self)
        dialog.exec_()
    
    def start_processing(self):
        """Startet die Bildverarbeitung"""
        input_dir = self.input_path.text()
        if not input_dir:
            input_dir = QFileDialog.getExistingDirectory(self, "Wähle den Eingabeordner")
            if not input_dir:
                return
            self.input_path.setText(input_dir)
            
        output_dir = self.output_path.text()
        if not output_dir:
            output_dir = QFileDialog.getExistingDirectory(self, "Wähle den Ausgabeordner")
            if not output_dir:
                return
            self.output_path.setText(output_dir)
    
        processor = BiometricImageProcessor(
            target_size=(int(self.width_input.text()), 
                        int(self.height_input.text())),
            max_file_size=int(self.file_size.text()) * 1024,
            name_extension=self.name_extension.text(),
            debug_mode=self.debug_check.isChecked(),
            auto_rotate=self.rotate_check.isChecked(),
            scal_check=self.scal_check.isChecked(),
            eye_check=self.eye_check.isChecked(),
            mouth_check=self.mouth_check.isChecked(),
            side_ratio_check=self.side_ratio_check.isChecked(),
            head_tilt_check=self.head_tilt_check.isChecked(),
            config=self.config
        )
        result = processor.process_directory(input_dir, output_dir)
        if result:
            QMessageBox.information(self, "Fertig!", "Alle Bilder wurden verarbeitet.")

def main():
    """Startet die Anwendung"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = BiometricProcessorGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()