import os
from pathlib import Path

# Chargeur .env optionnel: ne casse pas si python-dotenv n'est pas installé en prod
try:
    from dotenv import load_dotenv  # type: ignore
except Exception:  # ImportError ou autre
    def load_dotenv(*args, **kwargs):  # type: ignore
        return False

# Chemin de base du projet
BASE_DIR = Path(__file__).resolve().parent.parent

# Charger les variables d'environnement depuis un fichier .env si présent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('SECRET_KEY', 'please-set-a-strong-secret-key')

# DEBUG: str -> bool ("True"/"False")
DEBUG = os.getenv('DEBUG', 'True').lower() in ('1','true','yes','on')

# ALLOWED_HOSTS depuis env (liste séparée par des virgules)
ALLOWED_HOSTS = [h.strip() for h in os.getenv('ALLOWED_HOSTS', 'www.docteur-bronstein.com,127.0.0.1').split(',') if h.strip()]


# Application 'comptabilite' + apps par défaut
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'comptabilite',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # <— doit être là
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'comptabilite.middleware.UpdateLastSeenMiddleware',
    # … votre propre middleware ici …
]

ROOT_URLCONF = 'myproject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [ BASE_DIR /'templates' ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',          # nécessaire pour l’admin et pour avoir request dans vos templates
                'django.contrib.auth.context_processors.auth',         # nécessaire pour admin + {{ user }} dans vos templates
                'django.contrib.messages.context_processors.messages', # nécessaire pour admin + le framework de messages
                # … conservez ici les autres que vous aviez déjà, par ex. debug, i18n, static, etc.
            ],
        },
    },
]


WSGI_APPLICATION = 'myproject.wsgi.application'

# Base de données SQLite par défaut
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Configuration pour l’internationalisation (langue, fuseau horaire)
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Pacific/Tahiti'
USE_I18N = True
USE_L10N = True
USE_TZ = True

DATE_INPUT_FORMATS = ['%d/%m/%Y', '%Y-%m-%d']


# Configuration des fichiers statiques


STATIC_URL = '/static/'

# ✅ Dossier unique de sortie pour collectstatic
STATIC_ROOT = BASE_DIR / 'staticfiles'

# ✅ Dossiers à chercher en développement
STATICFILES_DIRS = [ BASE_DIR / 'static' ]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/facturation/patients/'  # redirige vers la liste des patients après connexion
LOGOUT_REDIRECT_URL = 'login'

EMAIL_BACKEND       = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST          = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT          = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS       = os.getenv('EMAIL_USE_TLS', 'True').lower() in ('1','true','yes','on')

EMAIL_HOST_USER     = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')

# Par défaut, utiliser l'adresse authentifiée comme expéditeur si disponible
_default_from = f"Pr. Jean-Ariel Bronstein <{EMAIL_HOST_USER}>" if EMAIL_HOST_USER else 'Pr. Jean-Ariel Bronstein <no-reply@example.com>'
DEFAULT_FROM_EMAIL  = os.getenv('DEFAULT_FROM_EMAIL', _default_from)
SERVER_EMAIL        = os.getenv('SERVER_EMAIL', EMAIL_HOST_USER or 'server@example.com')

# Réglages de sécurité appliqués seulement en production
if not DEBUG:
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = 'same-origin'
    SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

