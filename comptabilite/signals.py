from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.signals import user_logged_in
from .models import UserProfile, Observation, Patient, Facturation

@receiver(post_save, sender=User)
def create_profile_on_user_creation(sender, instance, created, **kwargs):
    if created and instance and isinstance(instance, User):
        UserProfile.objects.get_or_create(user=instance)

@receiver(user_logged_in)
def ensure_profile_on_login(sender, request, user, **kwargs):
    if user and isinstance(user, User):
        UserProfile.objects.get_or_create(user=user)


# ===== Sync Patient on Observation save =====
@receiver(post_save, sender=Observation)
def upsert_patient_from_observation(sender, instance: Observation, created: bool, **kwargs):
    """Crée ou met à jour la fiche Patient (référentiel) à chaque sauvegarde d'une Observation.

    Règle: DN = clé. On copie nom, prénom, date_naissance depuis l'observation.
    """
    if not instance or not instance.dn:
        return

    dn = instance.dn.strip()
    if not dn:
        return

    patient, _ = Patient.objects.get_or_create(dn=dn, defaults={
        'nom': instance.nom or '',
        'prenom': instance.prenom or '',
        'date_naissance': instance.date_naissance,
    })

    # Mettre à jour si différences
    updated = False
    if instance.nom and patient.nom != instance.nom:
        patient.nom = instance.nom
        updated = True
    if instance.prenom and patient.prenom != instance.prenom:
        patient.prenom = instance.prenom
        updated = True
    if (instance.date_naissance or patient.date_naissance) and patient.date_naissance != instance.date_naissance:
        patient.date_naissance = instance.date_naissance
        updated = True

    if updated:
        patient.save(update_fields=['nom', 'prenom', 'date_naissance', 'updated_at'])


@receiver(post_save, sender=Facturation)
def upsert_patient_from_facturation(sender, instance: Facturation, created: bool, **kwargs):
    """Crée ou met à jour la fiche Patient à chaque sauvegarde de Facturation.

    DN = clé. Source d'autorité pour identité: Facturation (nom, prénom, date_naissance).
    """
    if not instance or not instance.dn:
        return
    dn = instance.dn.strip()
    if not dn:
        return

    patient, _ = Patient.objects.get_or_create(dn=dn, defaults={
        'nom': instance.nom or '',
        'prenom': instance.prenom or '',
        'date_naissance': instance.date_naissance,
    })

    fields = []
    if patient.nom != (instance.nom or ''):
        patient.nom = instance.nom or ''
        fields.append('nom')
    if patient.prenom != (instance.prenom or ''):
        patient.prenom = instance.prenom or ''
        fields.append('prenom')
    if patient.date_naissance != instance.date_naissance:
        patient.date_naissance = instance.date_naissance
        fields.append('date_naissance')
    if fields:
        patient.save(update_fields=fields + ['updated_at'])
