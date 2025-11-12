from __future__ import annotations

import csv
from collections import defaultdict
import io
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from django.utils import timezone

from comptabilite.utils import build_email, safe_send


class Command(BaseCommand):
    help = (
        "Envoie chaque lundi la liste des patients convoqués (convocation.csv) "
        "dont la semaine d'examen correspond à la semaine courante."
    )

    CSV_FILENAME = "convocation.csv"
    DATE_FORMATS = (
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%Y/%m/%d",
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Forcer l'envoi même si nous ne sommes pas lundi.",
        )

    def handle(self, *args, **options):
        today = timezone.localdate()
        if today.weekday() != 0 and not options.get("force"):
            self.stdout.write(self.style.WARNING("Commande ignorée car nous ne sommes pas lundi."))
            return

        csv_path = Path(settings.BASE_DIR) / self.CSV_FILENAME
        if not csv_path.exists():
            self.stdout.write(self.style.ERROR(f"Fichier {csv_path} introuvable."))
            return

        current_week = today.isocalendar().week
        threshold_date = self._subtract_years(today, 3)
        highlight_year = self._subtract_years(today, 5).year
        rows_by_year = defaultdict(list)

        try:
            raw_bytes = csv_path.read_bytes()
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Impossible d'ouvrir {csv_path}"))
            return

        text = None
        for encoding in ("utf-8-sig", "latin-1"):
            try:
                text = raw_bytes.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        if text is None:
            self.stdout.write(self.style.ERROR("Impossible de décoder le fichier convocation.csv"))
            return

        sample = text[:2048]
        delimiter = ";" if sample.count(";") >= sample.count(",") else ","
        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        rows = list(reader)

        name_index: dict[str, dict] = {}
        for row in rows:
            exam_date = self._parse_date(row.get("date_examen") or row.get("date") or "")
            if not exam_date or exam_date.year >= 2024:
                continue
            dn = (row.get("dn") or row.get("numero_dossier") or "").strip()
            if not dn:
                continue
            birth_date = self._parse_date(row.get("date_naissance") or row.get("ddn") or "")
            if not birth_date:
                continue
            name_key = self._normalize_name(row.get("nom") or "")
            if not name_key:
                continue
            existing = name_index.get(name_key)
            if not existing or exam_date > existing["exam_date"]:
                name_index[name_key] = {
                    "dn": dn,
                    "birth_date": birth_date,
                    "exam_date": exam_date,
                    "phone": (row.get("telephone") or row.get("tel") or "").strip(),
                }

        enriched_rows = []
        for row in rows:
            row_copy = dict(row)
            exam_date = self._parse_date(row_copy.get("date_examen") or row_copy.get("date") or "")
            if exam_date and exam_date.year == 2024:
                name_key = self._normalize_name(row_copy.get("nom") or "")
                match = name_index.get(name_key) if name_key else None
                if match:
                    if not (row_copy.get("dn") or row_copy.get("numero_dossier")):
                        row_copy["dn"] = match["dn"]
                        row_copy.setdefault("numero_dossier", match["dn"])
                    if not (row_copy.get("date_naissance") or row_copy.get("ddn")):
                        formatted_birth = match["birth_date"].strftime("%d/%m/%Y")
                        row_copy["date_naissance"] = formatted_birth
                        row_copy.setdefault("ddn", formatted_birth)
                    if not (row_copy.get("telephone") or row_copy.get("tel")) and match.get("phone"):
                        row_copy["telephone"] = match["phone"]
                        row_copy.setdefault("tel", match["phone"])
            enriched_rows.append(row_copy)

        rows = enriched_rows

        latest_colo_by_dn = {}
        for row in rows:
            acte_text = (row.get("acte") or row.get("examen") or "").lower()
            if "colo" not in acte_text:
                continue
            dn = (row.get("dn") or row.get("numero_dossier") or "").strip()
            exam_date = self._parse_date(row.get("date_examen") or row.get("date") or "")
            if not dn or not exam_date:
                continue
            previous = latest_colo_by_dn.get(dn)
            if not previous or exam_date > previous:
                latest_colo_by_dn[dn] = exam_date

        for index, row in enumerate(rows, start=1):
            try:
                acte_text = (row.get("acte") or row.get("examen") or "")
                if "colo" not in acte_text.lower():
                    continue

                exam_date = self._parse_date(row.get("date_examen") or row.get("date") or "")
                if not exam_date or exam_date.isocalendar().week != current_week:
                    continue

                dn = (row.get("dn") or row.get("numero_dossier") or "").strip()
                if not dn:
                    continue

                latest_exam = latest_colo_by_dn.get(dn)
                if not latest_exam:
                    continue
                if latest_exam > threshold_date:
                    continue
                if exam_date != latest_exam:
                    continue

                birth_date = self._parse_date(row.get("date_naissance") or row.get("ddn") or "")
                if not birth_date:
                    continue

                age = self._compute_age(birth_date, today)
                if age is None or age > 85:
                    continue

                phone = (row.get("telephone") or row.get("tel") or "").strip()
                if not phone:
                    continue

                raw_name = (row.get("nom") or "").strip()
                nom = raw_name
                prenom = (row.get("prenom") or "").strip()
                if raw_name and not prenom:
                    simplified = raw_name.replace("//", "/")
                    parts = [piece.strip() for piece in simplified.split("/") if piece.strip()]
                    if parts:
                        nom = parts[0]
                        if len(parts) > 1:
                            prenom = " ".join(parts[1:])

                acte = acte_text.strip()

                rows_by_year[exam_date.year].append({
                    "nom": nom,
                    "prenom": prenom,
                    "dn": dn,
                    "exam_date": exam_date,
                    "acte": acte,
                    "telephone": phone,
                    "age": age,
                    "date_naissance": birth_date,
                    "highlight": exam_date.year == highlight_year,
                })
            except Exception as exc:  # pragma: no cover - robust parsing
                self.stdout.write(self.style.WARNING(f"Ligne {index} ignorée ({exc!r})."))

        if not rows_by_year:
            body_context = {
                "today": today,
                "week_number": current_week,
                "entries": [],
                "total": 0,
                "highlight_year": highlight_year,
            }
        else:
            sections = []
            for year in sorted(rows_by_year.keys()):
                patients = sorted(rows_by_year[year], key=lambda x: (x["exam_date"], x["nom"], x["prenom"]))
                sections.append({
                    "year": year,
                    "highlight": year == highlight_year,
                    "patients": patients,
                })
            body_context = {
                "today": today,
                "week_number": current_week,
                "entries": sections,
                "total": sum(len(section["patients"]) for section in sections),
                "highlight_year": highlight_year,
            }

        body = render_to_string("comptabilite/weekly_convocations_email.html", body_context)
        subject = f"Convocations – Semaine {current_week:02d}"
        email = build_email(
            subject,
            body,
            to=["secretariat@bronstein.fr"],
            cc=["docteur@bronstein.fr"],
        )
        email.content_subtype = "html"
        sent = safe_send(email)

        if body_context["total"]:
            self.stdout.write(self.style.SUCCESS(f"Convocations envoyées ({body_context['total']} patients, email={sent})."))
        else:
            self.stdout.write(self.style.WARNING("Aucun patient à notifier pour cette semaine.") )

    def _parse_date(self, raw: str | None):
        value = (raw or "").strip()
        if not value:
            return None
        for fmt in self.DATE_FORMATS:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
        return None

    @staticmethod
    def _compute_age(birth_date, today):
        if not birth_date:
            return None
        years = today.year - birth_date.year
        if (today.month, today.day) < (birth_date.month, birth_date.day):
            years -= 1
        return years

    @staticmethod
    def _subtract_years(base_date, years):
        target_year = base_date.year - years
        try:
            return base_date.replace(year=target_year)
        except ValueError:
            # Gestion du 29 février
            if base_date.month == 2 and base_date.day == 29:
                return base_date.replace(year=target_year, month=2, day=28)
            raise

    @staticmethod
    def _normalize_name(raw_name: str) -> str:
        if not raw_name:
            return ""
        simplified = raw_name.replace("//", "/").replace("-", " ")
        parts = [p.strip() for p in simplified.split("/") if p.strip()]
        if not parts:
            parts = simplified.split()
        normalized = " ".join(parts)
        return " ".join(normalized.lower().split())
