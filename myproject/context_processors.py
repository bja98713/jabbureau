import os
import re
import datetime
from functools import lru_cache
from pathlib import Path
from django.conf import settings


def _read_git_files():
    """Lit les infos de version directement dans les fichiers .git/ sans subprocess."""
    git_dir = Path(settings.BASE_DIR) / '.git'

    # 1. Lire le hash HEAD
    head_file = git_dir / 'HEAD'
    if not head_file.exists():
        return None, None, None

    head_content = head_file.read_text().strip()
    if head_content.startswith('ref: '):
        ref_path = git_dir / head_content[5:]
        if not ref_path.exists():
            packed = git_dir / 'packed-refs'
            if packed.exists():
                ref_name = head_content[5:]
                for line in packed.read_text().splitlines():
                    if line.endswith(ref_name):
                        full_hash = line.split()[0]
                        break
                else:
                    return None, None, None
            else:
                return None, None, None
        else:
            full_hash = ref_path.read_text().strip()
    else:
        full_hash = head_content

    short_hash = full_hash[:7]

    # 2. Compter les commits et lire la date depuis .git/logs/HEAD
    log_file = git_dir / 'logs' / 'HEAD'
    count = '?'
    date_str = '?'
    if log_file.exists():
        lines = [l for l in log_file.read_text().splitlines() if l.strip()]
        count = str(len(lines))
        # Le timestamp Unix est un nombre de 10 chiffres suivi d'un fuseau horaire (+HHMM)
        # Format d'une ligne : <hash> <hash> Name <email> <timestamp> <+HHMM>\t<message>
        last_line = lines[-1] if lines else ''
        m = re.search(r'(\d{10})\s+[+-]\d{4}', last_line)
        if m:
            ts = int(m.group(1))
            date_str = datetime.datetime.utcfromtimestamp(ts).strftime('%d/%m/%Y')

    return count, short_hash, date_str


@lru_cache(maxsize=1)
def _get_version():
    """Lit la version Git une seule fois au démarrage du serveur."""
    try:
        count, short_hash, date_str = _read_git_files()
        if count and short_hash:
            return f"v{count} ({short_hash}) — {date_str}"
        return "v?"
    except Exception:
        return "v?"


def app_version(request):
    return {'APP_VERSION': _get_version()}
