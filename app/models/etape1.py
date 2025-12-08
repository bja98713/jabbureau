from __future__ import annotations

import re
from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, validator


class Etape1PatientInfo(BaseModel):
    nom: str = Field(..., min_length=1, description="Nom de famille du patient")
    prenom: str = Field(..., min_length=1, description="Prénom du patient")
    date_de_naissance: date = Field(..., description="Date de naissance au format YYYY-MM-DD")
    taille_cm: int = Field(..., gt=0, description="Taille en centimètres")
    poids_kg: float = Field(..., gt=0, description="Poids en kilogrammes")
    bmi: Optional[float] = Field(
        None,
        gt=0,
        description="Indice de masse corporelle. Sera validé/calculé depuis taille et poids.",
    )
    email: EmailStr
    numero_telephone: str = Field(
        ...,
        description=(
            "Numéro de téléphone au format Suisse (+41 / 0) ou Français (+33 / 0) avec validation souple"
        ),
    )

    @validator("numero_telephone")
    def validate_numero_telephone(cls, value: str) -> str:
        cleaned = re.sub(r"[\s.-]", "", value)
        swiss_pattern = re.compile(r"^(?:\+?41|0)7[5-9]\d{7}$")
        french_pattern = re.compile(r"^(?:\+?33|0)[1-9]\d{8}$")
        if not (swiss_pattern.match(cleaned) or french_pattern.match(cleaned)):
            raise ValueError(
                "Numéro invalide : formats suisses (+41/0) ou français (+33/0) attendus"
            )
        return cleaned

    @validator("bmi", always=True)
    def validate_or_compute_bmi(cls, bmi: Optional[float], values):
        taille_cm = values.get("taille_cm")
        poids_kg = values.get("poids_kg")
        if taille_cm is None or poids_kg is None:
            return bmi
        calculated = round(poids_kg / ((taille_cm / 100) ** 2), 1)
        if bmi is None:
            return calculated
        difference = abs(bmi - calculated)
        if difference > 0.5:
            raise ValueError(
                f"BMI incohérent : attendu environ {calculated} selon la taille et le poids"
            )
        return bmi

    class Config:
        anystr_strip_whitespace = True
        allow_mutation = False
