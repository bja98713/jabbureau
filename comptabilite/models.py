import re

from django.db import models, transaction

class Medecin(models.Model):
    nom_medecin = models.CharField(max_length=100, verbose_name="Nom du Médecin")
    code_m = models.CharField(max_length=50, verbose_name="Code M")
    nom_clinique = models.CharField(max_length=100, verbose_name="Nom de la Clinique")

    def __str__(self):
        return self.nom_medecin

class Code(models.Model):
    # Champs existants avec modification de noms :
    code_acte = models.CharField(max_length=50, unique=True, verbose_name="Code de l'acte")
    total_acte = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Montant total de l'acte")
    tiers_payant = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        null=True,      # autorise NULL en base
        blank=True,     # autorise vide dans les formulaires
        verbose_name="Montant tiers payant"
    )
    total_paye = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        null=True,
        blank=True,
        verbose_name="Total payé"
    )

    medecin = models.ForeignKey(
        Medecin,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Médecin"
    )

    parcours_soin = models.BooleanField(default=False, verbose_name="Parcours de soins")
    longue_maladie = models.BooleanField(default=False, verbose_name="Longue maladie")
    code_reel = models.CharField(max_length=50, null=True, blank=True, verbose_name="Code réel")
    variable_1 = models.CharField(
        max_length=1,
        null=True,
        blank=True,
        verbose_name="Variable 1",
        help_text="Vide ou 1"
    )

    code_acte_normal = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Code Acte Normal"
    )
    variable_2 = models.CharField(
        max_length=1,
        null=True,
        blank=True,
        verbose_name="Variable 2",
        help_text="Vide ou 1"
    )
    modificateur = models.CharField(
        max_length=3,
        null=True,
        blank=True,
        verbose_name="Modificateur",
        help_text="CS, APC ou vide"
    )

    def __str__(self):
        return f"{self.code_acte} - {self.total_acte}xpf"

class Facturation(models.Model):
    """
    Facturation – enregistre les informations administratives d'une facture.
    """
    dn = models.CharField(
        max_length=7,
        verbose_name="DN (numéro à 7 chiffres)"
    )
    nom = models.CharField(
        max_length=100,
        verbose_name="Nom du patient"
    )
    prenom = models.CharField(
        max_length=100,
        verbose_name="Prénom du patient"
    )
    date_naissance = models.DateField(
        verbose_name="Date de naissance"
    )

    date_acte = models.DateField(
        verbose_name="Date de l'acte"
    )
    date_facture = models.DateField(
        verbose_name="Date de la facture"
    )

    REGIME_CHOICES = [
        ('Sécurité Sociale', 'Sécurité Sociale'),
        ('RNS', 'RNS'),
        ('Salarié', 'Salarié'),
        ('RST', 'RST'),
    ]
    regime = models.CharField(
        max_length=20,
        choices=REGIME_CHOICES,
        verbose_name="Régime"
    )

    droit_ouvert = models.BooleanField(
        default=False,
        verbose_name="Droits ouverts : (oui/non)"
    )

    regime_tp = models.BooleanField(
        default=False,
        verbose_name="Tiers Payants : (oui/non)"
    )

    regime_lm = models.BooleanField(
        default=False,
        verbose_name="Régime LM (oui/non)"
    )

    LIEU_CHOICES = [
        ('Cabinet', 'Cabinet'),
        ('Clinique', 'Clinique')
    ]
    lieu_acte = models.CharField(
        max_length=50,
        choices=LIEU_CHOICES,
        default='Cabinet',
        verbose_name="Lieu de l'acte"
    )

    code_acte = models.ForeignKey(
        Code,
        null=True,      # autorise NULL en base
        blank=True,
        on_delete=models.CASCADE,
        related_name='facturations',
        verbose_name="Code de l'acte"
    )

    numero_facture = models.CharField(
        max_length=50,
        null=True,      # autorise NULL en base
        blank=True,     # autorise vide dans les formulaires
        verbose_name="Numéro de facture"
    )

    total_acte = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        null=True,      # autorise NULL en base
        blank=True,     # autorise vide dans les formulaires
        verbose_name="Montant total de l'acte (facturé)"
    )
    tiers_payant = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        null=True,      # ici
        blank=True,     # et ici
        verbose_name="Montant tiers payant"
    )
    total_paye = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        null=True,
        blank=True,
        verbose_name="Total payé"
    )

    STATUT_CHOICES = [
        ('RAS', 'RAS'),
        ('DNO', 'DNO'),
        ('DNOLM', 'DNOLM'),
        ('Impayé', 'Impayé'),
        ('Rejet', 'Rejet'),
    ]
    statut_dossier = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='RAS',
        verbose_name="Statut du dossier"
    )

    numero_rejet = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Numéro de rejet"
    )
    numero_bordereau = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Numéro de bordereau"
    )
    date_bordereau = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date du bordereau"
    )
    remarque = models.TextField(
        null=True,
        blank=True,
        verbose_name="Remarques"
    )

    def __str__(self):
        return f"Facture n°{self.numero_facture} - {self.nom} {self.prenom}"
    
    def _assign_numero_si_besoin(self):
        """
        Assigne un numéro en s'appuyant sur ParametrageFacturation (compteur global),
        mais uniquement si aucun numéro n'est déjà présent.
        """
        if self.numero_facture:
            return

        # Incrément protégé (verrou SQL) pour éviter les collisions en concurrence
        from .models import ParametrageFacturation  # import local pour éviter les cycles
        with transaction.atomic():
            cfg = ParametrageFacturation.objects.select_for_update().first()
            if cfg is None:
                cfg = ParametrageFacturation.objects.create(prochain_numero=1)
            numero = cfg.prochain_numero
            cfg.prochain_numero = numero + 1
            cfg.save(update_fields=['prochain_numero'])

        # ⚠️ Formate le numéro ici comme tu le souhaites (je mets juste l'entier)
        self.numero_facture = str(numero)

    def save(self, *args, **kwargs):
        """
        Verrou dur :
        - Si lieu_acte == 'Clinique' → on NE prend PAS de numéro (on n'incrémente rien),
          et on force numero_facture vide.
        - Sinon → on assigne un numéro uniquement si self.numero_facture est vide.
        """
        if (getattr(self, 'lieu_acte', '') or '').lower() == 'clinique':
            # Important : ne surtout pas consommer le compteur ici
            self.numero_facture = ''
            return super().save(*args, **kwargs)

        # Hors Clinique → assigner si besoin (et donc consommer le compteur ici, et ici SEULEMENT)
        if not getattr(self, 'numero_facture', ''):
            self._assign_numero_si_besoin()

        return super().save(*args, **kwargs)

