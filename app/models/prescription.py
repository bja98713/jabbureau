from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .etape1 import Etape1PatientInfo
from .etape2 import Etape2ExamChoice
from .etape3 import Etape3Indication
from .etape4 import Etape4ClinicalContext
from .etape5 import Etape5MedicalHistory
from .etape6 import Etape6Treatments


class FinalPrescription(BaseModel):
    patient: Etape1PatientInfo
    examen: Etape2ExamChoice
    indication: Etape3Indication
    contexte: Etape4ClinicalContext
    antecedents: Etape5MedicalHistory
    traitements: Etape6Treatments
    generated_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow, description="Horodatage de la prescription"
    )

    class Config:
        allow_mutation = False
