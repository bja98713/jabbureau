from __future__ import annotations

import re
from datetime import date
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class ExamenType(str, Enum):
    GASTROSCOPIE = "gastroscopie"
    COLOSCOPIE = "coloscopie"


class ColoscopieIndication(str, Enum):
    RECTORRAGIE = "rectorragie"
    SUIVI_MICI = "suivi_mici"
    SURVEILLANCE_POLYPES = "surveillance_polypes"
    DOULEURS_ABDOMINALES = "douleurs_abdominales"
    AUTRE = "autre"


class GastroscopieIndication(str, Enum):
    DYSPESIE = "dyspepsie"
    RGO = "rgo_refractaire"
    ANEMIE = "anemie_fer"
    VOMISSEMENTS = "vomissements_inexpliques"
    AUTRE = "autre"


class DelayCardiaque(str, Enum):
    MOINS_1_MOIS = "< 1 mois"
    PLUS_12_MOIS = "> 12 mois"


class DelayEpTvp(str, Enum):
    MOINS_3_MOIS = "< 3 mois"
    PLUS_6_MOIS = "> 6 mois"


class Anticoagulant(str, Enum):
    WARFARINE = "warfarine_avk"
    APIXABAN = "apixaban"
    RIVAROXABAN = "rivaroxaban"
    DABIGATRAN = "dabigatran"
    EDOXABAN = "edoxaban"
    HEPARINE = "heparine"


class Antiagregant(str, Enum):
    ASPIRINE = "aspirine"
    CLOPIDOGREL = "clopidogrel"
    TICAGRELOR = "ticagrelor"
    PRASUGREL = "prasugrel"


class Antidiabetique(str, Enum):
    INSULINE = "insuline"
    METFORMINE = "metformine"
    SULFAMIDE = "sulfamides_hypoglycemiants"
    INCRETINE = "analogue_incretine"
    INHIB_SGLT2 = "ihm_sglt2"


