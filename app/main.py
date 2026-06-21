from __future__ import annotations

from fastapi import FastAPI

from app.models.prescription import FinalPrescription
from app.services.prescription_generator import PrescriptionGenerator

app = FastAPI(title="Prescription Endoscopie", version="0.1.0")


@app.get("/health")
def healthcheck():
    return {"status": "ok"}


@app.post("/prescription")
def create_prescription(prescription: FinalPrescription):
    """Simule la génération d'une prescription finale (email + PDF statique)."""
    summary = PrescriptionGenerator.build_summary(prescription)
    return {
        "message": "Prescription générée",
        "payload": summary,
    }
