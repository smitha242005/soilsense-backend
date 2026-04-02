from flask import Flask, request, jsonify
from flask_cors import CORS
import tensorflow as tf
import numpy as np
from PIL import Image
import io, json, base64, os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

print("Loading model...")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

keras_path = os.path.join(BASE_DIR, 'best_model.keras')
h5_path = os.path.join(BASE_DIR, 'best_model.h5')

if os.path.exists(keras_path):
    model = tf.keras.models.load_model(keras_path)
elif os.path.exists(h5_path):
    model = tf.keras.models.load_model(h5_path, compile=False)
else:
    raise FileNotFoundError("No model file found!")

print("✅ Model loaded!")

with open(os.path.join(BASE_DIR, 'class_indices.json')) as f:
    class_indices = json.load(f)
idx_to_label = {v: k for k, v in class_indices.items()}
print("Classes:", idx_to_label)

IMG_SIZE = (224, 224)
from tensorflow.keras.applications.resnet50 import preprocess_input

# ── Soil Info Dictionary ──
SOIL_INFO = {
    'Alluvial_Soil': {
        'display_name': 'Alluvial Soil',
        'description': 'Highly fertile soil deposited by rivers. Rich in minerals, nutrients and organic matter. Found mainly in river plains and deltas.',
        'moisture_level': 'Moderate (40-60%)',
        'ideal_moisture': 50,
        'crops': ['Rice', 'Wheat', 'Sugarcane', 'Cotton', 'Jute', 'Maize'],
        'characteristics': 'Light to medium texture, high fertility, good water retention',
        'found_in': 'River plains, Indo-Gangetic plain, coastal deltas'
    },
    'Black_Soil': {
        'display_name': 'Black Soil',
        'description': 'Dark clay soil also known as Black Cotton Soil or Regur. High water retention and rich in calcium, magnesium and iron.',
        'moisture_level': 'Low-Moderate (30-50%)',
        'ideal_moisture': 40,
        'crops': ['Cotton', 'Soybean', 'Wheat', 'Jowar', 'Sunflower', 'Tobacco'],
        'characteristics': 'High clay content, swells when wet, cracks when dry',
        'found_in': 'Deccan plateau, Maharashtra, Gujarat, Madhya Pradesh'
    },
    'Red_Soil': {
        'display_name': 'Red Soil',
        'description': 'Iron-rich reddish colored soil. Well drained but generally low in nutrients and organic matter.',
        'moisture_level': 'Low (20-40%)',
        'ideal_moisture': 30,
        'crops': ['Groundnut', 'Tobacco', 'Millets', 'Potato', 'Rice', 'Wheat'],
        'characteristics': 'Good drainage, low water retention, needs fertilizers',
        'found_in': 'Eastern and southern Deccan plateau, Tamil Nadu, Odisha'
    },
    'Clay': {
        'display_name': 'Clay Soil',
        'description': 'Heavy soil with very fine particles. Excellent nutrient content but poor drainage. Sticky when wet and hard when dry.',
        'moisture_level': 'High (50-70%)',
        'ideal_moisture': 60,
        'crops': ['Rice', 'Lettuce', 'Cabbage', 'Broccoli', 'Chard', 'Beans'],
        'characteristics': 'High nutrient content, poor drainage, slow to warm up',
        'found_in': 'River valleys, flood plains, low-lying areas'
    },
    'Laterite_Soil': {
        'display_name': 'Laterite Soil',
        'description': 'Formed in tropical regions with high rainfall. Rich in iron and aluminum oxides. Soft when wet, hard when dry.',
        'moisture_level': 'Moderate (35-55%)',
        'ideal_moisture': 45,
        'crops': ['Tea', 'Coffee', 'Cashew', 'Coconut', 'Rubber', 'Pineapple'],
        'characteristics': 'Low fertility, acidic, needs heavy fertilization',
        'found_in': 'Karnataka, Kerala, Tamil Nadu, Assam, Meghalaya'
    },
    'Loam_Soil': {
        'display_name': 'Loam Soil',
        'description': 'Ideal mix of sand, silt and clay. Best soil for farming with excellent drainage and water retention balance.',
        'moisture_level': 'Moderate (40-60%)',
        'ideal_moisture': 50,
        'crops': ['Almost all crops', 'Wheat', 'Corn', 'Vegetables', 'Fruits', 'Flowers'],
        'characteristics': 'Best soil for agriculture, balanced texture, high fertility',
        'found_in': 'Agricultural plains, temperate regions worldwide'
    },
    'Arid_Soil': {
        'display_name': 'Arid Soil',
        'description': 'Dry desert soil with very low organic matter and high salt content. Found in arid and semi-arid regions.',
        'moisture_level': 'Very Low (10-25%)',
        'ideal_moisture': 18,
        'crops': ['Millets', 'Barley', 'Cotton', 'Dates', 'Drought-resistant crops'],
        'characteristics': 'Sandy texture, low fertility, needs heavy irrigation',
        'found_in': 'Rajasthan, Gujarat desert regions, arid zones'
    },
    'Mountain_Soil': {
        'display_name': 'Mountain Soil',
        'description': 'Found in hilly and mountainous areas. Acidic in nature and rich in organic matter but shallow depth.',
        'moisture_level': 'High (50-70%)',
        'ideal_moisture': 60,
        'crops': ['Tea', 'Coffee', 'Fruits', 'Potatoes', 'Medicinal plants', 'Spices'],
        'characteristics': 'Acidic, rich in humus, shallow, prone to erosion',
        'found_in': 'Himalayas, Western Ghats, Northeastern hills'
    },
    'Yellow_Soil': {
        'display_name': 'Yellow Soil',
        'description': 'Yellow colored due to iron oxidation in hydrated form. Found in humid regions with moderate rainfall.',
        'moisture_level': 'Moderate (35-55%)',
        'ideal_moisture': 45,
        'crops': ['Rice', 'Sweet Potato', 'Corn', 'Tobacco', 'Groundnut'],
        'characteristics': 'Moderate fertility, good drainage, needs organic matter',
        'found_in': 'Humid subtropical regions, parts of South and East India'
    },
    'Cinder_Soil': {
        'display_name': 'Cinder Soil',
        'description': 'Volcanic origin soil with excellent drainage. Rich in minerals but low in organic matter.',
        'moisture_level': 'Low-Moderate (25-45%)',
        'ideal_moisture': 35,
        'crops': ['Grapes', 'Olives', 'Lavender', 'Herbs', 'Succulents', 'Cacti'],
        'characteristics': 'Excellent drainage, high mineral content, low water retention',
        'found_in': 'Volcanic regions, parts of Deccan plateau'
    }
}

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'error': 'No image provided'}), 400

        img_data = data['image']
        if ',' in img_data:
            img_data = img_data.split(',')[1]

        img_bytes = base64.b64decode(img_data)
        img = Image.open(io.BytesIO(img_bytes)).convert('RGB')
        img = img.resize(IMG_SIZE)

        arr = np.array(img, dtype=np.float32)
        arr = preprocess_input(arr)
        arr = np.expand_dims(arr, axis=0)

        preds = model.predict(arr)[0]
        pred_idx = int(np.argmax(preds))
        pred_label = idx_to_label[pred_idx]
        confidence = float(preds[pred_idx]) * 100

        soil = SOIL_INFO.get(pred_label, {})

        # Top 3 predictions
        top3_idx = np.argsort(preds)[::-1][:3]
        top3 = [
            {
                'soil': SOIL_INFO.get(idx_to_label[int(i)], {}).get('display_name', idx_to_label[int(i)]),
                'confidence': round(float(preds[i]) * 100, 1)
            }
            for i in top3_idx
        ]

        return jsonify({
            'success': True,
            'soil_type': pred_label,
            'display_name': soil.get('display_name', pred_label),
            'confidence': round(confidence, 1),
            'description': soil.get('description', ''),
            'moisture_level': soil.get('moisture_level', ''),
            'ideal_moisture': soil.get('ideal_moisture', 0),
            'crops': soil.get('crops', []),
            'characteristics': soil.get('characteristics', ''),
            'found_in': soil.get('found_in', ''),
            'top3': top3
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'model': 'ResNet50', 'classes': len(idx_to_label)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)