# Nouvelle table Paiement
class Paiement(models.Model):
    # On suppose qu'un paiement correspond à une facture unique.
    facture = models.OneToOneField(Facturation, on_delete=models.CASCADE, related_name='paiement')
    date = models.DateField(
        verbose_name="Date de paiement",
        null=True,
        blank=True
    )
    MODALITE_CHOICES = [
        ('-----', '-----'),
        ('CB', 'Carte Bancaire'),
        ('Chèque', 'Chèque'),
        ('Liquide', 'Liquide'),
        ('Virement', 'Virement'),
        ('Gratuit', 'Gratuit'),
    ]
    modalite_paiement = models.CharField(
        max_length=20,
        choices=MODALITE_CHOICES,
        verbose_name="Modalité de paiement"
    )
    BANQUE_CHOICES = [
        ('Banque de Tahiti', 'Banque de Tahiti'),
        ('Socredo', 'Socredo'),
        ('Banque de Polynésie', 'Banque de Polynésie'),
        ('CCP', 'CCP'),
    ]
    banque = models.CharField(
        max_length=50,
        choices=BANQUE_CHOICES,
        verbose_name="Banque"
    )
    porteur = models.CharField(
        max_length=100,
        verbose_name="Porteur"
    )
    montant = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        verbose_name="Montant",
        null=True,
        blank=True
    )

    liste = models.BooleanField(
        default=False,
        verbose_name="Listé",
        help_text="Coché quand ce chèque a été listé"
    )

    def __str__(self):
        return f"{self.date} – {self.montant} xpf – {'Oui' if self.liste else 'Non'}"

    def save(self, *args, **kwargs):
        # Avant de sauvegarder, on remplit la date et le montant à partir de la facture associée s'ils ne sont pas renseignés.
        if self.facture:
            if not self.date:
                self.date = self.facture.date_facture
            if not self.montant:
                self.montant = self.facture.total_paye
        super().save(*args, **kwargs)

    # (supprimé doublon __str__)

