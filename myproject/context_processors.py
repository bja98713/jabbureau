import os
import struct
import zlib
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
        # branche normale
        ref_path = git_dir / head_content[5:]
        if not ref_path.exists():
            # packed-refs fallback
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

    # 2. Compter les commits via COMMIT_EDITMSG (approximation) ou packed-refs
    # On compte les fichiers dans .git/logs/HEAD (chaque ligne = 1 commit)
    log_file = git_dir / 'logs' / 'HEAD'
    count = '?'
    date_str = '?'
    if log_file.exists():
        lines = [l for l in log_file.read_text().splitlines() if l.strip()]
        count = str(len(lines))
        # Date du dernier commit depuis la dernière ligne du log
        last_line = lines[-1] if lines else ''
        parts = last_line.split()
        # Format: <hash_ancien> <hash_nouveau> ... <timestamp> <timezone> <message>
        # Le timestamp Unix est le 5ème champ (index 4)
        try:
            import datetime
            ts = int(parts[4])
            date_str = datetime.datetime.utcfromtimestamp(ts).strftime('%d/%m/%Y')
        except Exception:
            date_str = '?'

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
