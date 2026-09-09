from __future__ import annotations

from datetime import date
from typing import List

import httpx
import streamlit as st

from app.models.etape1 import Etape1PatientInfo
from app.models.etape2 import Etape2ExamChoice, ExamenType
from app.models.etape3 import (
    COLOSCOPIE_INDICATIONS,
    GASTROSCOPIE_INDICATIONS,
)
from app.models.etape3 import Etape3Indication
from app.models.etape4 import Etape4ClinicalContext
from app.models.etape5 import Etape5MedicalHistory
from app.models.etape6 import (
    Anticoagulant,
    Antiagregant,
    Antidiabetique,
    Etape6Treatments,
)
from app.models.prescription import FinalPrescription

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Prescription Endoscopie", layout="wide")
st.title("Saisie structurée en 6 étapes")

if "current_step" not in st.session_state:
    st.session_state.current_step = 1


def timeline():
    st.sidebar.header("Progression")
    for idx in range(1, 7):
        st.sidebar.checkbox(f"Étape {idx}/6", value=idx <= st.session_state.current_step, disabled=True)
    st.sidebar.progress(st.session_state.current_step / 6)


def go_next():
    st.session_state.current_step = min(6, st.session_state.current_step + 1)


def go_back():
    st.session_state.current_step = max(1, st.session_state.current_step - 1)


def etape1_form():
    col1, col2, col3 = st.columns(3)
    with col1:
        nom = st.text_input("Nom")
        prenom = st.text_input("Prénom")
    with col2:
        date_de_naissance = st.date_input("Date de naissance", value=date(1980, 1, 1))
        email = st.text_input("Email")
    with col3:
        taille_cm = st.number_input("Taille (cm)", min_value=1, step=1)
        poids_kg = st.number_input("Poids (kg)", min_value=0.0, step=0.1, format="%0.1f")
        bmi = st.number_input("BMI (optionnel)", min_value=0.0, step=0.1, format="%0.1f", value=0.0)
    numero_telephone = st.text_input("Téléphone", help="Formats CH +41/0 ou FR +33/0")
    st.info("Le BMI sera recalculé et validé selon la taille/poids.")
    return Etape1PatientInfo(
        nom=nom,
        prenom=prenom,
        date_de_naissance=date_de_naissance,
        taille_cm=int(taille_cm) if taille_cm else 0,
        poids_kg=float(poids_kg) if poids_kg else 0,
        bmi=None if bmi == 0 else bmi,
        email=email,
        numero_telephone=numero_telephone,
    )


def etape2_form():
    examen = st.radio("Choix de l'examen", options=list(ExamenType))
    return Etape2ExamChoice(examen_choisi=examen)


def etape3_form(examen: ExamenType):
    st.write("Indications associées")
    indications: List[str] = []
    if examen == ExamenType.COLOSCOPIE:
        cols = st.columns(2)
        for idx, item in enumerate(COLOSCOPIE_INDICATIONS):
            with cols[idx % 2]:
                if st.checkbox(item, key=f"colo-{item}"):
                    indications.append(item)
        autre = st.text_input("Autre indication (50 caractères max)")
        return Etape3Indication(
            examen_choisi=examen,
            coloscopie_indications=indications,
            autre_indication=autre or None,
        )
    cols = st.columns(2)
    for idx, item in enumerate(GASTROSCOPIE_INDICATIONS):
        with cols[idx % 2]:
            if st.checkbox(item, key=f"gastro-{item}"):
                indications.append(item)
    autre = st.text_input("Autre indication (50 caractères max)")
    return Etape3Indication(
        examen_choisi=examen,
        gastroscopie_indications=indications,
        autre_indication=autre or None,
    )


def etape4_form():
    contexte = st.text_area("Contexte clinique (300 caractères max)", height=120)
    return Etape4ClinicalContext(contexte_clinique=contexte)