# === Nouvelle table Observation (au niveau module, pas à l'intérieur de Paiement) ===
class Observation(models.Model):
    """Observation médicale liée à un patient identifié par DN.

    Champs principaux:
    - dn: identifiant patient
    - nom, prenom, date_naissance: infos patient (recopiées pour facilité d'affichage)
    - date_observation: date du jour par défaut
    - motif_consultation, texte_observation, conclusion_observation: contenus saisis
    """
    dn = models.CharField(max_length=7, db_index=True, verbose_name="DN")
    nom = models.CharField(max_length=100, verbose_name="Nom")
    prenom = models.CharField(max_length=100, verbose_name="Prénom")
    date_naissance = models.DateField(null=True, blank=True, verbose_name="Date de naissance")

    date_observation = models.DateField(auto_now_add=True, verbose_name="Date de l'observation")

    motif_consultation = models.CharField(max_length=255, verbose_name="Motif de consultation")
    texte_observation = models.TextField(verbose_name="Observation")
    conclusion_observation = models.TextField(blank=True, verbose_name="Conclusion")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date_observation", "-created_at"]
        indexes = [
            models.Index(fields=["dn", "date_observation"]),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.dn} - {self.date_observation} - {self.motif_consultation[:30]}"


class Bibliographie(models.Model):
    """Fiche de bibliographie médicale indexée par codes CIM-10."""

    titre = models.CharField(max_length=200, unique=True, verbose_name="Titre")
    reference = models.CharField(max_length=255, blank=True, verbose_name="Référence")
    resume = models.TextField(blank=True, verbose_name="Résumé")
    texte = models.TextField(blank=True, verbose_name="Texte complet")
    lien = models.URLField(blank=True, verbose_name="Lien externe")
    codes_cim10 = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Codes CIM-10",
        help_text="Séparez les codes par une virgule ou un espace."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["titre"]
        verbose_name = "Bibliographie"
        verbose_name_plural = "Bibliographies"

    def __str__(self) -> str:  # pragma: no cover
        return self.titre

    def codes_list(self):
        raw = self.codes_cim10 or ""
        return [code.strip().upper() for code in re.split(r"[;,\s]+", raw) if code.strip()]


# === Table Patient (référentiel central par DN) ===
class Patient(models.Model):
    dn = models.CharField(max_length=7, unique=True, db_index=True, verbose_name="DN")
    nom = models.CharField(max_length=100, verbose_name="Nom")
    prenom = models.CharField(max_length=100, verbose_name="Prénom")
    date_naissance = models.DateField(null=True, blank=True, verbose_name="Date de naissance")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nom", "prenom"]
        verbose_name = "Patient"
        verbose_name_plural = "Patients"

    def __str__(self):  # pragma: no cover
        return f"{self.nom} {self.prenom} ({self.dn})"


# === Courrier médical par patient ===
class Courrier(models.Model):
    TYPE_CHOICES = [
        ('FOGD', 'Fibroscopie gastrique'),
        ('COLO', 'Coloscopie'),
        ('ECHO', 'Échographie abdominale'),
        ('SYN',  'Courrier de synthèse'),
        ('CONS', 'Fiche de consentement éclairé'),
        ('ATRE', 'Attestation de retour'),
    ]

    dn = models.CharField(max_length=7, db_index=True, verbose_name="DN")
    nom = models.CharField(max_length=100, verbose_name="Nom")
    prenom = models.CharField(max_length=100, verbose_name="Prénom")
    date_naissance = models.DateField(null=True, blank=True, verbose_name="Date de naissance")

    type_courrier = models.CharField(max_length=5, choices=TYPE_CHOICES, verbose_name="Type de courrier")
    date_courrier = models.DateField(auto_now_add=True, verbose_name="Date du courrier")
    corps = models.TextField(verbose_name="Texte du courrier")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date_courrier", "-created_at"]
        indexes = [
            models.Index(fields=["dn", "date_courrier"]),
        ]

    def type_label(self):
        return dict(self.TYPE_CHOICES).get(self.type_courrier, self.type_courrier)

    def __str__(self):  # pragma: no cover
        return f"{self.type_label()} – {self.nom} {self.prenom} ({self.dn})"


