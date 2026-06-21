from __future__ import annotations

from enum import Enum
from typing import List

from pydantic import BaseModel, Field, validator


class Anticoagulant(str, Enum):
    WARFARINE = "Warfarine"
    APIXABAN = "Apixaban"
    RIVAROXABAN = "Rivaroxaban"
    DABIGATRAN = "Dabigatran"
    EDOXABAN = "Edoxaban"


class Antiagregant(str, Enum):
    ASPIRINE = "Aspirine"
    CLOPIDOGREL = "Clopidogrel"
    TICAGRELOR = "Ticagrelor"


class Antidiabetique(str, Enum):
    INSULINE = "Insuline"
    METFORMINE = "Metformine"
    SU = "Sulfamides hypoglycémiants"
    GLP1 = "Agonistes GLP-1"


class Etape6Treatments(BaseModel):
    anticoagulants_choisis: List[Anticoagulant] = Field(
        default_factory=list, description="Liste d'anticoagulants actuels"
    )
    antiagregants_choisis: List[Antiagregant] = Field(
        default_factory=list, description="Liste d'antiagrégants actuels"
    )
    antidiabetiques_choisis: List[Antidiabetique] = Field(
        default_factory=list, description="Liste d'antidiabétiques actuels"
    )

    @validator(
        "anticoagulants_choisis", "antiagregants_choisis", "antidiabetiques_choisis",
        each_item=False
    )
    def avoid_duplicates(cls, value: List[str]):
        if len(set(value)) != len(value):
            raise ValueError("Les traitements sélectionnés ne peuvent pas contenir de doublons")
        return value

    class Config:
        use_enum_values = True
        allow_mutation = False
