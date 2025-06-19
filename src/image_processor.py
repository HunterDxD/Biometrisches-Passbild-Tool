import cv2
import numpy as np
from pathlib import Path
import dlib
import os
import sys

class BiometricImageProcessor:

    


    def __init__(self, target_size=(413, 531), max_file_size=500*1024, 
                 debug_mode=True, auto_rotate=False, scal_check=True, eye_check=True, mouth_check=False, side_ratio_check=True, head_tilt_check=True,
                 config=None):
        """
        Initialisiert den Bildprozessor
        :param target_size: Tuple (width, height) für die Zielauflösung
        :param max_file_size: Maximale Dateigröße in Bytes
        :param debug_mode: Wenn True, werden Vorschaubilder angezeigt
        :param auto_rotate: Automatische Rotation aktivieren/deaktivieren
        :param auto_contrast: Automatischer Kontrast aktivieren/deaktivieren
        """
        self.target_size = target_size
        self.max_file_size = max_file_size
        self.debug_mode = debug_mode
        self.auto_rotate = auto_rotate
        self.scal_check = scal_check
        self.eye_check = eye_check
        self.mouth_check = mouth_check
        self.side_ratio_check = side_ratio_check
        self.head_tilt_check = head_tilt_check
        self.config = config

        # Lade Konfiguration und berechne biometrische Parameter 
        self.chin_to_eye_factor = self.config.get('biometric_checks', 'chin_to_eye_factor') 
        self.min_face_hight_factor = self.config.get('biometric_checks', 'min_face_hight') / 100
        self.max_face_hight_factor = self.config.get('biometric_checks', 'max_face_height') / 100
        self.chin_hight_factor = self.config.get('biometric_checks', 'chin_hight') / 100
        self.min_eye_hight_factor = self.config.get('biometric_checks', 'min_eye_hight') / 100
        self.max_eye_hight_factor = self.config.get('biometric_checks', 'max_eye_hight') / 100
        self.after_scale_factor = self.config.get('biometric_checks', 'after_scale')

        def resource_path(relative_path):
            """Gibt den Pfad zur Datei, auch wenn eingefroren durch PyInstaller."""
            base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
            return os.path.join(base_path, relative_path)
    
        model_path = resource_path("src/shape_predictor_68_face_landmarks.dat")
        cascade_path = resource_path("src/haarcascade_frontalface_default.xml")

        # Lade den Gesichtserkennungs-Klassifikator
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + cascade_path
        )

        # Dlib für präzisere Gesichtserkennung
        self.predictor = dlib.shape_predictor(model_path)
        self.detector = dlib.get_frontal_face_detector()
    

    def process_image(self, image, shape, scale_override=None):
        """
        Schneidet das Bild so zu, dass:
        - Das Kinn (Landmark 8) 13,82% vom unteren Bildrand entfernt ist
        - Die Gesichtshöhe (Kinn bis Augenbrauenmitte, Landmark 27) zwischen 86,02% und 94,85% des Bildes liegt
        - Die Augenmitte zwischen 48,77% und 71,04% des Bildes liegt (von unten nach oben)
        """
        # Zielgrößen
        target_w, target_h = self.target_size

        # Landmark-Koordinaten
        chin = np.array([shape.part(8).x, shape.part(8).y])
        brow = np.array([shape.part(27).x, shape.part(27).y])
        left_eye = np.mean([[shape.part(i).x, shape.part(i).y] for i in range(36, 42)], axis=0)
        right_eye = np.mean([[shape.part(i).x, shape.part(i).y] for i in range(42, 48)], axis=0)
        eyes_center = (left_eye + right_eye) / 2

        # Gesichtshöhe (Kinn bis Augenlinie)
        face_height = np.linalg.norm(chin - eyes_center) * self.chin_to_eye_factor # optional realistischer Faktor

        # Ziel: Gesichtshöhe auf 90% (Mittelwert) der Bildhöhe skalieren
        min_face_height = self.min_face_hight_factor * target_h
        max_face_height = self.max_face_hight_factor * target_h
        target_face_height = (min_face_height + max_face_height) / 2

        scale = target_face_height / face_height

        # <--- HIER scale_override anwenden!
        if scale_override is not None:
            scale = (target_face_height / face_height) * scale_override

        # Bild skalieren
        scaled_img = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_LANCZOS4)

        # Landmarks nach Skalierung anpassen
        def scale_point(pt): return np.array(pt) * scale
        chin_s = scale_point(chin)
        brow_s = scale_point(brow)
        eyes_center_s = scale_point(eyes_center)

        # Ziel: Kinn 13,82% vom unteren Rand (also 86,18% von oben)
        chin_target_y = target_h * (1 - self.chin_hight_factor)

        # Zuschneidebereich so wählen, dass das Kinn an chin_target_y liegt
        crop_top = int(round(chin_s[1] - chin_target_y))
        crop_bottom = crop_top + target_h
        crop_center_x = int(round(eyes_center_s[0]))
        crop_left = crop_center_x - target_w // 2
        crop_right = crop_left + target_w

        # Bildränder prüfen
        h_s, w_s = scaled_img.shape[:2]
        if crop_top < 0:
            crop_top = 0
            crop_bottom = target_h
        if crop_bottom > h_s:
            crop_bottom = h_s
            crop_top = h_s - target_h
        if crop_left < 0:
            crop_left = 0
            crop_right = target_w
        if crop_right > w_s:
            crop_right = w_s
            crop_left = w_s - target_w

        # Zuschneiden
        cropped = scaled_img[crop_top:crop_bottom, crop_left:crop_right]

        # Falls das Bild zu klein ist, mit weiß auffüllen
        if cropped.shape[0] != target_h or cropped.shape[1] != target_w:
            result = np.ones((target_h, target_w, 3), dtype=np.uint8) * 255
            y_offset = max(0, (target_h - cropped.shape[0]) // 2)
            x_offset = max(0, (target_w - cropped.shape[1]) // 2)
            result[y_offset:y_offset+cropped.shape[0], x_offset:x_offset+cropped.shape[1]] = cropped
            cropped = result

        return cropped

    def adjust_jpeg_quality(self, image, max_size):
        """Passt die JPEG-Qualität an, um die Zieldateigröße zu erreichen"""
        quality = int(self.config.get('image_quality', 'start_jpeg_quality'))
        min_quality = int(self.config.get('image_quality', 'min_jpeg_quality'))
        quality_step = int(self.config.get('image_quality', 'quality_step'))
        
        while quality > min_quality:
            # Encode image to JPEG
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
            _, encoded_img = cv2.imencode('.jpg', image, encode_param)
            
            if encoded_img.nbytes <= max_size:
                return encoded_img
            
            quality -= quality_step
            
        return encoded_img

    def process_directory(self, input_dir, output_dir):
        """Verarbeitet alle Bilder in einem Verzeichnis"""
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Erstelle Log-Datei für nicht-biometrische Bilder
        log_file = output_path / "nicht_biometrisch.txt"
        
        with open(log_file, "w", encoding="utf-8") as log:
            for img_path in input_path.glob('*.[jJ][pP][gG]'):
                try:
                    print(f"Verarbeite {img_path.name}...")
                    image = cv2.imread(str(img_path))
                    if image is None:
                        continue
                    
                    # Gesichtserkennung
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                    scale_factor = self.config.get('face_detection', 'scale_factor')
                    min_neighbors = self.config.get('face_detection', 'min_neighbors')
                    faces = self.face_cascade.detectMultiScale(gray, scale_factor, int(min_neighbors))
                    
                    if len(faces) != 1:
                        log.write(f"{img_path.name}: Kein eindeutiges Gesicht gefunden\n")
                        continue
                    
                    face_coords = faces[0]
                    x, y, w, h = face_coords
                    
                    # Dlib Landmarks erkennen
                    dlib_rect = dlib.rectangle(left=x, top=y, right=x+w, bottom=y+h)
                    shape = self.predictor(gray, dlib_rect)
                    
                    # Biometrische Anforderungen prüfen
                    is_valid, message = self.check_biometric_requirements(shape)
                    if not is_valid:
                        log.write(f"{img_path.name}: {message}\n")
                        continue

                    # Arbeitskopie des Bildes erstellen
                    working_image = image.copy()
                    
                    # Debug-Visualisierung des ursprünglichen Bildes
                    if self.debug_mode:
                        debug_img = self.draw_debug_visualization(image, shape, face_coords)
                        if debug_img is None:
                            log.write(f"{img_path.name}: Gesicht zu groß oder zu nah am Bildrand\n")
                            continue
                        
                        cv2.imshow('1. Erkanntes Gesicht & Markierungen', debug_img)
                        if cv2.waitKey(0) == 27:  # ESC
                            cv2.destroyAllWindows()
                            log.write(f"{img_path.name}: Manuell übersprungen\n")
                            continue
                    else:
                        # Auch ohne Debug-Mode prüfen ob das Gesicht passt
                        debug_img = self.draw_debug_visualization(image, shape, face_coords)
                        if debug_img is None:
                            log.write(f"{img_path.name}: Gesicht zu groß oder zu nah am Bildrand\n")
                            continue

                    # Auto-Rotation wenn aktiviert
                    if self.auto_rotate:
                        working_image = self.auto_rotate_image(working_image, shape)
                        
                        # Nach Rotation neue Gesichtserkennung
                        gray = cv2.cvtColor(working_image, cv2.COLOR_BGR2GRAY)
                        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
                        if len(faces) == 1:
                            face_coords = faces[0]
                            dlib_rect = dlib.rectangle(left=face_coords[0], 
                                                    top=face_coords[1], 
                                                    right=face_coords[0]+face_coords[2], 
                                                    bottom=face_coords[1]+face_coords[3])
                            shape = self.predictor(gray, dlib_rect)
                            
                            if self.debug_mode:
                                debug_rotated = self.draw_debug_visualization(working_image, shape, face_coords)
                                cv2.imshow('2. Rotiertes Bild mit Markierungen', debug_rotated)
                                if cv2.waitKey(0) == 27:  # ESC
                                    cv2.destroyAllWindows()
                                    log.write(f"{img_path.name}: Manuell übersprungen\n")
                                    continue

                    # Bild zuschneiden
                    try:
                        if self.debug_mode or self.scal_check:
                            processed = self.interactive_finalize(working_image, shape)
                            if processed is None:
                                log.write(f"{img_path.name}: Manuell übersprungen\n")
                                continue
                        else:
                            processed = self.process_image(working_image, shape)
                    except ValueError as ve:
                        log.write(f"{img_path.name}: {str(ve)}\n")
                        continue
                    
                    #if self.debug_mode:
                    #    cv2.imshow('3. Finales Bild', processed_with_guides)
                    #    if cv2.waitKey(0) == 27:  # ESC
                    #        cv2.destroyAllWindows()
                    #        log.write(f"{img_path.name}: Manuell übersprungen\n")
                    #        continue
                    #    cv2.destroyAllWindows()
                
                    # Dateigröße anpassen und speichern
                    encoded_img = self.adjust_jpeg_quality(processed, self.max_file_size)
                    output_file = output_path / f"biometric_{img_path.name}"
                    with open(output_file, 'wb') as f:
                        f.write(encoded_img)
                    
                    print(f"Erfolgreich gespeichert: {output_file.name}")
                
                except Exception as e:
                    log.write(f"{img_path.name}: Fehler - {str(e)}\n")
                    print(f"Fehler bei {img_path.name}: {str(e)}")
        return True
    
    def check_biometric_requirements(self, shape):
        """Überprüft die biometrischen Anforderungen"""
        try:
            # Frontale Ausrichtung prüfen
            if self.side_ratio_check:
                left_eye_nose_dist = np.linalg.norm(
                    np.array([shape.part(36).x, shape.part(36).y]) - 
                    np.array([shape.part(31).x, shape.part(31).y])
                )
                right_eye_nose_dist = np.linalg.norm(
                    np.array([shape.part(45).x, shape.part(45).y]) - 
                    np.array([shape.part(35).x, shape.part(35).y])
                )
                
                # Verhältnis mit Toleranz aus Config
                side_ratio = left_eye_nose_dist / right_eye_nose_dist
                tolerance = self.config.get('biometric_checks', 'side_ratio_tolerance')
                if side_ratio < (1 - tolerance) or side_ratio > (1 + tolerance):
                    return False, f"Kopf nicht frontal ausgerichtet (Verhältnis: {side_ratio:.2f})"

            # Kopfneigung mit Max-Winkel aus Config
            if self.head_tilt_check:
                left_eye = np.mean([(shape.part(36+i).x, shape.part(36+i).y) for i in range(6)], axis=0)
                right_eye = np.mean([(shape.part(42+i).x, shape.part(42+i).y) for i in range(6)], axis=0)
                angle = np.degrees(np.arctan2(right_eye[1] - left_eye[1], right_eye[0] - left_eye[0]))
                
                max_tilt = self.config.get('biometric_checks', 'max_head_tilt')
                if abs(angle) > max_tilt:
                    return False, f"Kopfneigung zu stark: {angle:.1f}°"

            # Mund-Öffnung aus Config
            if self.mouth_check:
                mouth_top = shape.part(62).y
                mouth_bottom = shape.part(66).y
                mouth_gap = mouth_bottom - mouth_top
                max_gap = self.config.get('biometric_checks', 'max_mouth_gap')
                if mouth_gap > max_gap:
                    return False, "Mund muss geschlossen sein"

            # Augen-Öffnung aus Config
            if self.eye_check:
                left_eye_ratio = self._eye_aspect_ratio([shape.part(i) for i in range(36,42)])
                right_eye_ratio = self._eye_aspect_ratio([shape.part(i) for i in range(42,48)])
                min_eye_ratio = self.config.get('biometric_checks', 'min_eye_ratio')
                if left_eye_ratio < min_eye_ratio or right_eye_ratio < min_eye_ratio:
                    return False, "Augen müssen geöffnet sein"

            return True, "OK"
        except Exception as e:
            if self.debug_mode:
                print(f"Debug: Fehler in check_biometric_requirements: {str(e)}")
            return False, f"Fehler bei Gesichtserkennung: {str(e)}"

    def _eye_aspect_ratio(self, eye_points):
        """Berechnet Augenöffnung"""
        points = [(p.x, p.y) for p in eye_points]
        points = np.array(points)
        
        A = np.linalg.norm(points[1] - points[5])
        B = np.linalg.norm(points[2] - points[4])
        C = np.linalg.norm(points[0] - points[3])
        return (A + B) / (2.0 * C)

    def auto_rotate_image(self, image, shape):
        """Rotiert das Bild basierend auf Augenposition"""
        left_eye = np.mean([(shape.part(36+i).x, shape.part(36+i).y) for i in range(6)], axis=0)
        right_eye = np.mean([(shape.part(42+i).x, shape.part(42+i).y) for i in range(6)], axis=0)
        
        angle = np.degrees(np.arctan2(right_eye[1] - left_eye[1], right_eye[0] - left_eye[0]))
        
        center = (image.shape[1] // 2, image.shape[0] // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, rotation_matrix, (image.shape[1], image.shape[0]))
        
        return rotated

    def draw_debug_visualization(self, image, shape, face_coords):
        """Zeichnet alle Debug-Markierungen ins Bild, inkl. Ziel-Linien für Kinn, Augen und Gesichtshöhe"""
        debug_img = image.copy()
        x, y, w, h = face_coords

        # Biometrische Verhältnisse aus Konfiguration laden
        head_height = int(h * self.config.get('face_detection', 'head_height_factor'))
        total_height = int(h * self.config.get('face_detection', 'total_height_factor'))
        width = int(total_height * self.config.get('face_detection', 'width_ratio'))
        face_center_x = x + w//2
        face_center_y = y + int(h * 0.4)

        # Zuschnittgrenzen berechnen
        left = face_center_x - width//2
        top = face_center_y - int(total_height * 0.4)
        right = left + width
        bottom = top + total_height

        # Prüfen ob das Gesicht in den Grenzen liegt
        if (left < 0 or top < 0 or 
            right > image.shape[1] or 
            bottom > image.shape[0]):
            return None  # Keine Visualisierung wenn Gesicht nicht passt

        # Gesichtsrechteck (rot)
        cv2.rectangle(debug_img, (x, y), (x+w, y+h), (0, 0, 255), 2)

        # Dlib Landmarks einzeichnen (gelb)
        for i in range(68):
            point = (shape.part(i).x, shape.part(i).y)
            cv2.circle(debug_img, point, 2, (0, 255, 255), -1)

        # Zuschnittbereich (grün)
        cv2.rectangle(debug_img, 
                    (left, top), 
                    (right, bottom), 
                    (0, 255, 0), 2)

        # Gesichtsmitte (blau)
        cv2.circle(debug_img, (face_center_x, face_center_y), 5, (255, 0, 0), -1)

        # --- Ziel-Linien einzeichnen ---
        target_w, target_h = self.target_size
        self.draw_biometric_guides(debug_img)
        
        return debug_img

    def draw_biometric_guides(self, image):
        img = image.copy()
        h, w = img.shape[:2]

        # Kinn-Ziellinie (13,82% vom unteren Rand)
        chin_y = int(round(h * (1 - self.chin_hight_factor)))
        cv2.line(img, (0, chin_y), (w, chin_y), (255, 0, 255), 2)
        cv2.putText(img, f"Kinn ({self.chin_hight_factor * 100}%)", (10, chin_y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)

        # Gesichtshöhe (86,02% bis 94,85% von unten)
        face_top_min = int(round(h * (1 - self.max_face_hight_factor)))
        face_top_max = int(round(h * (1 - self.min_face_hight_factor)))
        cv2.line(img, (0, face_top_min), (w, face_top_min), (0, 255, 255), 1)
        cv2.line(img, (0, face_top_max), (w, face_top_max), (0, 255, 255), 1)
        cv2.putText(img, f"Gesicht max ({self.max_face_hight_factor * 100}%)", (10, face_top_min+20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        cv2.putText(img, f"Gesicht min ({self.min_face_hight_factor * 100}%)", (10, face_top_max+20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        # Augenbereich (48,77% bis 71,04% von unten)
        eye_min = int(round(h * (1 - self.max_eye_hight_factor)))
        eye_max = int(round(h * (1 - self.min_eye_hight_factor)))
        cv2.line(img, (0, eye_min), (w, eye_min), (0, 128, 255), 1)
        cv2.line(img, (0, eye_max), (w, eye_max), (0, 128, 255), 1)
        cv2.putText(img, f"Augen max ({self.max_eye_hight_factor * 100}%)", (10, eye_min+20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 128, 255), 1)
        cv2.putText(img, f"Augen min ({self.min_eye_hight_factor * 100}%)", (10, eye_max+20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 128, 255), 1)

        return img

    def interactive_finalize(self, image, shape):
        """
        Zeigt das finale Bild mit Hilfslinien und erlaubt interaktives Nachjustieren der Skalierung.
        + / - : Gesicht größer/kleiner skalieren (Kinn bleibt an Kinnlinie)
        ESC  : Abbrechen
        ENTER: Übernehmen
        """
        scale_factor = 1.0
        while True:
            processed = self.process_image(image, shape, scale_override=scale_factor)
            processed_with_guides = self.draw_biometric_guides(processed)
            cv2.imshow('3. Finales Bild (mit +/- skalieren, ENTER speichern, ESC abbrechen)', processed_with_guides)
            key = cv2.waitKey(0)
            if key == 27:  # ESC
                cv2.destroyAllWindows()
                return None  # Abbruch
            elif key in [13, 10]:  # ENTER
                cv2.destroyAllWindows()
                return processed  # Übernehmen
            elif key == 43:  # +
                scale_factor *= self.after_scale_factor  # Gesicht größer
                print("Key pressed:", key)

            elif key == 45:  # -
                scale_factor /= self.after_scale_factor  # Gesicht kleiner
                print("Key pressed:", key)

            # Fenster nach jedem Tastendruck offen lassen
            cv2.destroyWindow('3. Finales Bild (mit +/- skalieren, ENTER speichern, ESC abbrechen)')