class Etape1PatientInfo(BaseModel):
    nom: str = Field(..., min_length=1, max_length=80)
    prenom: str = Field(..., min_length=1, max_length=80)
    date_de_naissance: date = Field(..., description="Date de naissance (YYYY-MM-DD)")
    taille_cm: int = Field(..., gt=0, description="Taille en centimètres")
    poids_kg: float = Field(..., gt=0, description="Poids en kilogrammes")
    bmi: Optional[float] = Field(None, gt=0, description="Body Mass Index calculé")
    email: EmailStr
    numero_telephone: str = Field(..., description="Numéro de téléphone CH/FR")

    @field_validator("date_de_naissance")
    @classmethod
    def validate_birth_date_not_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("La date de naissance ne peut pas être dans le futur.")
        return value

    @field_validator("numero_telephone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        cleaned_digits = re.sub(r"\D", "", value)
        if cleaned_digits.startswith("00"):
            cleaned_digits = cleaned_digits[2:]

        def valid_domestic(number: str) -> bool:
            return len(number) == 10 and number.startswith("0")

        def valid_with_country(number: str, country_code: str) -> bool:
            return number.startswith(country_code) and len(number) == len(country_code) + 9

        if not (
            valid_domestic(cleaned_digits)
            or valid_with_country(cleaned_digits, "41")
            or valid_with_country(cleaned_digits, "33")
        ):
            raise ValueError(
                "Numéro invalide : utilisez un indicatif CH (+41) ou FR (+33), 10 à 11 chiffres au total."
            )
        return value

    @model_validator(mode="after")
    def compute_bmi_if_missing(self) -> "Etape1PatientInfo":
        if self.bmi is None:
            taille_m = self.taille_cm / 100
            if taille_m > 0:
                self.bmi = round(self.poids_kg / (taille_m**2), 1)
        else:
            taille_m = self.taille_cm / 100
            expected_bmi = self.poids_kg / (taille_m**2)
            if abs(self.bmi - expected_bmi) > 1.5:
                raise ValueError(
                    "L'IMC fourni est incohérent avec taille/poids (tolérance 1.5)."
                )
        return self


class Etape2ExamChoice(BaseModel):
    examen_choisi: ExamenType


class Etape3Indication(BaseModel):
    coloscopie_indications: Optional[List[ColoscopieIndication]] = None
    gastroscopie_indications: Optional[List[GastroscopieIndication]] = None
    autre_indication: Optional[str] = Field(None, max_length=50)

    @model_validator(mode="after")
    def validate_autre_indication(self) -> "Etape3Indication":
        indications = (
            self.coloscopie_indications or []
        ) + (self.gastroscopie_indications or [])
        if any(indic.name == "AUTRE" if isinstance(indic, Enum) else indic == "autre" for indic in indications):
            if not self.autre_indication:
                raise ValueError("Le champ 'autre_indication' est requis lorsque 'Autre' est sélectionné.")
        elif self.autre_indication:
            raise ValueError("Le champ 'autre_indication' ne doit être rempli que si 'Autre' est sélectionné.")
        return self


class Etape4ClinicalContext(BaseModel):
    contexte_clinique: str = Field(..., max_length=300)


class Etape5MedicalHistory(BaseModel):
    cardiopathie_ischemique: bool = False
    cardiopathie_ischemique_delai: Optional[DelayCardiaque] = None
    ep_tvp: bool = False
    ep_tvp_delai: Optional[DelayEpTvp] = None
    insuffisance_renale_chronique: bool = False
    insuffisance_hepatique: bool = False
    allergie_connue: bool = False
    allergie_detail: Optional[str] = Field(None, max_length=120)
    grossesse_en_cours: bool = False
    antecedent_hemorragique: bool = False

    @model_validator(mode="after")
    def validate_conditional_fields(self) -> "Etape5MedicalHistory":
        if self.cardiopathie_ischemique and self.cardiopathie_ischemique_delai is None:
            raise ValueError(
                "Précisez le délai de cardiopathie ischémique (< 1 mois ou > 12 mois)."
            )
        if not self.cardiopathie_ischemique:
            self.cardiopathie_ischemique_delai = None

        if self.ep_tvp and self.ep_tvp_delai is None:
            raise ValueError("Précisez le délai de l'épisode EP/TVP (< 3 mois ou > 6 mois).")
        if not self.ep_tvp:
            self.ep_tvp_delai = None

        if self.allergie_connue and not self.allergie_detail:
            raise ValueError("Décrivez l'allergie connue (120 caractères max).")
        if not self.allergie_connue:
            self.allergie_detail = None
        return self


class Etape6Treatments(BaseModel):
    anticoagulants_choisis: List[Anticoagulant] = Field(default_factory=list)
    antiagregants_choisis: List[Antiagregant] = Field(default_factory=list)
    antidiabetiques_choisis: List[Antidiabetique] = Field(default_factory=list)
    autres_traitements: List[str] = Field(default_factory=list, max_items=6)

    @model_validator(mode="after")
    def ensure_unique_entries(self) -> "Etape6Treatments":
        for label, values in {
            "anticoagulants": self.anticoagulants_choisis,
            "antiagrégants": self.antiagregants_choisis,
            "antidiabétiques": self.antidiabetiques_choisis,
        }.items():
            if len(values) != len(set(values)):
                raise ValueError(f"Les traitements {label} ne doivent pas contenir de doublons.")
        return self


class FinalPrescription(BaseModel):
    etape1: Etape1PatientInfo
    etape2: Etape2ExamChoice
    etape3: Etape3Indication
    etape4: Etape4ClinicalContext
    etape5: Etape5MedicalHistory
    etape6: Etape6Treatments

    @model_validator(mode="after")
    def validate_indication_alignment(self) -> "FinalPrescription":
        exam = self.etape2.examen_choisi
        if exam == ExamenType.COLOSCOPIE:
            if not self.etape3.coloscopie_indications:
                raise ValueError("Pour une coloscopie, précisez au moins une indication dédiée.")
            if self.etape3.gastroscopie_indications:
                raise ValueError(
                    "Les indications de gastroscopie ne doivent pas être renseignées quand l'examen est une coloscopie."
                )
        elif exam == ExamenType.GASTROSCOPIE:
            if not self.etape3.gastroscopie_indications:
                raise ValueError("Pour une gastroscopie, précisez au moins une indication dédiée.")
            if self.etape3.coloscopie_indications:
                raise ValueError(
                    "Les indications de coloscopie ne doivent pas être renseignées quand l'examen est une gastroscopie."
                )
        return self

    def as_dict(self) -> Dict[str, object]:
        return self.model_dump()
