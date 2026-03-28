# Vehicle Damage Detection — UI

A full-stack web UI for the car damage classification model.

```
ui/
├── backend/          ← FastAPI (Python)
│   ├── main.py
│   ├── model.py
│   ├── requirements.txt
│   └── saved_model.pth
└── frontend/         ← React + Vite
```

---

## How to Run

### 1 — Backend (FastAPI)

```bash
cd ui/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The API will be available at **http://localhost:8000**
Interactive docs: **http://localhost:8000/docs**

> **Note:** The model loads only once at startup. All predictions reuse
> the in-memory model — no re-loading per request.

### 2 — Frontend (React)

Open a **second** terminal:

```bash
cd ui/frontend
npm install        # first time only
npm run dev
```

Open **http://localhost:5173** in your browser.

---

## API Endpoints

| Method | Path       | Description                        |
|--------|------------|-------------------------------------|
| GET    | /health    | Check if model is loaded            |
| POST   | /predict   | Upload image → get damage class     |

### POST /predict — Response Example

```json
{
  "predicted_class": "F_Normal",
  "predicted_label": "Front Normal",
  "confidence": 94.23,
  "all_probabilities": {
    "F_Breakage": 0.91,
    "F_Crushed":  0.12,
    "F_Normal":   94.23,
    "R_Breakage": 3.44,
    "R_Crushed":  0.97,
    "R_Normal":   0.33
  }
}
```

## Classes

| Class      | Description            |
|------------|------------------------|
| F_Normal   | Front — no damage      |
| F_Breakage | Front — breakage       |
| F_Crushed  | Front — crushed        |
| R_Normal   | Rear — no damage       |
| R_Breakage | Rear — breakage        |
| R_Crushed  | Rear — crushed         |
