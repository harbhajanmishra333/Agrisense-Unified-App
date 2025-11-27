# AgriSense - Project Structure

## 📁 Directory Structure

```
unified_app/
│
├── app.py                          # Main Flask application (456 lines)
├── requirements.txt                # Python dependencies
├── run.bat                         # Windows startup script
├── .gitignore                      # Git ignore rules
│
├── README.md                       # Detailed documentation
├── QUICK_START.md                  # Quick start guide
├── PROJECT_STRUCTURE.md            # This file
│
├── templates/                      # HTML Templates
│   ├── base.html                   # Base template with navbar
│   ├── login.html                  # Login page
│   ├── register.html               # Registration page
│   ├── dashboard.html              # Main dashboard
│   ├── crop_recommendation.html    # Crop recommendation tool
│   ├── crop_yield.html             # Yield prediction tool
│   ├── plant_disease.html          # Disease detection tool
│   └── soil_type.html              # Soil analysis tool
│
├── uploads/                        # Auto-created for image uploads
│   ├── plant_disease/              # Disease detection images
│   └── soil_type/                  # Soil analysis images
│
├── venv/                           # Virtual environment (auto-created)
│
└── agrisense.db                    # SQLite database (auto-created)
```

## 🔗 Integration with Existing Models

The unified app integrates with existing models in parent directories:

```
Final1/
│
├── unified_app/                    # ← New unified application
│   └── app.py
│
├── AgriSense1-main/               # ← Crop Recommendation
│   └── best_model.pkl
│
├── crop_yield3/                   # ← Yield Prediction
│   ├── crop_yield_model.joblib
│   └── yield.csv
│
├── plant_disease1/                # ← Disease Detection
│   ├── models/
│   │   └── plant_disease_recog_model_pwp.keras
│   └── plant_disease.json
│
└── soil_type_predictor/           # ← Soil Analysis
    └── soil_type_model.h5
```

## 🎨 Application Flow

```
┌─────────────────────────────────────────────┐
│          Browser: localhost:5000            │
└─────────────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │   Login/Register      │
         │   (Authentication)    │
         └───────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │      Dashboard        │
         │   (4 Tool Cards)      │
         └───────────────────────┘
                     │
         ┌───────────┴───────────┬───────────┬───────────┐
         ▼                       ▼           ▼           ▼
    ┌─────────┐          ┌─────────┐  ┌─────────┐  ┌─────────┐
    │  Crop   │          │  Yield  │  │ Disease │  │  Soil   │
    │  Recom. │          │  Pred.  │  │ Detect. │  │ Analysis│
    └─────────┘          └─────────┘  └─────────┘  └─────────┘
         │                    │            │            │
         ▼                    ▼            ▼            ▼
    [ML Model]           [ML Model]   [ML Model]   [ML Model]
```

## 🔐 Authentication System

```
User Registration
    ↓
Password Hashing (Werkzeug)
    ↓
Store in SQLite Database
    ↓
Login with Credentials
    ↓
Session Management (Flask-Login)
    ↓
Access Protected Routes
```

## 🛠️ Technology Stack

### Backend
- **Framework**: Flask 2.3.3
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: Flask-Login 0.6.2
- **Security**: Werkzeug password hashing

### Machine Learning
- **TensorFlow**: 2.13.0 (Deep Learning models)
- **scikit-learn**: 1.3.0 (Traditional ML)
- **joblib**: Model serialization
- **Pillow**: Image processing

### Frontend
- **CSS Framework**: Bootstrap 5.1.3
- **Icons**: Font Awesome 6.0.0
- **JavaScript**: Vanilla JS (Fetch API)

### Data Processing
- **pandas**: 2.0.3 (Data manipulation)
- **numpy**: 1.24.3 (Numerical operations)

## 📊 Database Schema

```sql
User Table:
├── id (Primary Key)
├── username (Unique)
├── email (Unique)
├── password_hash
└── created_at (Timestamp)
```

## 🔄 API Endpoints

### Authentication Routes
- `GET  /` → Redirect to login/dashboard
- `GET  /login` → Login page
- `POST /login` → Process login
- `GET  /register` → Registration page
- `POST /register` → Process registration
- `GET  /logout` → Logout user

### Protected Routes (Login Required)
- `GET  /dashboard` → Main dashboard
- `GET  /crop-recommendation` → Crop tool page
- `POST /predict-crop` → Crop prediction API
- `GET  /crop-yield` → Yield tool page
- `POST /predict-yield` → Yield prediction API
- `GET  /plant-disease` → Disease tool page
- `POST /detect-disease` → Disease detection API
- `GET  /soil-type` → Soil tool page
- `POST /predict-soil` → Soil analysis API

## 🎯 Key Features

### 1. Unified Authentication
- Single login for all tools
- Secure password storage
- Session persistence

### 2. Responsive Design
- Mobile-friendly interface
- Bootstrap 5 components
- Modern gradient backgrounds

### 3. Modular Architecture
- Separate routes for each tool
- Reusable base template
- Independent ML model loading

### 4. Error Handling
- User-friendly error messages
- Model loading fallbacks
- Form validation

### 5. File Upload Management
- Secure file handling
- Image preview functionality
- Organized storage structure

## 🚀 Deployment Checklist

- [ ] Change SECRET_KEY in app.py
- [ ] Set debug=False for production
- [ ] Configure production database
- [ ] Set up proper file storage
- [ ] Configure HTTPS
- [ ] Set up environment variables
- [ ] Add rate limiting
- [ ] Implement logging
- [ ] Add backup system
- [ ] Configure CORS if needed

## 📈 Future Enhancements

1. **User Features**
   - Profile management
   - Prediction history
   - Export results to PDF

2. **Advanced Analytics**
   - Dashboard statistics
   - Trend analysis
   - Comparison charts

3. **Integration**
   - Weather API
   - Market prices
   - Government schemes

4. **Mobile App**
   - React Native version
   - Offline mode
   - Push notifications

5. **Admin Panel**
   - User management
   - Model updates
   - System monitoring

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Status**: Production Ready
