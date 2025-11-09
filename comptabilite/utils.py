# utils.py
from typing import Iterable, Optional, Dict, Any
import re
import os
import re
import json

from django.conf import settings
from django.core.mail import EmailMessage, get_connection
import smtplib


def get_user_profile(user):
    from comptabilite.models import UserProfile
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def _load_recipient_cache(user) -> Dict[str, Any]:
    try:
        prof = get_user_profile(user)
        return json.loads(prof.email_recipient_cache or '{}')
    except Exception:
        return {}


def _save_recipient_cache(user, cache: Dict[str, Any]):
    try:
        prof = get_user_profile(user)
        prof.email_recipient_cache = json.dumps(cache)
        prof.save(update_fields=['email_recipient_cache'])
    except Exception:
        pass


def remember_recipients(user, courrier_type: str, to_list: Iterable[str], cc_list: Iterable[str]):
    """Persist last used recipients for a given user and courrier type."""
    key = (courrier_type or '').upper() or 'DEFAULT'
    cache = _load_recipient_cache(user)
    cache[key] = {
        'to': list(dict.fromkeys([x.strip().lower() for x in (to_list or []) if x.strip()])),
        'cc': list(dict.fromkeys([x.strip().lower() for x in (cc_list or []) if x.strip()])),
    }
    _save_recipient_cache(user, cache)


def get_remembered_recipients(user, courrier_type: str):
    key = (courrier_type or '').upper() or 'DEFAULT'
    cache = _load_recipient_cache(user)
    return cache.get(key) or {}


def _normalize_subject(subject: str) -> str:
    """Reduce risky patterns for spam filters: ASCII dashes, collapse spaces."""
    s = (subject or "").replace("\n", " ").strip()
    # Replace en/em dashes and unusual punctuation with simple hyphen
    s = s.replace("–", "-").replace("—", "-")
    # Collapse multiple spaces
    s = re.sub(r"\s+", " ", s)
    return s


def _brand_subject(subject: str) -> str:
    """Optionnellement préfixer le sujet par une marque.

    Contrôlable via variables d'env:
    - DISABLE_SUBJECT_BRAND=1 pour désactiver totalement le préfixe.
    - EMAIL_BRAND_PREFIX="Texte" pour changer la marque (défaut: Cabinet Dr Bronstein).
    """
    # Par défaut on désactive le préfixe de marque pour réduire le risque de marquage [SPAM]
    disable = os.getenv('DISABLE_SUBJECT_BRAND', '1').lower() in ('1','true','yes','on')
    brand = os.getenv('EMAIL_BRAND_PREFIX', 'Cabinet Dr Bronstein').strip()
    s = _normalize_subject(subject)
    if disable or not brand:
        return s  # pas de marque
    # Éviter double préfixe
    if s.lower().startswith(brand.lower()):
        return s
    return f"{brand} - {s}" if s else brand


def build_email(subject: str,
                body: str,
                to: Iterable[str],
                cc: Optional[Iterable[str]] = None) -> EmailMessage:
    """Construit un EmailMessage avec des en-têtes favorables à la délivrabilité.

    - Préfixe sujet par la marque pour améliorer la réputation.
    - From: settings.DEFAULT_FROM_EMAIL (doit être aligné à EMAIL_HOST_USER).
    - Reply-To: 'docteur@bronstein.fr' (ou EMAIL_HOST_USER à défaut).
    - Headers: X-Mailer, Auto-Submitted.
    """
    # Désactiver tout préfixe de marque pour réduire le risque de [SPAM]
    subj = _normalize_subject(subject)
    # Utiliser strictement l'adresse authentifiée pour le From (meilleure délivrabilité)
    from_email = getattr(settings, 'EMAIL_HOST_USER', None) or getattr(settings, 'DEFAULT_FROM_EMAIL', None)
    # Forcer l'adresse de réponse vers docteur@bronstein.fr (ou DEFAULT_REPLY_TO si défini)
    reply_to_addr = getattr(settings, 'DEFAULT_REPLY_TO', None) or 'docteur@bronstein.fr'
    reply_to = [reply_to_addr]

    email = EmailMessage(
        subject=subj,
        body=body or "",
        from_email=from_email,
        to=list(to or []),
        headers={
            'X-Mailer': 'Jabbureau',
            'Auto-Submitted': 'no',
        },
    )
    if cc:
        email.cc = list(cc)
    email.reply_to = reply_to
    return email


def safe_send(email: EmailMessage) -> int:
    """Envoie un e‑mail de façon robuste.

    - Tente l'envoi via le backend configuré.
    - En cas d'erreur d'authentification (530/535) ou d'erreur SMTP générique,
      se rabat sur le backend console pour ne pas bloquer l'action utilisateur.
    - Retourne le nombre de messages envoyés (ou affichés en console).
    """
    try:
        return email.send(fail_silently=False)
    except (smtplib.SMTPAuthenticationError, smtplib.SMTPSenderRefused, smtplib.SMTPRecipientsRefused, smtplib.SMTPException):
        # Fallback console
        try:
            conn = get_connection('django.core.mail.backends.console.EmailBackend')
            return conn.send_messages([email]) or 0
        except Exception:
            return 0