class CourrierPhoto(models.Model):
    """Photo associée à un courrier (max 4 par courrier)."""
    courrier = models.ForeignKey(Courrier, related_name='photos', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='courrier_photos/%Y/%m/%d')
    position = models.PositiveSmallIntegerField(default=1, help_text="Ordre d'affichage (1-4)")
    legend = models.CharField(max_length=120, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['position', 'id']
        constraints = [
            models.UniqueConstraint(fields=['courrier', 'position'], name='uniq_photo_position_par_courrier')
        ]

    def __str__(self):  # pragma: no cover
        return f"Photo {self.position} du courrier {self.courrier_id}"


# === Rappel Anapath (biopsies) après FOGD/COLO ===
class BiopsyReminder(models.Model):
    EXAM_CHOICES = [
        ('FOGD', 'Fibroscopie gastrique'),
        ('COLO', 'Coloscopie'),
    ]
    DEST_CHOICES = [
        ('CERBA', 'CERBA - France'),
        ('CHT', 'Service anatomo-pathologie - CHT'),
    ]

    dn = models.CharField(max_length=7, db_index=True, verbose_name="DN")
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField(null=True, blank=True)

    type_examen = models.CharField(max_length=4, choices=EXAM_CHOICES)
    destination = models.CharField(max_length=10, choices=DEST_CHOICES)

    exam_date = models.DateField()
    send_on = models.DateField(db_index=True, help_text="Date prévue d'envoi du rappel")

    sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-send_on", "-created_at"]
        indexes = [
            models.Index(fields=["dn", "send_on", "sent"]),
        ]

    def destination_label(self):
        return dict(self.DEST_CHOICES).get(self.destination, self.destination)

    def __str__(self):  # pragma: no cover
        when = self.send_on.strftime('%d/%m/%Y') if self.send_on else '—'
        return f"Rappel anapath {self.type_examen} – {self.nom} {self.prenom} ({self.dn}) le {when} → {self.destination_label()}"

from django.db import models

class Statistique(models.Model):
    """
    Statistiques mensuelles de l'activité par lieu.
    """
    year = models.PositiveSmallIntegerField(verbose_name="Année")
    month = models.PositiveSmallIntegerField(verbose_name="Mois (1-12)")
    total_acte_cabinet = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Total des actes au Cabinet"
    )
    total_acte_clinique = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Total des actes en Clinique"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        unique_together = (('year', 'month'),)
        verbose_name = "Statistique mensuelle"
        verbose_name_plural = "Statistiques mensuelles"

from django.db import models

class PrevisionHospitalisation(models.Model):
    dn = models.CharField(max_length=20)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField()

    date_entree = models.DateField(null=True, blank=True)
    date_bloc = models.DateField(null=True, blank=True)
    date_sortie = models.DateField(null=True, blank=True)
    date_sortie_theorique = models.DateField(null=True, blank=True)
    motif_hospitalisation = models.CharField(max_length=255)
    lieu_hospitalisation = models.CharField(max_length=50, choices=[
        ('Médecine', 'Médecine'),
        ('Bloc', 'Bloc'),
        ('Soins Intensifs', 'Soins Intensifs'),
    ])

    cs_anesthesie = models.BooleanField(default=False, verbose_name="Consultation anesthésie")
    fo_ag = models.BooleanField(default=False, verbose_name="FOGD / AG")
    colo_ag = models.BooleanField(default=False, verbose_name="Coloscopie / AG")
    fo_al = models.BooleanField(default=False, verbose_name="FOGD sans AG")
    colo_al = models.BooleanField(default=False, verbose_name="Coloscopie sans AG")
    eeh_ag = models.BooleanField(default=False, verbose_name="Echo-Endoscopie Haute / AG")
    eeb_al = models.BooleanField(default=False, verbose_name="Echo-Endoscopie basse sans AG")
    cs_cardiologie = models.BooleanField(default=False, verbose_name="Consultation cardiologie")
    cs_pneumologie = models.BooleanField(default=False, verbose_name="Consultation pneumologie")
    cs_dermatologie = models.BooleanField(default=False, verbose_name="Consultation dermatologie")

    courrier = models.TextField(blank=True)
    remarque = models.CharField(max_length=255, blank=True)

    @property
    def date_sortie_theorique(self):
        return self.date_sortie or self.date_entree + timezone.timedelta(days=1)

    def __str__(self):
        return f"{self.nom} {self.prenom} ({self.dn})"

from django.db import models
from django.contrib.auth.models import User

class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    lu = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"De {self.sender} à {self.receiver} : {self.content[:30]}"

# models.py

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    last_seen = models.DateTimeField(default=timezone.now)
    # Cache JSON (string) des derniers destinataires utilisés par type de courrier
    # Format: {"FOGD": {"to": ["a@exemple.com"], "cc": ["b@exemple.com"]}, ...}
    email_recipient_cache = models.TextField(blank=True, default='{}')

    def is_online(self):
        return timezone.now() - self.last_seen < timezone.timedelta(minutes=5)

class ParametrageFacturation(models.Model):
    prochain_numero = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"Prochain numéro de facture : {self.prochain_numero}"