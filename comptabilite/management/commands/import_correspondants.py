from __future__ import annotations

import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from comptabilite.models import CorrespondantEmail


class Command(BaseCommand):
    help = "Importe les correspondants e-mail depuis un fichier Markdown à deux colonnes (Nom|Adresse e-mail)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            default="tableau_emails.md",
            help="Chemin du fichier Markdown à importer (par défaut: tableau_emails.md à la racine du projet).",
        )
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Supprimer les correspondants existants avant import (remplacement complet).",
        )

    def handle(self, *args, **options):
        file_path = Path(options["file"])
        if not file_path.is_absolute():
            file_path = Path(settings.BASE_DIR) / file_path

        if not file_path.exists():
            raise CommandError(f"Fichier introuvable: {file_path}")

        lines = file_path.read_text(encoding="utf-8").splitlines()
        pattern = re.compile(r"\s*\|\s*")
        records: list[tuple[str, str]] = []
        for raw_line in lines:
            line = raw_line.strip()
            if not line or line.startswith("---"):
                continue
            if line.lower().startswith("nom|"):
                continue
            parts = [part.strip() for part in pattern.split(line, maxsplit=1)]
            if len(parts) < 2:
                continue
            name, email = parts[0], parts[1]
            if not email:
                continue
            records.append((name, email))

        if not records:
            self.stdout.write(self.style.WARNING("Aucun enregistrement détecté dans le fichier."))
            return

        created = 0
        updated = 0
        with transaction.atomic():
            if options.get("replace"):
                CorrespondantEmail.objects.all().delete()
            for name, email in records:
                obj, was_created = CorrespondantEmail.objects.update_or_create(
                    name=name,
                    email=email,
                    defaults={},
                )
                if was_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Import terminé depuis {file_path}. Créés: {created}, mis à jour: {updated}."
            )
        )
