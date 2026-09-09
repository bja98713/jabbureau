from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ExamenType(str, Enum):
    GASTROSCOPIE = "GASTROSCOPIE"
    COLOSCOPIE = "COLOSCOPIE"


class Etape2ExamChoice(BaseModel):
    examen_choisi: ExamenType = Field(..., description="Examen selectionné")

    class Config:
        use_enum_values = True
        allow_mutation = False
