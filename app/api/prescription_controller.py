from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.models.prescription import FinalPrescription
from app.services.prescription_output import PrescriptionOutputService

router = APIRouter(prefix="/api/v1/prescription", tags=["prescription"])


def get_output_service() -> PrescriptionOutputService:
    return PrescriptionOutputService()


@router.post("/generate")
async def generate_prescription(
    payload: FinalPrescription,
    output_service: PrescriptionOutputService = Depends(get_output_service),
) -> dict:
    try:
        data_dict = payload.as_dict()
        pdf_result = output_service.generer_pdf(data_dict)
        email_specialiste = output_service.generer_email_specialiste(data_dict)
        email_prescripteur = output_service.generer_email_prescripteur(data_dict)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return {
        "pdf": pdf_result,
        "email_specialiste": email_specialiste,
        "email_prescripteur": email_prescripteur,
    }
