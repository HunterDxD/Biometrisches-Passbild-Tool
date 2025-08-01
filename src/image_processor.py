import cv2
import numpy as np
from pathlib import Path
import dlib
import os
import sys

class BiometricImageProcessor:
    """Verarbeitet Bilder zu biometrischen Passbildern"""

    def __init__(self, target_size=(413, 531), max_file_size=500*1024, name_extension="",
                 debug_mode=True, auto_rotate=False, scal_check=True, eye_check=True, mouth_check=False, side_ratio_check=True, head_tilt_check=True,
                 config=None):
        # Zielgröße des Passbildes (Breite, Höhe)
        self.target_size = target_size
        # Maximale Dateigröße in Bytes
        self.max_file_size = max_file_size
        # Präfix für Ausgabedateien
        self.name_extension = name_extension
        # Debug-Modus für Vorschau und Hilfslinien
        self.debug_mode = debug_mode
        # Automatische Rotation aktivieren
        self.auto_rotate = auto_rotate
        # Skalierungskorrektur erlauben
        self.scal_check = scal_check
        # Prüfung auf offene Augen
        self.eye_check = eye_check
        # Prüfung auf geschlossenen Mund
        self.mouth_check = mouth_check
        # Prüfung auf frontale Ausrichtung
        self.side_ratio_check = side_ratio_check
        # Prüfung auf Kopfneigung
        self.head_tilt_check = head_tilt_check
        # Konfiguration laden
        self.config = config

        # Biometrische Parameter aus Konfiguration laden
        self.chin_to_eye_factor = self.config.get('biometric_checks', 'chin_to_eye_factor') 
        self.min_face_hight_factor = self.config.get('biometric_checks', 'min_face_hight') / 100
        self.max_face_hight_factor = self.config.get('biometric_checks', 'max_face_height') / 100
        self.chin_hight_factor = self.config.get('biometric_checks', 'chin_hight') / 100
        self.min_eye_hight_factor = self.config.get('biometric_checks', 'min_eye_hight') / 100
        self.max_eye_hight_factor = self.config.get('biometric_checks', 'max_eye_hight') / 100
        self.after_scale_factor = self.config.get('biometric_checks', 'after_scale')
        self.rotate_angle = self.config.get('biometric_checks', 'rotate_angle')  # Rotationswinkel in Grad
        self.move_step = int(self.config.get('biometric_checks', 'move_step'))  # Pixel pro Tastendruck

        # Hilfsfunktion für Ressourcenpfad (PyInstaller-kompatibel)
        def resource_path(relative_path):
            base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
            return os.path.join(base_path, relative_path)
    
        # Pfad zum Dlib-Landmark-Modell
        model_path = resource_path("src/shape_predictor_68_face_landmarks.dat")

        # Dlib-Modelle für Gesichtserkennung und präzise Landmark-Erkennung
        self.predictor = dlib.shape_predictor(model_path)
        self.detector = dlib.get_frontal_face_detector()
    

    def process_image(self, image, shape, scale_override=None, offset_x=0, offset_y=0, rotation_angle=0):
        """Schneidet das Bild nach biometrischen Vorgaben zu, mit optionalem Offset und Rotation"""
        target_w, target_h = self.target_size  # Zielbreite und -höhe

        # Bild rotieren, falls rotation_angle != 0
        if rotation_angle != 0:
            center = (image.shape[1] // 2, image.shape[0] // 2)
            rot_mat = cv2.getRotationMatrix2D(center, rotation_angle, 1.0)
            image = cv2.warpAffine(image, rot_mat, (image.shape[1], image.shape[0]))
            

        # Landmark-Koordinaten auslesen
        chin = np.array([shape.part(8).x, shape.part(8).y])  # Kinn
        brow = np.array([shape.part(27).x, shape.part(27).y])  # Augenbrauenmitte
        left_eye = np.mean([[shape.part(i).x, shape.part(i).y] for i in range(36, 42)], axis=0)
        right_eye = np.mean([[shape.part(i).x, shape.part(i).y] for i in range(42, 48)], axis=0)
        eyes_center = (left_eye + right_eye) / 2  # Mittelpunkt zwischen den Augen

        # Gesichtshöhe berechnen
        face_height = np.linalg.norm(chin - eyes_center) * self.chin_to_eye_factor

        # Ziel-Gesichtshöhe berechnen
        min_face_height = self.min_face_hight_factor * target_h
        max_face_height = self.max_face_hight_factor * target_h
        target_face_height = (min_face_height + max_face_height) / 2

        # Skalierungsfaktor bestimmen
        scale = target_face_height / face_height

        # Optional: manuelle Skalierung anwenden
        if scale_override is not None:
            scale = (target_face_height / face_height) * scale_override

        # Bild skalieren
        scaled_img = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_LANCZOS4)

        # Landmarks nach Skalierung anpassen
        def scale_point(pt): return np.array(pt) * scale
        chin_s = scale_point(chin)
        brow_s = scale_point(brow)
        eyes_center_s = scale_point(eyes_center)

        # Zielposition für das Kinn bestimmen
        chin_target_y = target_h * (1 - self.chin_hight_factor)

        # Zuschneidebereich berechnen (mit Offset)
        crop_top = int(round(chin_s[1] - chin_target_y)) + offset_y
        crop_bottom = crop_top + target_h
        crop_center_x = int(round(eyes_center_s[0])) + offset_x
        crop_left = crop_center_x - target_w // 2
        crop_right = crop_left + target_w

        # Zuschneidebereich an Bildränder anpassen
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

        # Bild zuschneiden
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
            # Bild als JPEG kodieren
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
        
        # Log-Datei für nicht-biometrische Bilder
        log_file = output_path / "nicht_biometrisch.txt"
        
        with open(log_file, "w", encoding="utf-8") as log:
            for img_path in input_path.glob('*.[jJ][pP][gG]'):
                try:
                    # Unicode-sicheres Einlesen
                    with open(img_path, 'rb') as f:
                        file_bytes = np.asarray(bytearray(f.read()), dtype=np.uint8)
                        image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
                    if image is None:
                        log.write(f"{img_path.name}: Bild konnte nicht geladen werden\n")
                        continue
                    
                    # Gesichtserkennung (nur Dlib)
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                    faces = self.detector(gray, 0)
                    
                    if len(faces) == 0:
                        log.write(f"{img_path.name}: Kein Gesicht gefunden\n")
                        continue
                    if len(faces) > 1:
                        log.write(f"{img_path.name}: Mehrere Gesichter gefunden, nur das erste wird verarbeitet\n")
                    
                    dlib_rect = faces[0]
                    shape = self.predictor(gray, dlib_rect)
                    
                    # Biometrische Anforderungen prüfen
                    is_valid, message = self.check_biometric_requirements(shape)
                    if not is_valid:
                        log.write(f"{img_path.name}: {message}\n")
                        continue

                    # Arbeitskopie des Bildes
                    working_image = image.copy()
                    
                    # Debug-Visualisierung anzeigen
                    if self.debug_mode:
                        debug_img = self.draw_debug_visualization(image, shape, dlib_rect)
                        if debug_img is None:
                            log.write(f"{img_path.name}: Gesicht zu groß oder zu nah am Bildrand\n")
                            continue
                        
                        cv2.imshow('1. Erkanntes Gesicht & Markierungen', debug_img)
                        if cv2.waitKey(0) == 27:  # ESC
                            cv2.destroyAllWindows()
                            log.write(f"{img_path.name}: Manuell übersprungen\n")
                            continue
                    else:
                        # Auch ohne Debug prüfen, ob das Gesicht passt
                        debug_img = self.draw_debug_visualization(image, shape, dlib_rect)
                        if debug_img is None:
                            log.write(f"{img_path.name}: Gesicht zu groß oder zu nah am Bildrand\n")
                            continue

                    # Automatische Rotation falls aktiviert
                    if self.auto_rotate:
                        working_image = self.auto_rotate_image(working_image, shape)
                        # Nach Rotation neue Gesichtserkennung (nur Dlib)
                        gray = cv2.cvtColor(working_image, cv2.COLOR_BGR2GRAY)
                        faces = self.detector(gray, 1)
                        if len(faces) == 1:
                            dlib_rect = faces[0]
                            shape = self.predictor(gray, dlib_rect)
                            if self.debug_mode:
                                debug_rotated = self.draw_debug_visualization(working_image, shape, dlib_rect)
                                cv2.imshow('2. Rotiertes Bild mit Markierungen', debug_rotated)
                                if cv2.waitKey(0) == 27:  # ESC
                                    cv2.destroyAllWindows()
                                    log.write(f"{img_path.name}: Manuell übersprungen\n")
                                    continue

                    # Bild zuschneiden und ggf. interaktiv nachjustieren
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
                    
                    # Dateigröße anpassen und speichern
                    encoded_img = self.adjust_jpeg_quality(processed, self.max_file_size)
                    output_file = output_path / f"{self.name_extension}{img_path.name}"
                    with open(output_file, 'wb') as f:
                        f.write(encoded_img)
                    
                    print(f"Erfolgreich gespeichert: {output_file.name}")
                
                except Exception as e:
                    log.write(f"{img_path.name}: Fehler - {str(e)}\n")
                    print(f"Fehler bei {img_path.name}: {str(e)}")
        return True
    
    def check_biometric_requirements(self, shape):
        """Prüft, ob das Gesicht biometrischen Anforderungen entspricht"""
        try:
            # Prüfung auf frontale Ausrichtung
            if self.side_ratio_check:
                left_eye_nose_dist = np.linalg.norm(
                    np.array([shape.part(36).x, shape.part(36).y]) - 
                    np.array([shape.part(31).x, shape.part(31).y])
                )
                right_eye_nose_dist = np.linalg.norm(
                    np.array([shape.part(45).x, shape.part(45).y]) - 
                    np.array([shape.part(35).x, shape.part(35).y])
                )
                side_ratio = left_eye_nose_dist / right_eye_nose_dist
                tolerance = self.config.get('biometric_checks', 'side_ratio_tolerance')
                if side_ratio < (1 - tolerance) or side_ratio > (1 + tolerance):
                    return False, f"Kopf nicht frontal ausgerichtet (Verhältnis: {side_ratio:.2f})"

            # Prüfung auf Kopfneigung
            if self.head_tilt_check:
                left_eye = np.mean([(shape.part(36+i).x, shape.part(36+i).y) for i in range(6)], axis=0)
                right_eye = np.mean([(shape.part(42+i).x, shape.part(42+i).y) for i in range(6)], axis=0)
                angle = np.degrees(np.arctan2(right_eye[1] - left_eye[1], right_eye[0] - left_eye[0]))
                max_tilt = self.config.get('biometric_checks', 'max_head_tilt')
                if abs(angle) > max_tilt:
                    return False, f"Kopfneigung zu stark: {angle:.1f}°"

            # Prüfung auf Mundöffnung
            if self.mouth_check:
                mouth_top = shape.part(62).y
                mouth_bottom = shape.part(66).y
                mouth_gap = mouth_bottom - mouth_top
                max_gap = self.config.get('biometric_checks', 'max_mouth_gap')
                if mouth_gap > max_gap:
                    return False, "Mund muss geschlossen sein"

            # Prüfung auf Augenöffnung
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
        """Berechnet das Verhältnis der Augenöffnung"""
        points = [(p.x, p.y) for p in eye_points]
        points = np.array(points)
        A = np.linalg.norm(points[1] - points[5])
        B = np.linalg.norm(points[2] - points[4])
        C = np.linalg.norm(points[0] - points[3])
        return (A + B) / (2.0 * C)

    def auto_rotate_image(self, image, shape):
        """Dreht das Bild so, dass die Augen waagrecht stehen"""
        left_eye = np.mean([(shape.part(36+i).x, shape.part(36+i).y) for i in range(6)], axis=0)
        right_eye = np.mean([(shape.part(42+i).x, shape.part(42+i).y) for i in range(6)], axis=0)
        angle = np.degrees(np.arctan2(right_eye[1] - left_eye[1], right_eye[0] - left_eye[0]))
        center = (image.shape[1] // 2, image.shape[0] // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, rotation_matrix, (image.shape[1], image.shape[0]))
        return rotated

    def draw_debug_visualization(self, image, shape, dlib_rect):
        """Zeichnet Hilfslinien und Markierungen ins Bild"""
        debug_img = image.copy()
        x, y, w, h = dlib_rect.left(), dlib_rect.top(), dlib_rect.width(), dlib_rect.height()

        # Biometrische Verhältnisse aus Konfiguration
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

        # Prüfen ob das Gesicht im Bereich liegt
        if (left < 0 or top < 0 or 
            right > image.shape[1] or 
            bottom > image.shape[0]):
            return None

        # Rechteck um das Gesicht (rot)
        cv2.rectangle(debug_img, (x, y), (x+w, y+h), (0, 0, 255), 2)

        # Dlib-Landmarks (gelb)
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

        # Biometrische Hilfslinien einzeichnen
        self.draw_biometric_guides(debug_img)
        
        return debug_img

    def draw_biometric_guides(self, image):
        """Zeichnet biometrische Hilfslinien ins Bild"""
        img = image.copy()
        h, w = img.shape[:2]

        # Kinn-Ziellinie
        chin_y = int(round(h * (1 - self.chin_hight_factor)))
        cv2.line(img, (0, chin_y), (w, chin_y), (255, 0, 255), 2)
        cv2.putText(img, f"Kinn ({self.chin_hight_factor * 100}%)", (10, chin_y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)

        # Gesichtshöhe (max/min)
        face_top_min = int(round(h * (1 - self.max_face_hight_factor)))
        face_top_max = int(round(h * (1 - self.min_face_hight_factor)))
        cv2.line(img, (0, face_top_min), (w, face_top_min), (0, 255, 255), 1)
        cv2.line(img, (0, face_top_max), (w, face_top_max), (0, 255, 255), 1)
        cv2.putText(img, f"Gesicht max ({self.max_face_hight_factor * 100}%)", (10, face_top_min+20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        cv2.putText(img, f"Gesicht min ({self.min_face_hight_factor * 100}%)", (10, face_top_max+20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        # Augenbereich (max/min)
        eye_min = int(round(h * (1 - self.max_eye_hight_factor)))
        eye_max = int(round(h * (1 - self.min_eye_hight_factor)))
        cv2.line(img, (0, eye_min), (w, eye_min), (0, 128, 255), 1)
        cv2.line(img, (0, eye_max), (w, eye_max), (0, 128, 255), 1)
        cv2.putText(img, f"Augen max ({self.max_eye_hight_factor * 100}%)", (10, eye_min+20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 128, 255), 1)
        cv2.putText(img, f"Augen min ({self.min_eye_hight_factor * 100}%)", (10, eye_max+20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 128, 255), 1)

        return img

    def interactive_finalize(self, image, shape):
        """Erlaubt interaktives Nachjustieren der Skalierung, Verschiebung und Rotation"""
        scale_factor = 1.0
        offset_x = 0
        offset_y = 0
        rotation_angle = 0  # Rotationswinkel in Grad

        while True:
            processed = self.process_image(
                image, shape,
                scale_override=scale_factor,
                offset_x=offset_x,
                offset_y=offset_y,
                rotation_angle=rotation_angle  
            )
            processed_with_guides = self.draw_biometric_guides(processed)
            cv2.imshow('3. Finales Bild (mit +/- skalieren, Pfeiltasten verschieben, l/r rotieren, ENTER speichern, ESC abbrechen)', processed_with_guides)
            key = cv2.waitKey(0)
            if key == 27:  # ESC
                cv2.destroyAllWindows()
                return None
            elif key in [13, 10]:  # ENTER
                cv2.destroyAllWindows()
                return processed
            elif key == 43:  # +
                scale_factor *= self.after_scale_factor
            elif key == 45:  # -
                scale_factor /= self.after_scale_factor
            elif key == 2:  # Links
                offset_x += self.move_step
            elif key == 3:  # Rechts
                offset_x -= self.move_step
            elif key == 0:  # Hoch
                offset_y += self.move_step
            elif key == 1:  # Runter
                offset_y -= self.move_step
            elif key == ord('l'):  # l für links drehen
                rotation_angle += self.rotate_angle
            elif key == ord('r'):  # r für rechts drehen
                rotation_angle -= self.rotate_angle
            else:
                print(f"Unbekannte Taste: {key}.")
            cv2.destroyWindow('3. Finales Bild (mit +/- skalieren, Pfeiltasten verschieben, l/r rotieren, ENTER speichern, ESC abbrechen)')

