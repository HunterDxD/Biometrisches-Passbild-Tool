from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QLineEdit, QComboBox, 
                           QCheckBox, QPushButton, QFileDialog, QGroupBox, QSizePolicy, QMessageBox, QSlider, QStyleFactory)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
import sys
from pathlib import Path
from image_processor import BiometricImageProcessor
from config import Config
from config_dialog import ConfigDialog
import cv2
import numpy as np

import os
import urllib.request
import bz2
import shutil

class BiometricProcessorGUI(QMainWindow):
    """Hauptfenster für das biometrische Passbild-Tool"""
    def __init__(self):
        super().__init__()
        self.config = Config()  # Konfiguration laden
        self.current_image = None  # Das aktuell angezeigte Bild
        self.current_shape = None
        self.scale_factor = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.rotation_angle = 0
        self.processor = None
        self.image_list = []
        self.image_index = 0
        self.log_file = None
        self.initUI()


    def initUI(self):
        """Initialisiert das GUI"""
        self.setWindowTitle('Biometrisches Passbild-Tool')
        self.setGeometry(100, 100, 600, 400)

        # Fenster auf volle Bildschirmgröße setzen
        self.showMaximized()

        # Hauptlayout: horizontal (links, mitte, rechts)
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout()

        # Bildschirmbreite auslesen
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        self.screen_width = screen_geometry.width()
        self.screen_height = screen_geometry.height()

        # Linker Bereich: Einstellungen
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        
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
        left_layout.addWidget(folder_group)

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
        
        # Namenserweiterung für Ausgabedateien
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel('Namenserweiterung:'))
        self.name_extension = QLineEdit('biometric_')  # Präfix für Dateinamen
        self.name_extension.setFixedWidth(150)
        name_layout.addWidget(self.name_extension)
        name_layout.addStretch()
        settings_layout.addLayout(name_layout)
        settings_group.setLayout(settings_layout)
        left_layout.addWidget(settings_group)
        
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
        left_layout.addWidget(options_group)
        
        # Button für erweiterte Einstellungen
        config_button = QPushButton('Erweiterte Einstellungen')
        config_button.clicked.connect(self.show_config_dialog)
        left_layout.addWidget(config_button)
        
        # Start-Button für die Verarbeitung
        self.start_button = QPushButton('Verarbeitung starten')
        self.start_button.clicked.connect(self.start_processing)
        left_layout.addWidget(self.start_button)
        
        # Fußzeile mit Urheber
        footer = QLabel("Created by Jan Schneider © 2025")
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: gray; font-size: 10pt; margin-top: 20px;")

        # Hauptlayout als QVBoxLayout
        outer_layout = QVBoxLayout()
        outer_layout.addLayout(main_layout)
        outer_layout.addWidget(footer)
        main_widget.setLayout(outer_layout)

        left_widget.setLayout(left_layout)
        left_widget.setMaximumHeight(int(self.screen_height * 0.9))  # Maximale Höhe für den linken Bereich

        # Mittlerer Bereich: Bildanzeige
        center_widget = QWidget()
        center_layout = QVBoxLayout()
        self.image_label = QLabel("Kein Bild geladen")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background: #222; border: 1px solid #888;")
        center_layout.addWidget(self.image_label)

        self.info_label = QLabel("Auflösung: -    Dateigröße: -")
        self.info_label.setAlignment(Qt.AlignLeft | Qt.AlignBottom)
        self.info_label.setFixedHeight(int(self.screen_height * 0.025))  # Höhe für Info-Label
        self.info_label.setStyleSheet("color: #666; font-size: 11pt; margin-top: 10px;")
        center_layout.addWidget(self.info_label)

        center_widget.setLayout(center_layout)
        center_widget.setMaximumHeight(int(self.screen_height * 0.9))  # Maximale Höhe für den mittleren Bereich

        # Rechter Bereich: Manuelle Steuerung
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("<b>Manuelle Anpassung</b>"))
        self.scale_up_btn = QPushButton("Größer (+)")
        self.scale_down_btn = QPushButton("Kleiner (-)")
        self.move_left_btn = QPushButton("← Links")
        self.move_right_btn = QPushButton("→ Rechts")
        self.move_up_btn = QPushButton("↑ Hoch")
        self.move_down_btn = QPushButton("↓ Runter")
        self.rotate_left_btn = QPushButton("Links drehen (l)")
        self.rotate_right_btn = QPushButton("Rechts drehen (r)")
        # Buttons verbinden
        self.scale_up_btn.clicked.connect(lambda: self.manual_adjust('scale_up'))
        self.scale_down_btn.clicked.connect(lambda: self.manual_adjust('scale_down'))
        self.move_left_btn.clicked.connect(lambda: self.manual_adjust('move_left'))
        self.move_right_btn.clicked.connect(lambda: self.manual_adjust('move_right'))
        self.move_up_btn.clicked.connect(lambda: self.manual_adjust('move_up'))
        self.move_down_btn.clicked.connect(lambda: self.manual_adjust('move_down'))
        self.rotate_left_btn.clicked.connect(lambda: self.manual_adjust('rotate_left'))
        self.rotate_right_btn.clicked.connect(lambda: self.manual_adjust('rotate_right'))
        # Buttons ins Layout
        for btn in [self.scale_up_btn, self.scale_down_btn, self.move_left_btn, self.move_right_btn,
                    self.move_up_btn, self.move_down_btn, self.rotate_left_btn, self.rotate_right_btn]:
            right_layout.addWidget(btn)
        # Speicher- und Weiter-Button hinzufügen
        self.save_btn = QPushButton("Speichern")
        self.save_btn.clicked.connect(self.save_current_image)
        self.next_btn = QPushButton("Nächstes Bild")
        self.next_btn.clicked.connect(self.next_image)
        right_layout.addWidget(self.save_btn)
        right_layout.addWidget(self.next_btn)
        right_layout.addStretch()

        # Gruppierung für Bildbearbeitung
        edit_group = QGroupBox("Bildbearbeitung")
        edit_layout = QVBoxLayout()

        self.gamma_slider = QSlider(Qt.Horizontal)
        self.gamma_slider.setMinimum(10)
        self.gamma_slider.setMaximum(300)
        self.gamma_slider.setValue(100)
        self.gamma_slider.setTickInterval(10)
        self.gamma_slider.setTickPosition(QSlider.TicksBelow)
        edit_layout.addWidget(QLabel("Gamma"))
        edit_layout.addWidget(self.gamma_slider)

        self.brightness_slider = QSlider(Qt.Horizontal)
        self.brightness_slider.setMinimum(-100)
        self.brightness_slider.setMaximum(100)
        self.brightness_slider.setValue(0)
        edit_layout.addWidget(QLabel("Helligkeit"))
        edit_layout.addWidget(self.brightness_slider)

        self.contrast_slider = QSlider(Qt.Horizontal)
        self.contrast_slider.setMinimum(10)
        self.contrast_slider.setMaximum(300)
        self.contrast_slider.setValue(100)
        edit_layout.addWidget(QLabel("Kontrast"))
        edit_layout.addWidget(self.contrast_slider)

        self.r_slider = QSlider(Qt.Horizontal)
        self.r_slider.setMinimum(-100)
        self.r_slider.setMaximum(100)
        self.r_slider.setValue(0)
        edit_layout.addWidget(QLabel("Rot-Korrektur"))
        edit_layout.addWidget(self.r_slider)

        self.g_slider = QSlider(Qt.Horizontal)
        self.g_slider.setMinimum(-100)
        self.g_slider.setMaximum(100)
        self.g_slider.setValue(0)
        edit_layout.addWidget(QLabel("Grün-Korrektur"))
        edit_layout.addWidget(self.g_slider)

        self.b_slider = QSlider(Qt.Horizontal)
        self.b_slider.setMinimum(-100)
        self.b_slider.setMaximum(100)
        self.b_slider.setValue(0)
        edit_layout.addWidget(QLabel("Blau-Korrektur"))
        edit_layout.addWidget(self.b_slider)

        self.magic_btn = QPushButton("Magische Hautkorrektur")
        edit_layout.addWidget(self.magic_btn)

        edit_group.setLayout(edit_layout)
        right_layout.addWidget(edit_group)

        right_widget.setLayout(right_layout)
        right_widget.setFixedWidth(220)  # Optional: feste Breite
        right_widget.setMaximumHeight(int(self.screen_height * 0.9))  # Maximale Höhe für den mittleren Bereich

        # Layout zusammenbauen
        main_layout.addWidget(left_widget)
        main_layout.addWidget(center_widget, stretch=2)
        main_layout.addWidget(right_widget)
        main_widget.setLayout(main_layout)

        # Events für automatische Berechnung der Auflösung
        self.width_input.textChanged.connect(self.calculate_height)
        self.height_input.textChanged.connect(self.calculate_width)
        self.preset_combo.currentIndexChanged.connect(self.update_resolution)
        
        # ...Rest wie bisher (Events, Verarbeitung starten etc.)...
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()

        # Verbindungen für Bildbearbeitungs-Slider und -Buttons
        self.gamma_slider.valueChanged.connect(self.update_image_preview)
        self.brightness_slider.valueChanged.connect(self.update_image_preview)
        self.contrast_slider.valueChanged.connect(self.update_image_preview)
        self.r_slider.valueChanged.connect(self.update_image_preview)
        self.g_slider.valueChanged.connect(self.update_image_preview)
        self.b_slider.valueChanged.connect(self.update_image_preview)
        self.magic_btn.clicked.connect(self.magic_skin_correction)

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
        """Startet die Bildverarbeitung und lädt Bilder für die manuelle Anpassung"""
        input_dir = self.input_path.text()
        output_dir = self.output_path.text()
        if not input_dir or not output_dir:
            QMessageBox.warning(self, "Fehler", "Bitte Eingabe- und Ausgabeordner wählen!")
            return

        self.processor = BiometricImageProcessor(
            target_size=(int(self.width_input.text()), int(self.height_input.text())),
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

        # Lade alle Bilder aus dem Eingabeordner
        self.image_list = list(Path(input_dir).glob('*.[jJ][pP][gG]'))
        if not self.image_list:
            QMessageBox.warning(self, "Fehler", "Keine JPG-Bilder im Eingabeordner gefunden!")
            return
        self.image_index = 0
        self.load_current_image()

        self.log_file = Path(self.output_path.text()) / "nicht_biometrisch.txt"
        with open(self.log_file, "w", encoding="utf-8") as log:
            log.write("")  # Datei leeren/neu anlegen

    def load_current_image(self):
        """Lädt das aktuelle Bild und die Landmarks"""
        img_path = self.image_list[self.image_index]
        file_bytes = np.asarray(bytearray(open(img_path, 'rb').read()), dtype=np.uint8)
        image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        if image is None:
            self.log_non_biometric("Bild konnte nicht geladen werden")
            QMessageBox.warning(self, "Fehler", f"Bild konnte nicht geladen werden: {img_path.name}")
            return
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.processor.detector(gray, 1)
        if len(faces) == 0:
            self.log_non_biometric("Kein Gesicht erkannt")
            QMessageBox.warning(self, "Fehler", f"Kein Gesicht erkannt: {img_path.name}")
            return
        shape = self.processor.predictor(gray, faces[0])
        # Biometrische Anforderungen prüfen
        is_valid, message = self.processor.check_biometric_requirements(shape)
        if not is_valid:
            self.log_non_biometric(message)
            QMessageBox.warning(self, "Nicht biometrisch", f"{img_path.name}: {message}")
            # Optional: Bild überspringen
            return
        self.current_image = image
        self.current_shape = shape
        self.scale_factor = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.rotation_angle = 0
        self.setFocus()
        self.update_image_preview()

    def manual_adjust(self, action):
        """Manuelle Anpassung des aktuellen Bildes"""
        if self.current_image is None or self.current_shape is None:
            return
        if action == 'scale_up':
            self.scale_factor *= self.processor.after_scale_factor
        elif action == 'scale_down':
            self.scale_factor /= self.processor.after_scale_factor
        elif action == 'move_left':
            self.offset_x -= self.processor.move_step
        elif action == 'move_right':
            self.offset_x += self.processor.move_step
        elif action == 'move_up':
            self.offset_y -= self.processor.move_step
        elif action == 'move_down':
            self.offset_y += self.processor.move_step
        elif action == 'rotate_left':
            self.rotation_angle += self.processor.rotate_angle
        elif action == 'rotate_right':
            self.rotation_angle -= self.processor.rotate_angle
        self.update_image_preview()

    def update_image_preview(self):
        """Aktualisiert die Bildanzeige in der Mitte"""
        if self.current_image is not None and self.current_shape is not None:
            processed = self.processor.process_image(
                self.current_image,
                self.current_shape,
                scale_override=self.scale_factor,
                offset_x=self.offset_x,
                offset_y=self.offset_y,
                rotation_angle=self.rotation_angle
            )
            # Bildbearbeitung anwenden
            processed = self.apply_image_edits(processed)
            processed_with_guides = self.processor.draw_biometric_guides(processed)
            height, width, channel = processed_with_guides.shape
            bytes_per_line = 3 * width
            q_img = QImage(processed_with_guides.tobytes(), width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
            pixmap = QPixmap.fromImage(q_img)
            self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

            # Auflösung und Dateigröße anzeigen
            # Kodieren als JPEG, um die aktuelle Größe zu bekommen
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 95]
            _, encoded_img = cv2.imencode('.jpg', processed, encode_param)
            size_kb = encoded_img.nbytes // 1024
            self.info_label.setText(f"Auflösung: {width} x {height}    Dateigröße: {size_kb} KB")
        else:
            self.image_label.setText("Kein Bild geladen")
            self.info_label.setText("Auflösung: -    Dateigröße: -")

    def save_current_image(self):
        """Speichert das aktuell bearbeitete Bild im Ausgabeordner"""
        if self.current_image is None or self.current_shape is None:
            return
        processed = self.processor.process_image(
            self.current_image,
            self.current_shape,
            scale_override=self.scale_factor,
            offset_x=self.offset_x,
            offset_y=self.offset_y,
            rotation_angle=self.rotation_angle
        )
        encoded_img = self.processor.adjust_jpeg_quality(processed, self.processor.max_file_size)
        output_dir = self.output_path.text()
        img_path = self.image_list[self.image_index]
        output_file = Path(output_dir) / f"{self.name_extension.text()}{img_path.name}"
        with open(output_file, 'wb') as f:
            f.write(encoded_img)
        QMessageBox.information(self, "Gespeichert", f"Bild gespeichert: {output_file.name}")
        self.next_image(save="gesichert")

    def next_image(self, save=""):
        """Wechselt zum nächsten Bild"""
        if save != "gesichert":
          self.log_non_biometric("Manuell übersprungen")
        self.setFocus()
        if self.image_index < len(self.image_list) - 1:
            self.image_index += 1
            self.load_current_image()
        else:
            self.image_label.clear()
            self.info_label.clear()
            self.current_image = None
            self.current_shape = None
            QMessageBox.information(self, "Fertig", "Alle Bilder wurden bearbeitet.")

    def keyPressEvent(self, event):
        """Erlaubt manuelle Anpassung per Tastatur"""
        key = event.key()
        if key == Qt.Key_Plus:
            self.manual_adjust('scale_up')
        elif key == Qt.Key_Minus:
            self.manual_adjust('scale_down')
        elif key == Qt.Key_Left:
            self.manual_adjust('move_left')
        elif key == Qt.Key_Right:
            self.manual_adjust('move_right')
        elif key == Qt.Key_Up:
            self.manual_adjust('move_up')
        elif key == Qt.Key_Down:
            self.manual_adjust('move_down')
        elif key == Qt.Key_L:
            self.manual_adjust('rotate_left')
        elif key == Qt.Key_R:
            self.manual_adjust('rotate_right')
        elif key == Qt.Key_Return or key == Qt.Key_Enter:
            self.save_current_image()
        elif key == Qt.Key_Escape:
            self.next_image()

    def log_non_biometric(self, message):
        with open(self.log_file, "a", encoding="utf-8") as log:
            img_path = self.image_list[self.image_index]
            log.write(f"{img_path.name}: {message}\n")
    
    def apply_image_edits(self, img):
        """Wendet Gamma, Helligkeit, Kontrast und RGB-Korrektur an"""
        # Gamma
        gamma = self.gamma_slider.value() / 100.0
        if gamma != 1.0:
            invGamma = 1.0 / gamma
            table = np.array([((i / 255.0) ** invGamma) * 255 for i in np.arange(256)]).astype("uint8")
            img = cv2.LUT(img, table)
        # Helligkeit und Kontrast
        brightness = self.brightness_slider.value()
        contrast = self.contrast_slider.value() / 100.0
        img = cv2.convertScaleAbs(img, alpha=contrast, beta=brightness)
        # RGB-Korrektur
        r = self.r_slider.value()
        g = self.g_slider.value()
        b = self.b_slider.value()
        img = img.astype(np.int16)
        img[..., 0] = np.clip(img[..., 0] + b, 0, 255)
        img[..., 1] = np.clip(img[..., 1] + g, 0, 255)
        img[..., 2] = np.clip(img[..., 2] + r, 0, 255)
        img = img.astype(np.uint8)
        return img

    def magic_skin_correction(self):
        """Automatische Hautkorrektur (einfacher Weißabgleich + Glättung)"""
        if self.current_image is None:
            return
        processed = self.processor.process_image(
            self.current_image,
            self.current_shape,
            scale_override=self.scale_factor,
            offset_x=self.offset_x,
            offset_y=self.offset_y,
            rotation_angle=self.rotation_angle
        )
        # Weißabgleich
        result = cv2.xphoto.createSimpleWB().balanceWhite(processed)
        # Glättung (leichtes Bilateral-Filter)
        result = cv2.bilateralFilter(result, 9, 75, 75)
        # Werte auf die Slider übertragen (optional)
        self.gamma_slider.setValue(100)
        self.brightness_slider.setValue(0)
        self.contrast_slider.setValue(100)
        self.r_slider.setValue(0)
        self.g_slider.setValue(0)
        self.b_slider.setValue(0)
        # Zeige das Ergebnis
        processed_with_guides = self.processor.draw_biometric_guides(result)
        height, width, channel = processed_with_guides.shape
        bytes_per_line = 3 * width
        q_img = QImage(processed_with_guides.tobytes(), width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(q_img)
        self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

def main():
    """Startet die Anwendung"""
    app = QApplication(sys.argv)
    config = Config()
    qt_style = config.get("ui", "qt_style")
    if qt_style in QStyleFactory.keys():
        app.setStyle(qt_style)
    else:
        app.setStyle('Fusion')
    window = BiometricProcessorGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
