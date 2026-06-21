from __future__ import annotations

from pydantic import BaseModel, Field


class Etape4ClinicalContext(BaseModel):
    contexte_clinique: str = Field(
        ..., max_length=300, description="Résumé du contexte clinique (300 caractères max)"
    )

    class Config:
        anystr_strip_whitespace = True
        allow_mutation = False
