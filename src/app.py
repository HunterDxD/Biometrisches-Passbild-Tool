from flask import Flask, render_template, request, jsonify
from image_processor import BiometricImageProcessor
from config import Config
import cv2
import numpy as np
import base64
import dlib

app = Flask(__name__)
config = Config()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_image_endpoint():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        try:
            in_memory_file = file.read()
            file_bytes = np.frombuffer(in_memory_file, np.uint8)
            image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            if image is None:
                return jsonify({'error': 'Could not decode image'}), 400

            processor = BiometricImageProcessor(
                target_size=(413, 531),
                max_file_size=500 * 1024,
                config=config,
                debug_mode=False,
                auto_rotate=True,
                scal_check=False,
                eye_check=True,
                mouth_check=False,
                side_ratio_check=True,
                head_tilt_check=True
            )

            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            faces = processor.detector(gray, 1)

            if len(faces) == 0:
                return jsonify({'error': 'No face detected'}), 400

            face = faces[0]
            shape = processor.predictor(gray, face)

            is_valid, message = processor.check_biometric_requirements(shape)
            if not is_valid:
                return jsonify({'error': f'Biometric check failed: {message}'}), 400

            processed_image = processor.process_image(image, shape)

            encoded_img_bytes = processor.adjust_jpeg_quality(processed_image, processor.max_file_size)

            img_str = base64.b64encode(encoded_img_bytes).decode('utf-8')

            return jsonify({'success': True, 'image': f'data:image/jpeg;base64,{img_str}'})

        except dlib.error as e:
             return jsonify({'error': f'Dlib model error. Make sure shape_predictor_68_face_landmarks.dat is in the src/ directory. Details: {e}'}), 500
        except Exception as e:
            return jsonify({'error': f'An unexpected error occurred: {e}'}), 500

    return jsonify({'error': 'Something went wrong'}), 500


if __name__ == '__main__':
    app.run(debug=True)
