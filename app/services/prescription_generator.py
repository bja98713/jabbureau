from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from jinja2 import Template

from app.models.prescription import FinalPrescription

EMAIL_TEMPLATE = Template(
    """
Objet: Préparation de l'examen {{ prescription.examen.examen_choisi }}

Bonjour {{ prescription.patient.prenom }} {{ prescription.patient.nom }},

Nous confirmons la préparation de votre {{ prescription.examen.examen_choisi.lower() }}.
Indication principale: {{ prescription.indication.autre_indication or 'Voir liste jointe' }}.
Contexte clinique: {{ prescription.contexte.contexte_clinique }}

Cordialement,
Service d'endoscopie
"""
)

PDF_TEMPLATE = Template(
    """
Prescription - {{ prescription.generated_at.strftime('%Y-%m-%d %H:%M') }}
Patient: {{ prescription.patient.prenom }} {{ prescription.patient.nom }} ({{ prescription.patient.date_de_naissance }})
Examen: {{ prescription.examen.examen_choisi }}
Indication: {{ prescription.indication.autre_indication or 'Sélection structurée' }}
Traitements: Anticoagulants {{ prescription.traitements.anticoagulants_choisis }}, \
Antiagrégants {{ prescription.traitements.antiagregants_choisis }}, Antidiabétiques {{ prescription.traitements.antidiabetiques_choisis }}
"""
)


@dataclass
class PrescriptionGenerator:
    @staticmethod
    def generate_email(prescription: FinalPrescription) -> str:
        return EMAIL_TEMPLATE.render(prescription=prescription)

    @staticmethod
    def generate_pdf_payload(prescription: FinalPrescription) -> str:
        return PDF_TEMPLATE.render(prescription=prescription)

    @staticmethod
    def build_summary(prescription: FinalPrescription) -> Dict[str, str]:
        return {
            "email": PrescriptionGenerator.generate_email(prescription),
            "pdf": PrescriptionGenerator.generate_pdf_payload(prescription),
        }
