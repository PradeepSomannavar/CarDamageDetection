<h1 align="center"> Car Damage Detection</h1>

<p align="center">
  <strong>AI-powered vehicle damage classification using ResNet50 transfer learning</strong><br/>
  Upload a car image → get instant damage type, confidence score, and a downloadable PDF report
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Model-ResNet50-00bcd4?style=flat-square&logo=pytorch&logoColor=white"/>
  <img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white"/>
  <img src="https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61dafb?style=flat-square&logo=react&logoColor=black"/>
  <img src="https://img.shields.io/badge/Accuracy-82%25-4caf50?style=flat-square"/>
  <img src="https://img.shields.io/badge/Classes-6-ff9800?style=flat-square"/>
</p>

---

## 📸 Demo

![Vehicle Damage Detection UI](docs/ui-demo-v2.png)

---

##  What This Project Does

This application lets you upload a photo of a car and instantly classifies what type of damage is present — or confirms the car is in normal condition. It works for both **front** and **rear** views of the vehicle.

The model was trained on ~1,700 labelled images across 6 damage categories using **ResNet50** with transfer learning. A clean web interface lets anyone use it without any technical knowledge — just drag, drop, and detect.

---

## Features

| Feature | Description |
|---|---|
|  **Instant Classification** | ResNet50 inference in under 0.2 seconds |
|  **Confidence Scores** | Per-class probability breakdown for all 6 categories |
|  **PDF Report** | Download a formatted diagnostic report with the image and results |
|  **Shareable Link** | Generate a secure UUID link to share any prediction result |
|  **Fully Responsive** | Works cleanly on desktop, tablet, and mobile |
|  **Singleton Model** | Model loads once at startup; never reloaded per request |

---

## Model Details

| Property | Value |
|---|---|
| Architecture | ResNet50 (pretrained on ImageNet) + custom classifier head |
| Input size | 224 × 224 RGB |
| Training images | ~1,700 |
| Output classes | 6 |
| Validation accuracy | **~82%** |
| Inference device | CPU / GPU (auto-detected) |

### Transfer Learning Approach

1. Load ResNet50 with ImageNet weights
2. Freeze convolutional layers
3. Replace the final fully-connected layer with `Dropout(0.5) → Linear(2048 → 6)`
4. Fine-tune on the vehicle damage dataset with data augmentation

---

## Damage Classes

| Class | Label | Description |
|---|---|---|
| `F_Normal` | Front Normal | Front of car — no visible damage |
| `F_Breakage` | Front Breakage | Front — broken components (headlights, bumper, etc.) |
| `F_Crushed` | Front Crushed | Front — significant crush damage |
| `R_Normal` | Rear Normal | Rear of car — no visible damage |
| `R_Breakage` | Rear Breakage | Rear — broken components (taillights, boot, etc.) |
| `R_Crushed` | Rear Crushed | Rear — significant crush damage |

> **Note:** The model is trained on front and rear views only. For best results, ensure the photo clearly captures either the front or rear of the vehicle.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Deep Learning | PyTorch, torchvision |
| Backend API | FastAPI, Uvicorn |
| PDF Generation | ReportLab |
| Frontend | React 18, Vite |
| Styling | Vanilla CSS (no framework) |

---

## 📁 Project Structure

```
damage-prediction/
│
├── training/
│   ├── damage_pred.ipynb          # Full training pipeline (ResNet50)
│   └── hyperparam_tuning.ipynb    # Learning rate, dropout experiments
│
├── ui/
│   ├── backend/
│   │   ├── main.py                # FastAPI app — all API endpoints
│   │   ├── model.py               # CarClassifierResNet class + load_model()
│   │   ├── requirements.txt       # Python dependencies
│   │   └── saved_model.pth        # Trained model weights (not tracked in git)
│   │
│   └── frontend/
│       ├── public/
│       │   └── car-icon.svg       # Custom browser favicon
│       └── src/
│           ├── App.jsx            # Main React component
│           ├── App.css            # Full design system (navy/cyan theme)
│           └── main.jsx           # Vite entry point
│
└── docs/
    └── ui-demo-v2.png             # UI screenshot
```

---

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+
- Git

---

### 1 · Clone the Repository

```bash
git clone https://github.com/PradeepSomannavar/CarDamageDetection.git
cd CarDamageDetection
```

---

### 2 · Backend Setup (FastAPI)

```bash
cd ui/backend

# Install dependencies
pip install -r requirements.txt

# Add your trained weights file
# Place saved_model.pth inside ui/backend/

# Start the server
uvicorn main:app --port 8000 --reload
```

The API will be live at **http://localhost:8000**  
Interactive docs: **http://localhost:8000/docs**

> The model is loaded **once** at startup. All predictions reuse the same in-memory model — no performance hit per request.

---

### 3 · Frontend Setup (React)

Open a **second terminal**:

```bash
cd ui/frontend

# Install packages (first time only)
npm install

# Start the dev server
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Check server and model status |
| `GET` | `/stats` | Total scans, accuracy, system status |
| `POST` | `/predict` | Upload image → get prediction |
| `GET` | `/report/{id}` | Download PDF report for a prediction |
| `POST` | `/share` | Create shareable link for a prediction |
| `GET` | `/share/{id}` | Retrieve a shared prediction result |

### Example: POST /predict

**Request:** `multipart/form-data` with field `file`

**Response:**
```json
{
  "prediction_id": "8ad0a4f8-20fd-4390-bb6a-81e0b187fd0e",
  "predicted_class": "F_Crushed",
  "predicted_label": "Front Crushed",
  "confidence": 99.87,
  "all_probabilities": {
    "F_Breakage": 0.03,
    "F_Crushed":  99.87,
    "F_Normal":   0.02,
    "R_Breakage": 0.04,
    "R_Crushed":  0.02,
    "R_Normal":   0.02
  },
  "process_time_s": 0.118,
  "filename": "car_front.jpg",
  "timestamp": "2026-03-28T03:44:32Z"
}
```

---

## 📄 PDF Report

After running a prediction, click **"Generate Detailed PDF Report"** to download a formatted report that includes:

- Uploaded car image
- Predicted damage class
- Confidence score with a visual progress bar
- Full probability breakdown for all 6 classes

---

## ⚠️ Important Notes

- `saved_model.pth` is **not tracked in git** (94 MB). You must train the model yourself using `training/damage_pred.ipynb`, or obtain the weights file separately and place it at `ui/backend/saved_model.pth`.
- The model works best with clear, well-lit photos of the **front or rear** of a car.
- Shared prediction links (`/share/{id}`) are stored in-memory and will reset if the server restarts.

---

## 👤 Author

**Pradeep Somannavar**  
[GitHub](https://github.com/PradeepSomannavar) · [CarDamageDetection Repo](https://github.com/PradeepSomannavar/CarDamageDetection)
