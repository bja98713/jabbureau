# comptabilite/management/commands/backup_sqlite.py
import sqlite3
from pathlib import Path
from datetime import datetime

from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Crée une sauvegarde cohérente de la base SQLite dans le dossier 'backups/'."

    def handle(self, *args, **options):
        base_dir = Path(settings.BASE_DIR)
        db_path = base_dir / 'db.sqlite3'
        if not db_path.exists():
            self.stderr.write(self.style.ERROR(f"Base introuvable: {db_path}"))
            return 1

        backups_dir = base_dir / 'backups'
        backups_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.now().strftime('%Y%m%d-%H%M%S')
        out_path = backups_dir / f"db.{ts}.sqlite3"

        self.stdout.write(f"Sauvegarde en cours → {out_path}")

        # Utilise l'API de backup SQLite (sûre même si la base est utilisée)
        src = sqlite3.connect(str(db_path))
        try:
            dst = sqlite3.connect(str(out_path))
            try:
                src.backup(dst)
            finally:
                dst.close()
        finally:
            src.close()

        self.stdout.write(self.style.SUCCESS(f"Sauvegarde terminée: {out_path}"))
        return 0
