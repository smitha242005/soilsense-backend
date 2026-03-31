from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
import json
import os
import base64
import io

app = Flask(__name__)

# ── Allow your frontend website to call this backend ──────────
CORS(app, resources={r"/*": {"origins": "*"}})

# ── Load model only once at startup ───────────────────────────
model = None
index_to_class = {}

def load_model():
    global model, index_to_class
    try:
        import tensorflow as tf
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        model_path = os.path.join(BASE_DIR, 'best_model.h5')
        class_path = os.path.join(BASE_DIR, 'class_indices.json')

        if not os.path.exists(model_path):
            print("⚠️  best_model.h5 not found — running in simulation mode")
            return False

        print("Loading model from:", model_path)
        model = tf.keras.models.load_model(model_path)

        with open(class_path, 'r') as f:
            class_indices = json.load(f)

        # Flip: {"dry":0,"moderate":1,"wet":2} → {0:"dry",1:"moderate",2:"wet"}
        index_to_class = {v: k for k, v in class_indices.items()}
        print("✅ Model loaded. Classes:", index_to_class)
        return True

    except Exception as e:
        print("❌ Model load failed:", e)
        return False

model_loaded = load_model()

# ── Recommendation logic ───────────────────────────────────────
def get_recommendation(label, confidence):
    label_lower = label.lower()
    conf = float(confidence)

    if label_lower == 'dry':
        pct = int(10 + (100 - conf) * 0.2)
        return {
            "level": "Dry",
            "emoji": "🏜️",
            "moisture_percent": max(5, min(pct, 30)),
            "rec_type": "warn",
            "rec_title": "⚠️ Irrigation Required",
            "rec_text": "The soil is too dry. Water the field immediately to prevent crop stress and root damage."
        }
    elif label_lower == 'moderate':
        pct = int(35 + (conf - 50) * 0.3)
        return {
            "level": "Moderate",
            "emoji": "🌿",
            "moisture_percent": max(30, min(pct, 60)),
            "rec_type": "monitor",
            "rec_title": "🔵 Monitor Soil",
            "rec_text": "Soil moisture is at an acceptable level. Monitor again in 2 hours and irrigate if it drops below 30%."
        }
    else:  # wet
        pct = int(60 + (conf - 50) * 0.4)
        return {
            "level": "Wet",
            "emoji": "💧",
            "moisture_percent": max(55, min(pct, 95)),
            "rec_type": "ok",
            "rec_title": "✅ No Irrigation Needed",
            "rec_text": "The soil has sufficient moisture. No irrigation required. Ensure proper drainage to avoid waterlogging."
        }

# ── /predict endpoint ──────────────────────────────────────────
@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()

        if not data or 'image' not in data:
            return jsonify({'error': 'No image provided'}), 400

        image_data = data['image']
        if ',' in image_data:
            image_data = image_data.split(',')[1]

        if not model_loaded or model is None:
            import random
            options = ['dry', 'moderate', 'wet']
            label = random.choice(options)
            confidence = round(random.uniform(78, 95), 1)
            rec = get_recommendation(label, confidence)
            return jsonify({
                "success": True,
                "predicted_class": label.capitalize(),
                "confidence": confidence,
                "mode": "simulation",
                **rec
            })

        import tensorflow as tf
        from PIL import Image

        image_bytes = base64.b64decode(image_data)
        img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        img = img.resize((224, 224))

        img_array = np.array(img, dtype=np.float32)
        img_array = tf.keras.applications.mobilenet_v2.preprocess_input(img_array)
        img_array = np.expand_dims(img_array, axis=0)

        predictions = model.predict(img_array)
        class_idx = int(np.argmax(predictions[0]))
        confidence = round(float(np.max(predictions[0])) * 100, 1)

        label = index_to_class.get(class_idx, 'moderate')
        rec = get_recommendation(label, confidence)

        return jsonify({
            "success": True,
            "predicted_class": label.capitalize(),
            "confidence": confidence,
            "all_predictions": {
                index_to_class.get(i, str(i)): round(float(p) * 100, 1)
                for i, p in enumerate(predictions[0])
            },
            **rec
        })

    except Exception as e:
        print("Prediction error:", e)
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'SoilSense backend is running ✅',
        'model_loaded': model_loaded,
        'classes': index_to_class
    })

@app.route('/', methods=['GET'])
def home():
    return jsonify({'message': 'SoilSense API is live 🌱', 'model_ready': model_loaded})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
