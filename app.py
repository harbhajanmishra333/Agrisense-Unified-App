import os
import uuid
import base64
import json
import requests
import pandas as pd
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime

# -------------------------
# OpenRouter API CONFIG
# -------------------------
OPENROUTER_API_KEY = "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"

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

OPENROUTER_HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "HTTP-Referer": "http://localhost",
    "X-Title": "AgriSense",
    "Content-Type": "application/json"
}

def query_openrouter(prompt, model="openai/gpt-oss-20b:free"):
    """Reliable free-model OpenRouter caller"""
    try:
        response = requests.post(
            OPENROUTER_API_URL,
            headers=OPENROUTER_HEADERS,
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are an agricultural expert."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2
            },
            timeout=20
        )

        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]

        return content.strip() if content else None

    except Exception as e:
        print("OpenRouter API Error:", e)
        return None


# -------------------------
# FLASK APP CONFIG
# -------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'change_this_in_production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agrisense.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

os.makedirs("uploads/plant_disease", exist_ok=True)
os.makedirs("uploads/soil_type", exist_ok=True)

# -------------------------
# USER MODEL
# -------------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# -------------------------
# CROP RECOMMENDATION
# -------------------------
def get_crop_recommendation(soil_data):

    prompt = f"""
You are an agricultural expert. Your outputs MUST be deterministic.

Based on the given soil & environmental parameters, select the MOST suitable crop ONLY from this fixed list:

["Wheat", "Rice", "Maize", "Sugarcane", "Cotton", "Pulses", "Groundnut", "Bajra", "Mustard", "Barley", "Jute"]

Evaluate each crop on a 0–100 suitability scale using:
- Nitrogen (N): {soil_data['N']}
- Phosphorus (P): {soil_data['P']}
- Potassium (K): {soil_data['K']}
- Temperature: {soil_data['temperature']}
- Humidity: {soil_data['humidity']}
- pH: {soil_data['ph']}
- Rainfall: {soil_data['rainfall']}

RULES FOR CONSISTENT OUTPUT:
1. ALWAYS choose the crop with the highest suitability score.
2. NO creativity, NO randomness.
3. NO extra text — ONLY JSON.
4. Additional recommendations must be fixed and factual.

Return ONLY this exact JSON structure:
{{
    "crop": "Crop name",
    "reason": "Short fixed explanation",
    "additional_recommendations": ["Soil improvement tip", "Basic fertilizer advice"]
}}
"""

    # Use deterministic model + zero randomness
    response = query_openrouter(prompt, model="openai/gpt-oss-20b:free")  # BEST FREE MODEL
    # you may also use → model="openai/gpt-oss-20b:free" but Gemma is more stable

    if not response or not isinstance(response, str):
        return {
            "crop": "Unknown",
            "reason": "AI returned no response",
            "additional_recommendations": []
        }

    # Remove markdown fencing if present
    cleaned = (
        response.replace("```json", "")
                .replace("```", "")
                .strip()
    )

    # Extract pure JSON (protective measure)
    if "{" in cleaned and "}" in cleaned:
        cleaned = cleaned[cleaned.index("{"): cleaned.rindex("}") + 1]

    try:
        return json.loads(cleaned)
    except Exception as e:
        print("JSON parse error:", e)
        print("AI RAW →", response)
        return {
            "crop": "Unknown",
            "reason": "Could not parse JSON",
            "additional_recommendations": []
        }


# -------------------------
# ROUTES
# -------------------------
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


# -------------------------
# AUTH
# -------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm = request.form.get("confirm_password")

        if password != confirm:
            flash("Passwords do not match!", "danger")
            return redirect(url_for("register"))

        if User.query.filter_by(username=username).first():
            flash("Username already taken!", "danger")
            return redirect(url_for("register"))

        if User.query.filter_by(email=email).first():
            flash("Email already registered!", "danger")
            return redirect(url_for("register"))

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash("Registration successful! Please login.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password!", "danger")

    return render_template("login.html")


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template("dashboard.html", username=current_user.username)


# -------------------------
# CROP RECOMMENDATION PAGE
# -------------------------
@app.route('/crop-recommendation')
@login_required
def crop_recommendation():
    return render_template("crop_recommendation.html")


@app.route('/predict-crop', methods=['POST'])
@login_required
def predict_crop():
    try:
        data = request.get_json()
        soil_data = {
            'N': float(data['N']),
            'P': float(data['P']),
            'K': float(data['K']),
            'temperature': float(data['temperature']),
            'humidity': float(data['humidity']),
            'ph': float(data['ph']),
            'rainfall': float(data['rainfall'])
        }

        prediction = get_crop_recommendation(soil_data)

        return jsonify({"success": True, "prediction": prediction})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# -------------------------
