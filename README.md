# Biometrisches Passbild-Tool

Dieses Programm verarbeitet Fotos automatisch zu biometrischen Passbildern nach offiziellen Vorgaben. Es erkennt Gesichter, richtet sie korrekt aus, schneidet sie passend zu und prüft biometrische Anforderungen. Die Bedienung erfolgt über eine grafische Oberfläche.

## Funktionen

- **Automatisches Zuschneiden und Ausrichten** von Fotos zu biometrischen Passbildern
- **Gesichtserkennung** mit Dlib und OpenCV
- **Biometrische Prüfungen** (z.B. Augen offen, Kopfhaltung, Mund geschlossen)
- **Automatische Rotation** bei schiefen Bildern
- **Einstellbare Zielauflösung und Dateigröße**
- **Debug-Modus** mit Vorschau und Hilfslinien
- **Erweiterte Einstellungen** für alle Parameter
- **Verarbeitung ganzer Ordner** mit einem Klick
- **Manuelle Nachjustierung:**  
  Im interaktiven Modus kann das finale Bild zusätzlich angepasst werden:
  - **Verschieben des Bildausschnitts** mit den Pfeiltasten
  - **Skalieren** mit den Tasten `+` und `-`
  - **Rotation** des Bildes um jeweils 1 Grad mit den Tasten `l` (links) und `r` (rechts)

## Installation

1. **Python installieren**  
   Stelle sicher, dass Python 3.8 oder neuer installiert ist.

2. **Abhängigkeiten installieren**  
   Installiere die benötigten Pakete mit:
   ```
   pip install -r requirements.txt
   ```

3. **Modelldateien bereitstellen**  
   Lade die folgenden Dateien herunter und lege sie im `src/models/`-Verzeichnis ab:
   - `shape_predictor_68_face_landmarks.dat` (Dlib Landmark-Modell)
   - `haarcascade_frontalface_default.xml` (OpenCV Haar-Cascade)

4. **Programm starten**  
   Starte das Programm mit:
   ```
   python src/main.py
   ```

## Bedienung

1. **Eingabe- und Ausgabeordner wählen**  
   Wähle den Ordner mit den zu verarbeitenden Fotos und einen Zielordner für die fertigen Passbilder.

2. **Bildeinstellungen anpassen**  
   Lege Auflösung, Dateigröße und Namenserweiterung fest.

3. **Optionen wählen**  
   Aktiviere oder deaktiviere biometrische Prüfungen und den Debug-Modus nach Bedarf.

4. **Erweiterte Einstellungen**  
   Passe bei Bedarf die biometrischen Parameter und die Bildqualität über den Button „Erweiterte Einstellungen“ an.

5. **Verarbeitung starten**  
   Klicke auf „Verarbeitung starten“. Die fertigen Bilder werden im Ausgabeordner gespeichert. Nicht-biometrische Bilder werden protokolliert.

### Interaktiver Modus

Nach der automatischen Verarbeitung kann das finale Bild im interaktiven Modus manuell angepasst werden:

- **Ausschnitt verschieben:** Mit den Pfeiltasten (←, →, ↑, ↓)
- **Skalieren:** Mit `+` (größer) und `-` (kleiner)
- **Rotieren:** Mit `l` (1° nach links) und `r` (1° nach rechts)
- **Speichern:** Mit `Enter`
- **Abbrechen:** Mit `ESC`

## Hinweise

- Das Programm funktioniert am besten mit gut ausgeleuchteten, frontalen Porträtfotos.
- Im Debug-Modus kannst du die automatische Skalierung manuell nachjustieren.
- Alle Einstellungen werden in einer JSON-Datei gespeichert und können jederzeit angepasst werden.

## Lizenzen

Dieses Programm verwendet folgende Open-Source-Bibliotheken und Modelle:

- Dlib (Boost Software License 1.0)
- OpenCV (Apache License 2.0)
- PyQt5 (LGPL v3)
- NumPy (BSD License)

Die vollständigen Lizenztexte befinden sich im Ordner `licenses`.

**Hinweis zu PyQt5:**  
Die verwendeten Modelle (`shape_predictor_68_face_landmarks.dat` und `haarcascade_frontalface_default.xml`) unterliegen denselben Lizenzen wie die jeweilige Bibliothek.

---

**Erstellt von Jan Schneider © 2025**