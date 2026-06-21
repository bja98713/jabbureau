from __future__ import annotations

from typing import Dict, Optional

from pydantic import BaseModel, Field, root_validator


class Etape5MedicalHistory(BaseModel):
    cardiopathie_ischemique: bool = False
    delai_cardiopathie: Optional[str] = Field(None, description="Délai cardiopathie (mois/année)")
    insuffisance_cardiaque: bool = False
    delai_insuffisance_cardiaque: Optional[str] = Field(
        None, description="Délai insuffisance cardiaque"
    )
    avc_ait: bool = False
    delai_avc: Optional[str] = Field(None, description="Délai AVC/AIT")
    insuffisance_renale: bool = False
    delai_insuffisance_renale: Optional[str] = Field(
        None, description="Délai insuffisance rénale"
    )
    diabete: bool = False
    delai_diabete: Optional[str] = Field(None, description="Délai diabète")

    @root_validator
    def ensure_delai_when_positive(cls, values: Dict):
        couples = [
            ("cardiopathie_ischemique", "delai_cardiopathie"),
            ("insuffisance_cardiaque", "delai_insuffisance_cardiaque"),
            ("avc_ait", "delai_avc"),
            ("insuffisance_renale", "delai_insuffisance_renale"),
            ("diabete", "delai_diabete"),
        ]
        for flag_field, delai_field in couples:
            if values.get(flag_field) and not values.get(delai_field):
                raise ValueError(
                    f"Préciser le délai pour l'antécédent '{flag_field.replace('_', ' ')}'"
                )
        return values

    class Config:
        anystr_strip_whitespace = True
        allow_mutation = False
