import re
from django import forms
from django.db import transaction
from django.utils import timezone
from .models import (
    Facturation,
    Paiement,
    ParametrageFacturation,
    Observation,
    Patient,
    Courrier,
    Bibliographie,
    CorrespondantEmail,
)
from .widgets import IntegerNumberInput, CodeSelectWidget

class FacturationForm(forms.ModelForm):
    modalite_paiement = forms.ChoiceField(
        choices=Paiement.MODALITE_CHOICES,
        required=False,
        label="Modalité de paiement",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    banque = forms.ChoiceField(
        choices=Paiement.BANQUE_CHOICES,
        required=False,
        label="Banque",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    porteur = forms.CharField(
        required=False,
        label="Porteur",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Facturation
        fields = '__all__'
        widgets = {
            'code_acte': CodeSelectWidget(attrs={'class': 'form-control'}),
            'date_naissance': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'date_acte': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'date_facture': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'numero_facture': forms.TextInput(attrs={'class': 'form-control'}),
            'total_acte': IntegerNumberInput(attrs={'class': 'form-control'}),
            'tiers_payant': IntegerNumberInput(attrs={'class': 'form-control'}),
            'total_paye': IntegerNumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            today = timezone.localdate()
            self.fields['date_acte'].initial = today
            self.fields['date_facture'].initial = today
            param = ParametrageFacturation.objects.first()
            self.fields['numero_facture'].initial = str(param.prochain_numero if param else 1)

        for fname in ('date_naissance', 'date_acte', 'date_facture'):
            self.fields[fname].input_formats = ['%Y-%m-%d', '%d/%m/%Y']
        for fname in ('tiers_payant', 'total_paye', 'numero_facture', 'code_acte', 'total_acte'):
            self.fields[fname].required = False

        order = list(self.fields.keys())
        for key in ('modalite_paiement', 'banque', 'porteur'):
            if key in order:
                order.remove(key)
        if 'total_paye' in order:
            idx = order.index('total_paye')
            order[idx+1:idx+1] = ['modalite_paiement', 'banque', 'porteur']
        self.order_fields(order)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('modalite_paiement') == 'Chèque':
            if not cleaned.get('banque'):
                self.add_error('banque', "Ce champ est requis pour les paiements par chèque.")
            if not cleaned.get('porteur'):
                self.add_error('porteur', "Ce champ est requis pour les paiements par chèque.")

        total_paye = cleaned.get("total_paye")
        if total_paye in (0, 230, 396):
            cleaned["regime_lm"] = True
        else:
            cleaned["regime_lm"] = False
        return cleaned

    def save(self, commit=True):
        creating = self.instance._state.adding
        fact = super().save(commit=False)
        # Régime LM déduit du total_paye
        fact.regime_lm = (fact.total_paye in (0, 230, 396))

        # Verrou clinique : jamais de numéro et surtout pas d'incrément.
        if (getattr(fact, 'lieu_acte', '') or '').lower() == 'clinique':
            fact.numero_facture = ''

        if commit:
            fact.save()

            if creating and (getattr(fact, 'lieu_acte', '') or '').lower() != 'clinique' and fact.numero_facture:
                with transaction.atomic():
                    param = ParametrageFacturation.objects.select_for_update().first()
                    if param is None:
                        param = ParametrageFacturation.objects.create(prochain_numero=1)
                    try:
                        prochain_numero = int(fact.numero_facture) + 1
                    except (TypeError, ValueError):
                        prochain_numero = param.prochain_numero + 1
                    if param.prochain_numero < prochain_numero:
                        param.prochain_numero = prochain_numero
                        param.save(update_fields=['prochain_numero'])

            # Gestion du paiement
            modalite = self.cleaned_data.get('modalite_paiement')
            if modalite:
                paiement, _ = Paiement.objects.get_or_create(facture=fact)
                paiement.modalite_paiement = modalite
                if modalite == 'Chèque':
                    paiement.banque = self.cleaned_data.get('banque', '')
                    paiement.porteur = self.cleaned_data.get('porteur', '')
                else:
                    paiement.banque = ''
                    paiement.porteur = ''
                paiement.save()

        return fact



    
from .models import PrevisionHospitalisation

class PrevisionHospitalisationForm(forms.ModelForm):
    class Meta:
        model = PrevisionHospitalisation
        fields = '__all__'
        widgets = {
            'date_naissance': forms.DateInput(attrs={
                'class': 'form-control datepicker',
                'autocomplete': 'off',
            }),
            'date_entree': forms.DateInput(attrs={
                'class': 'form-control datepicker',
                'autocomplete': 'off',
            }),
            'date_bloc': forms.DateInput(attrs={
                'class': 'form-control datepicker',
                'autocomplete': 'off',
            }),
            'date_sortie': forms.DateInput(attrs={
                'class': 'form-control datepicker',
                'autocomplete': 'off',
            }),
            'courrier': forms.Textarea(attrs={'rows': 6, 'cols': 60}),
            'remarque': forms.Textarea(attrs={'rows': 3, 'cols': 60}),
        }
 
class CourrierForm(forms.ModelForm):
    class Meta:
        model = Courrier
        fields = [
            'dn', 'nom', 'prenom', 'date_naissance',
            'type_courrier', 'corps'
        ]
        widgets = {
            'dn': forms.TextInput(attrs={'class': 'form-control'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control'}),
            'date_naissance': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'type_courrier': forms.Select(attrs={'class': 'form-control'}),
            'corps': forms.Textarea(attrs={'class': 'form-control', 'rows': 8}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Accept both YYYY-MM-DD and DD/MM/YYYY for date_naissance
        self.fields['date_naissance'].input_formats = ['%Y-%m-%d', '%d/%m/%Y']

# ===== Observations =====
class ObservationForm(forms.ModelForm):
    class Meta:
        model = Observation
        # date_observation est auto_now_add, on ne l'expose pas dans le formulaire
        fields = [
            'dn', 'nom', 'prenom', 'date_naissance',
            'motif_consultation', 'texte_observation', 'conclusion_observation'
        ]
        widgets = {
            'dn': forms.TextInput(attrs={'class': 'form-control'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control'}),
            'date_naissance': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'motif_consultation': forms.TextInput(attrs={'class': 'form-control'}),
            'texte_observation': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'conclusion_observation': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def clean(self):
        cleaned = super().clean()
        dn = (cleaned.get('dn') or '').strip()
        if dn:
            # Si le DN existe dans Facturation, on force les infos patient à celles de la dernière facture (verrou solide)
            fact = Facturation.objects.filter(dn=dn).order_by('-date_acte', '-id').first()
            if fact:
                cleaned['nom'] = fact.nom
                cleaned['prenom'] = fact.prenom
                cleaned['date_naissance'] = fact.date_naissance
            # Sinon, DN inconnu : on laisse la saisie utilisateur telle quelle
        return cleaned


class BibliographieForm(forms.ModelForm):
    codes_cim10 = forms.CharField(
        required=False,
        label="Codes CIM-10",
        help_text="Séparez les codes par une virgule ou un espace.",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'K52, A09'})
    )

    class Meta:
        model = Bibliographie
        fields = ['titre', 'resume', 'texte', 'reference', 'lien', 'codes_cim10']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'reference': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Liste des sources, articles, ouvrages…'}),
            'resume': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'texte': forms.Textarea(attrs={'class': 'form-control', 'rows': 8}),
            'lien': forms.URLInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'reference': 'Références bibliographiques',
        }

    def clean_codes_cim10(self):
        raw = self.cleaned_data.get('codes_cim10', '') or ''
        parts = [p.strip().upper() for p in re.split(r"[;,\s]+", raw) if p.strip()]
        return ", ".join(sorted(dict.fromkeys(parts)))



# ===== Patients =====
class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['nom', 'prenom', 'date_naissance']  # DN non éditable ici
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control'}),
            'date_naissance': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
        }


class CorrespondantEmailForm(forms.ModelForm):
    class Meta:
        model = CorrespondantEmail
        fields = ['name', 'email', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom ou structure'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'adresse@example.com'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Informations complémentaires (optionnel)'}),
        }
