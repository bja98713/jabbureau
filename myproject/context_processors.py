import subprocess
from functools import lru_cache


@lru_cache(maxsize=1)
def _get_version():
    """Lit la version Git une seule fois au démarrage du serveur."""
    try:
        count = subprocess.check_output(
            ['git', 'rev-list', '--count', 'HEAD'],
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()
        short_hash = subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'],
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()
        date = subprocess.check_output(
            ['git', 'log', '-1', '--format=%cd', '--date=format:%d/%m/%Y'],
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()
        return f"v{count} ({short_hash}) — {date}"
    except Exception:
        return "v?"


def app_version(request):
    return {'APP_VERSION': _get_version()}
