# utils.py
from typing import Iterable, Optional
import re

from django.conf import settings
from django.core.mail import EmailMessage


def get_user_profile(user):
    from comptabilite.models import UserProfile
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def _normalize_subject(subject: str) -> str:
    """Reduce risky patterns for spam filters: ASCII dashes, collapse spaces."""
    s = (subject or "").replace("\n", " ").strip()
    # Replace en/em dashes and unusual punctuation with simple hyphen
    s = s.replace("–", "-").replace("—", "-")
    # Collapse multiple spaces
    s = re.sub(r"\s+", " ", s)
    return s


def _brand_subject(subject: str) -> str:
    base = "Cabinet Dr Bronstein"
    s = _normalize_subject(subject)
    # Évite de doubler le préfixe si déjà présent (insensible à la casse)
    if s.lower().startswith(base.lower()):
        return s
    return f"{base} – {s}" if s else base


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
    subj = _brand_subject(subject)
    # Utiliser strictement l'adresse authentifiée pour le From (meilleure délivrabilité)
    from_email = getattr(settings, 'EMAIL_HOST_USER', None) or getattr(settings, 'DEFAULT_FROM_EMAIL', None)
    reply_to = [getattr(settings, 'EMAIL_HOST_USER', None) or getattr(settings, 'DEFAULT_REPLY_TO', None) or 'docteur@bronstein.fr']

    email = EmailMessage(
        subject=_normalize_subject(subj),
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
