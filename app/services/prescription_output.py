from __future__ import annotations

from typing import Dict


class PrescriptionOutputService:
    """Service de sortie statique sans génération par IA.

    Les gabarits sont internes et utilisent simplement les données validées
    pour produire des chaînes simulant l'export (PDF / e-mails).
    """

    def __init__(self) -> None:
        self.pdf_template = """Prescription endoscopique\nPatient: {nom} {prenom}\nExamen: {examen}\nContexte: {contexte}\n"""
        self.specialiste_template = (
            "[Synthèse spécialiste]\n"
            "Examen: {examen}\n"
            "Indications: {indications}\n"
            "Traitements en cours: {traitements}\n"
        )
        self.prescripteur_template = (
            "[Recommandations prescripteur]\n"
            "Anticoagulants: {anticoagulants}\n"
            "Antiagrégants: {antiagregants}\n"
            "Antidiabétiques: {antidiabetiques}\n"
        )

    def generer_pdf(self, data: Dict) -> str:
        patient = data.get("etape1", {})
        contexte = data.get("etape4", {}).get("contexte_clinique", "")
        examen = data.get("etape2", {}).get("examen_choisi", "")
        return self.pdf_template.format(
            nom=patient.get("nom", ""),
            prenom=patient.get("prenom", ""),
            examen=examen,
            contexte=contexte,
        )

    def generer_email_specialiste(self, data: Dict) -> str:
        examen = data.get("etape2", {}).get("examen_choisi", "")
        indications = data.get("etape3", {}).get("coloscopie_indications") or data.get("etape3", {}).get(
            "gastroscopie_indications"
        )
        traitements = data.get("etape6", {})
        traitements_liste = [
            *["Anticoagulant: " + t for t in traitements.get("anticoagulants_choisis", [])],
            *["Antiagrégant: " + t for t in traitements.get("antiagregants_choisis", [])],
            *["Antidiabétique: " + t for t in traitements.get("antidiabetiques_choisis", [])],
        ]
        return self.specialiste_template.format(
            examen=examen,
            indications=", ".join(indications or []),
            traitements=", ".join(traitements_liste) or "Aucun traitement prioritaire",
        )

    def generer_email_prescripteur(self, data: Dict) -> str:
        traitements = data.get("etape6", {})
        return self.prescripteur_template.format(
            anticoagulants=", ".join(traitements.get("anticoagulants_choisis", [])) or "Non renseigné",
            antiagregants=", ".join(traitements.get("antiagregants_choisis", [])) or "Non renseigné",
            antidiabetiques=", ".join(traitements.get("antidiabetiques_choisis", [])) or "Non renseigné",
        )
