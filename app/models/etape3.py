from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, root_validator

from .etape2 import ExamenType

COLOSCOPIE_INDICATIONS = [
    "Saignement digestif bas",
    "Polypes connus",
    "Surveillance post-polypectomie",
    "Douleurs abdominales",
    "Dépistage familial",
]

GASTROSCOPIE_INDICATIONS = [
    "Reflux gastro-oesophagien",
    "Dysphagie",
    "Anémie inexpliquée",
    "Hématémèse",
    "Dépistage Barrett",
]


class Etape3Indication(BaseModel):
    examen_choisi: ExamenType
    coloscopie_indications: Optional[List[str]] = Field(
        None, description="Liste d'indications pour une coloscopie"
    )
    gastroscopie_indications: Optional[List[str]] = Field(
        None, description="Liste d'indications pour une gastroscopie"
    )
    autre_indication: Optional[str] = Field(
        None, max_length=50, description="Préciser une autre indication si nécessaire"
    )

    @root_validator
    def validate_indications(cls, values):
        examen = values.get("examen_choisi")
        coloscopie = values.get("coloscopie_indications") or []
        gastroscopie = values.get("gastroscopie_indications") or []

        if examen == ExamenType.COLOSCOPIE:
            if not coloscopie and not values.get("autre_indication"):
                raise ValueError("Choisir au moins une indication pour la coloscopie")
            invalid = [item for item in coloscopie if item not in COLOSCOPIE_INDICATIONS]
            if invalid:
                raise ValueError(f"Indications coloscopie non reconnues: {', '.join(invalid)}")
            values["gastroscopie_indications"] = None
        elif examen == ExamenType.GASTROSCOPIE:
            if not gastroscopie and not values.get("autre_indication"):
                raise ValueError("Choisir au moins une indication pour la gastroscopie")
            invalid = [item for item in gastroscopie if item not in GASTROSCOPIE_INDICATIONS]
            if invalid:
                raise ValueError(f"Indications gastroscopie non reconnues: {', '.join(invalid)}")
            values["coloscopie_indications"] = None
        else:
            raise ValueError("Examen non défini pour l'indication")
        return values

    class Config:
        anystr_strip_whitespace = True
        allow_mutation = False