# CROP YIELD PREDICTION
# -------------------------
@app.route('/crop-yield')
@login_required
def crop_yield():
    try:
        df = pd.read_csv("../crop_yield3/yield.csv")
        df.columns = df.columns.str.strip()  # FIX: remove accidental spaces in headers

        categories = {
            'State': sorted(df['State'].fillna('').unique().tolist()),
            'District': sorted(df['District'].fillna('').unique().tolist()),
            'Season': sorted(df['Season'].fillna('').unique().tolist()),
            'Crop': sorted(df['Crop'].fillna('').unique().tolist())
        }
    except Exception as e:
        print("Yield load error:", e)
        categories = {}

    return render_template("crop_yield.html", categories=categories)



@app.route('/predict-yield', methods=['POST'])
@login_required
def predict_yield():
    try:
        data = request.form.to_dict()

        prompt = f"""
        You are an expert agricultural data analyst.

        Estimate crop yield using the following inputs:

        State: {data.get('State')}
        District: {data.get('District')}
        Season: {data.get('Season')}
        Crop: {data.get('Crop')}
        Crop Year: {data.get('Crop_Year')}
        Area: {data.get('Area')} hectares

        Respond ONLY with valid JSON in this exact format:

        {{
            "estimated_yield": 0.0,
            "confidence": "High/Medium/Low",
            "factors": ["factor1", "factor2"],
            "recommendations": ["rec1", "rec2"]
        }}

        DO NOT return explanations, DO NOT add text outside the JSON.
        """

        # Use free model
        raw = query_openrouter(prompt, model="openai/gpt-oss-20b:free")

        if not raw:
            return jsonify({"success": False, "error": "AI returned no response"}), 500

        # Remove markdown fences
        cleaned = (
            raw.replace("```json", "")
               .replace("```", "")
               .strip()
        )

        # Extract JSON inside text safely
        if "{" in cleaned and "}" in cleaned:
            cleaned = cleaned[cleaned.index("{"): cleaned.rindex("}") + 1]

        try:
            result = json.loads(cleaned)
        except Exception as e:
            print("JSON Parse Error:", e)
            print("RAW RESPONSE:", raw)
            return jsonify({"success": False, "error": "JSON parse failure"}), 500

        # Ensure numeric yield
        try:
            result["estimated_yield"] = float(result.get("estimated_yield", 0))
        except:
            result["estimated_yield"] = 0.0

        return jsonify({"success": True, "prediction": result})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# -------------------------
# PLANT DISEASE (TEXT MODEL ONLY, NO VISION)
# -------------------------
@app.route('/plant-disease')
@login_required
def plant_disease():
    return render_template("plant_disease.html")


@app.route('/detect-disease', methods=['POST'])
@login_required
def detect_disease():
    try:
        if "image" not in request.files:
            return jsonify({"success": False, "error": "No image uploaded"}), 400

        image = request.files["image"]
        filename = f"{uuid.uuid4().hex}_{secure_filename(image.filename)}"
        filepath = os.path.join("uploads/plant_disease", filename)
        image.save(filepath)

        # Convert to base64 (but not used for AI)
        with open(filepath, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode()

        prompt = """
        Analyze this plant image (text-only mode).

        Return JSON:
        {
            "disease": "",
            "confidence": "",
            "description": "",
            "causes": [],
            "treatment": [],
            "prevention": []
        }
        """

        response = query_openrouter(prompt)

        try:
            diagnosis = json.loads(response)
            return jsonify({
                "success": True,
                "prediction": diagnosis.get("disease", "Unknown"),
                "details": diagnosis,
                "image": img_base64
            })
        except:
            return jsonify({"success": False, "error": "AI parse failed"}), 500

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# -------------------------
# SOIL TYPE (TEXT MODEL ONLY)
# -------------------------
@app.route('/soil-type')
@login_required
def soil_type():
    return render_template("soil_type.html")

@app.route('/predict-soil', methods=['POST'])
@login_required
def predict_soil():
    try:
        if "image" not in request.files:
            return jsonify({"success": False, "error": "No image uploaded"}), 400

        # Save image
        image = request.files["image"]
        filename = secure_filename(image.filename)
        filepath = os.path.join("uploads/soil_type", filename)
        image.save(filepath)

        # Load + preprocess image
        img = load_and_preprocess_single_image(filepath)

        # Predict using your model
        predictions = model.predict(img)
        confidence = float(np.max(predictions))
        predicted_class = class_names[np.argmax(predictions)]

        # Get irrigation advice
        advice = get_soil_advice(predicted_class)

        # Convert uploaded image to base64 (frontend preview)
        with open(filepath, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode()

        return jsonify({
            "success": True,
            "prediction": predicted_class,
            "confidence": confidence,
            "description": advice["description"],
            "irrigation": advice["irrigation"],
            "crop_suggestion": advice["crop_suggestion"],
            "suitable_crops": advice["suitable_crops"],
            "tips": advice["tips"],
            "image": img_base64
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500



# -------------------------
# RUN APP
# -------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
