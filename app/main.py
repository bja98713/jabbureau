from __future__ import annotations

from fastapi import FastAPI

from app.api.prescription_controller import router as prescription_router

app = FastAPI(
    title="Service de Prescription Endoscopique",
    version="0.1.0",
    description=(
        "API structurée par couches pour la saisie multi-étapes du formulaire de prescription "
        "(priorité usage desktop)."
    ),
)

app.include_router(prescription_router)
