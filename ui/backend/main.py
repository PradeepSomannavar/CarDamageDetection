"""
FastAPI backend for Car Damage Detection — v2.
"""

from __future__ import annotations

import io
import os
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime

import torch
import torch.nn.functional as F
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from PIL import Image
from torchvision import transforms

from model import CLASS_LABELS, CLASS_NAMES, load_model

# ---------------------------------------------------------------------------
# Globals
# ---------------------------------------------------------------------------
_model = None
_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

WEIGHTS_PATH = os.path.join(os.path.dirname(__file__), "saved_model.pth")

_predictions: dict[str, dict] = {}
_shares: dict[str, dict] = {}
_total_scans: int = 0


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _model
    print(f"[startup] Loading model from {WEIGHTS_PATH} on {_device} …")
    if not os.path.exists(WEIGHTS_PATH):
        raise FileNotFoundError(f"Weights not found: {WEIGHTS_PATH}")
    _model = load_model(WEIGHTS_PATH, _device)
    print("[startup] Model ready ✓")
    yield
    print("[shutdown] Done.")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="Vehicle Damage Detection API", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_result(pred_class, confidence, all_probs, process_time_s, filename):
    return {
        "predicted_class": pred_class,
        "predicted_label": CLASS_LABELS[pred_class],
        "confidence": round(confidence, 2),
        "all_probabilities": all_probs,
        "process_time_s": round(process_time_s, 3),
        "filename": filename,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


def _generate_pdf(data: dict) -> bytes:
    """
    Professional PDF report:
      - Title: Vehicle Damage Detection
      - Subtitle: Diagnostic Report
      - Scan Details table  (file, timestamp, process time)
      - Uploaded image (centred, max 70 mm tall)
      - Predicted Class  (large dark text)
      - Confidence Score (large cyan)  + progress bar
      - All Class Probabilities table
    No footer, no extra branding text.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        HRFlowable, Image as RLImage,
        Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
    )

    W, _ = A4
    LEFT = RIGHT = 20 * mm
    usable_w = W - LEFT - RIGHT          # ≈ 170 mm

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=18 * mm, bottomMargin=18 * mm,
        leftMargin=LEFT, rightMargin=RIGHT,
    )

    # ── Palette (dark-on-white → readable on paper) ──────────────────
    NAVY      = colors.HexColor("#0d1b2a")
    CYAN      = colors.HexColor("#00acc1")
    DARK      = colors.HexColor("#1c2d40")
    MID       = colors.HexColor("#6b7c93")
    LIGHT_BG  = colors.HexColor("#f0f5f9")
    ROW_A     = colors.HexColor("#f7fafc")
    ROW_B     = colors.white
    RULE      = colors.HexColor("#d1dce8")
    HDR_BG    = colors.HexColor("#0d1b2a")

    # ── Paragraph styles ────────────────────────────────────────────
    base = getSampleStyleSheet()

    def ps(name, **kw):
        return ParagraphStyle(name, parent=base["Normal"], **kw)

    S_TITLE    = ps("t", fontSize=24, fontName="Helvetica-Bold",
                    textColor=NAVY, alignment=1, spaceAfter=4)
    S_SUB      = ps("s", fontSize=11, textColor=MID, alignment=1, spaceAfter=10)
    S_SECTION  = ps("sc", fontSize=8, fontName="Helvetica-Bold",
                    textColor=MID, spaceBefore=16, spaceAfter=6)
    S_BIGVAL   = ps("bv", fontSize=22, fontName="Helvetica-Bold",
                    textColor=NAVY, spaceAfter=6)
    S_CONFVAL  = ps("cv", fontSize=32, fontName="Helvetica-Bold",
                    textColor=CYAN, spaceAfter=14)
    S_TH       = ps("th", fontSize=8, fontName="Helvetica-Bold", textColor=colors.white)
    S_TH_R     = ps("thr", fontSize=8, fontName="Helvetica-Bold",
                    textColor=colors.white, alignment=2)
    S_TD       = ps("td", fontSize=8,  textColor=DARK)
    S_TD_B     = ps("tdb", fontSize=8, fontName="Helvetica-Bold", textColor=DARK)
    S_TD_CYN   = ps("tdc", fontSize=8, fontName="Helvetica-Bold", textColor=CYAN)
    S_TD_R     = ps("tdr", fontSize=8, textColor=DARK, alignment=2)
    S_TD_R_B   = ps("tdrb", fontSize=8, fontName="Helvetica-Bold", textColor=DARK, alignment=2)
    S_TD_R_CYN = ps("tdrc", fontSize=8, fontName="Helvetica-Bold", textColor=CYAN, alignment=2)

    story = []

    # ── TITLE ────────────────────────────────────────────────────────
    story += [
        Paragraph("Vehicle Damage Detection", S_TITLE),
        Spacer(1, 10),
        HRFlowable(width="100%", thickness=2, color=CYAN, spaceAfter=8),
    ]

    # ── SCAN DETAILS ─────────────────────────────────────────────────
    story.append(Paragraph("SCAN DETAILS", S_SECTION))

    meta_tbl = Table(
        [
            [Paragraph("File",         S_TD), Paragraph(data.get("filename", "—"),                     S_TD_B)],
            [Paragraph("Timestamp",    S_TD), Paragraph(data.get("timestamp", "—"),                    S_TD_B)],
            [Paragraph("Process Time", S_TD), Paragraph(f"{data.get('process_time_s', 0):.3f} s",     S_TD_B)],
        ],
        colWidths=[38 * mm, usable_w - 38 * mm],
    )
    meta_tbl.setStyle(TableStyle([
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [ROW_A, ROW_B]),
        ("BOX",            (0, 0), (-1, -1), 0.5, RULE),
        ("INNERGRID",      (0, 0), (-1, -1), 0.25, RULE),
        ("TOPPADDING",     (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 7),
        ("LEFTPADDING",    (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 10),
        ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(meta_tbl)

    # ── IMAGE ────────────────────────────────────────────────────────
    img_bytes = data.get("image_bytes")
    if img_bytes:
        try:
            pil = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            iw, ih = pil.size
            scale   = min(usable_w / iw, 70 * mm / ih)
            rw, rh  = iw * scale, ih * scale

            rl_img  = RLImage(io.BytesIO(img_bytes), width=rw, height=rh)
            img_tbl = Table([[rl_img]], colWidths=[usable_w])
            img_tbl.setStyle(TableStyle([
                ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
                ("BOX",           (0, 0), (-1, -1), 0.5, RULE),
                ("TOPPADDING",    (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("BACKGROUND",    (0, 0), (-1, -1), ROW_A),
            ]))
            story += [Spacer(1, 10), img_tbl]
        except Exception:
            pass

    story.append(HRFlowable(width="100%", thickness=0.75, color=RULE, spaceAfter=2))

    # ── PREDICTED CLASS ──────────────────────────────────────────────
    story.append(Paragraph("PREDICTED CLASS", S_SECTION))
    pred_label = (data.get("predicted_label") or data.get("predicted_class") or "—").upper()
    story += [Paragraph(pred_label, S_BIGVAL), Spacer(1, 14)]

    # ── CONFIDENCE SCORE ─────────────────────────────────────────────
    story.append(Paragraph("CONFIDENCE SCORE", S_SECTION))
    conf = float(data.get("confidence") or 0)
    story += [Paragraph(f"{conf:.1f}%", S_CONFVAL), Spacer(1, 24)]

    # Progress bar using two cells
    filled  = max(0.0, min(1.0, conf / 100.0))
    fw = usable_w * filled
    ew = usable_w * (1 - filled)
    if ew > 0.5:
        pb = Table([["", ""]], colWidths=[fw, ew], rowHeights=[7])
        pb.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (0, 0), CYAN),
            ("BACKGROUND",    (1, 0), (1, 0), LIGHT_BG),
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ]))
    else:
        pb = Table([[""]], colWidths=[usable_w], rowHeights=[7])
        pb.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (0, 0), CYAN),
            ("TOPPADDING",    (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ]))
    story.append(pb)
    story.append(Spacer(1, 18))

    # ── ALL CLASS PROBABILITIES ──────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.75, color=RULE, spaceAfter=4))
    story.append(Paragraph("ALL CLASS PROBABILITIES", S_SECTION))

    sorted_probs = sorted(data.get("all_probabilities", {}).items(), key=lambda x: -x[1])
    top_cls = data.get("predicted_class", "")

    # Column widths: class name | % value | bar
    C1, C2, C3 = 65 * mm, 30 * mm, usable_w - 95 * mm

    prob_rows = [[
        Paragraph("CLASS",    S_TH),
        Paragraph("CONF. %",  S_TH_R),
        Paragraph("BAR",      S_TH),
    ]]
    for cls, pct in sorted_probs:
        is_top   = cls == top_cls
        name_sty = S_TD_CYN  if is_top else S_TD_B
        pct_sty  = S_TD_R_CYN if is_top else S_TD_R_B
        bar_len  = max(1, int((pct / 100) * 32))
        bar_sty  = ps(f"bar_{cls}", fontSize=6,
                      textColor=CYAN if is_top else colors.HexColor("#b0c4d8"))
        prob_rows.append([
            Paragraph(CLASS_LABELS.get(cls, cls),  name_sty),
            Paragraph(f"{pct:.1f}%",               pct_sty),
            Paragraph("█" * bar_len,               bar_sty),
        ])

    n = len(prob_rows)
    row_bgs = [ROW_A if i % 2 == 1 else ROW_B for i in range(n)]

    prob_tbl = Table(prob_rows, colWidths=[C1, C2, C3])
    prob_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), HDR_BG),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [ROW_A, ROW_B]),
        ("BOX",           (0, 0), (-1, -1), 0.5, RULE),
        ("INNERGRID",     (0, 0), (-1, -1), 0.25, RULE),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("ALIGN",         (1, 0), (1, -1), "RIGHT"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(prob_tbl)

    doc.build(story)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": _model is not None, "device": str(_device)}


@app.get("/stats")
async def stats():
    return {
        "total_scans": _total_scans,
        "ai_accuracy": 82.09,
        "system_status": "OPTIMAL",
    }


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    global _total_scans
    if _model is None:
        raise HTTPException(503, "Model not loaded.")
    if file.content_type not in ("image/jpeg", "image/jpg", "image/png", "image/webp"):
        raise HTTPException(400, f"Unsupported file type: {file.content_type}")

    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception as e:
        raise HTTPException(400, f"Cannot read image: {e}")

    tensor = _transform(image).unsqueeze(0).to(_device)

    t0 = time.perf_counter()
    with torch.no_grad():
        logits = _model(tensor)
        probs  = F.softmax(logits, dim=1).squeeze()
    elapsed = time.perf_counter() - t0

    pred_idx  = int(probs.argmax().item())
    pred_cls  = CLASS_NAMES[pred_idx]
    conf      = float(probs[pred_idx].item()) * 100
    all_p     = {CLASS_NAMES[i]: round(float(probs[i].item()) * 100, 2)
                 for i in range(len(CLASS_NAMES))}

    prediction_id = str(uuid.uuid4())
    result = _make_result(pred_cls, conf, all_p, elapsed, file.filename or "unknown")

    # Store image bytes so the PDF report can embed the photo
    result["image_bytes"] = contents

    _predictions[prediction_id] = result
    _total_scans += 1

    # Return result WITHOUT the raw bytes (keep API response compact)
    api_result = {k: v for k, v in result.items() if k != "image_bytes"}
    return {"prediction_id": prediction_id, **api_result}


@app.get("/report/{prediction_id}")
async def get_report(prediction_id: str):
    data = _predictions.get(prediction_id)
    if not data:
        raise HTTPException(404, "Prediction not found. Run /predict first.")
    pdf_bytes = _generate_pdf(data)
    filename  = f"damage_report_{prediction_id[:8]}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/share")
async def create_share(body: dict):
    pid = body.get("prediction_id")
    if not pid or pid not in _predictions:
        raise HTTPException(404, "Prediction not found.")
    share_id = str(uuid.uuid4())
    # Share data without raw image bytes
    _shares[share_id] = {k: v for k, v in _predictions[pid].items() if k != "image_bytes"}
    return {"share_id": share_id, "share_url": f"/share/{share_id}"}


@app.get("/share/{share_id}")
async def get_share(share_id: str):
    data = _shares.get(share_id)
    if not data:
        raise HTTPException(404, "Shared result not found or expired.")
    return data