def etape5_form():
    st.subheader("Antécédents")
    cols = st.columns(2)
    with cols[0]:
        cardiopathie = st.checkbox("Cardiopathie ischémique")
        avc = st.checkbox("AVC/AIT")
        insuff_renale = st.checkbox("Insuffisance rénale")
    with cols[1]:
        insuff_cardiaque = st.checkbox("Insuffisance cardiaque")
        diabete = st.checkbox("Diabète")
    delai_cardiopathie = st.text_input("Délai cardiopathie") if cardiopathie else None
    delai_avc = st.text_input("Délai AVC/AIT") if avc else None
    delai_insuff_renale = st.text_input("Délai insuffisance rénale") if insuff_renale else None
    delai_insuff_cardiaque = st.text_input("Délai insuffisance cardiaque") if insuff_cardiaque else None
    delai_diabete = st.text_input("Délai diabète") if diabete else None
    return Etape5MedicalHistory(
        cardiopathie_ischemique=cardiopathie,
        delai_cardiopathie=delai_cardiopathie,
        insuffisance_cardiaque=insuff_cardiaque,
        delai_insuffisance_cardiaque=delai_insuff_cardiaque,
        avc_ait=avc,
        delai_avc=delai_avc,
        insuffisance_renale=insuff_renale,
        delai_insuffisance_renale=delai_insuff_renale,
        diabete=diabete,
        delai_diabete=delai_diabete,
    )


def etape6_form():
    st.subheader("Traitements")
    col1, col2, col3 = st.columns(3)
    with col1:
        anticoagulants = st.multiselect(
            "Anticoagulants",
            options=[drug.value for drug in Anticoagulant],
        )
    with col2:
        antiagregants = st.multiselect(
            "Antiagrégants",
            options=[drug.value for drug in Antiagregant],
        )
    with col3:
        antidiabetiques = st.multiselect(
            "Antidiabétiques",
            options=[drug.value for drug in Antidiabetique],
        )
    return Etape6Treatments(
        anticoagulants_choisis=anticoagulants,
        antiagregants_choisis=antiagregants,
        antidiabetiques_choisis=antidiabetiques,
    )


def submit_to_api(prescription: FinalPrescription):
    try:
        response = httpx.post(f"{API_URL}/prescription", json=prescription.dict())
        response.raise_for_status()
        payload = response.json()
        st.success("Prescription envoyée au backend FastAPI")
        st.json(payload)
    except httpx.HTTPError as exc:  # pragma: no cover - affichage utilisateur
        st.error(f"Erreur lors de l'envoi: {exc}")


def render_step(step: int):
    if step == 1:
        patient = etape1_form()
        st.session_state.patient = patient
    elif step == 2:
        examen = etape2_form()
        st.session_state.examen = examen
    elif step == 3:
        examen = st.session_state.get("examen", Etape2ExamChoice(examen_choisi=ExamenType.GASTROSCOPIE))
        st.session_state.indication = etape3_form(examen.examen_choisi)
    elif step == 4:
        st.session_state.contexte = etape4_form()
    elif step == 5:
        st.session_state.antecedents = etape5_form()
    elif step == 6:
        st.session_state.traitements = etape6_form()
        if st.button("Envoyer au backend", type="primary"):
            prescription = FinalPrescription(
                patient=st.session_state.patient,
                examen=st.session_state.examen,
                indication=st.session_state.indication,
                contexte=st.session_state.contexte,
                antecedents=st.session_state.antecedents,
                traitements=st.session_state.traitements,
            )
            submit_to_api(prescription)
    st.write("")


timeline()
st.markdown(f"### Étape {st.session_state.current_step} / 6")
render_step(st.session_state.current_step)
col_prev, col_next = st.columns([1, 1])
with col_prev:
    if st.session_state.current_step > 1 and st.button("← Précédent"):
        go_back()
with col_next:
    if st.session_state.current_step < 6 and st.button("Suivant →", type="primary"):
        go_next()
