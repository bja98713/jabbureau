from django.db import models

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

    def __str__(self):
        return f"Paiement de facture {self.facture.numero_facture} - {self.montant} xpf"
