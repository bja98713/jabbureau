from django import forms
from django.utils import timezone
from .models import Facturation, Paiement
from .widgets import IntegerNumberInput, CodeSelectWidget

class FacturationForm(forms.ModelForm):
    # Champs de paiement
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
            'date_naissance': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'placeholder': 'JJ/MM/AAAA', 'class': 'form-control', 'type': 'date'}
            ),
            'date_acte': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'placeholder': 'JJ/MM/AAAA', 'class': 'form-control', 'type': 'date'}
            ),
            'date_facture': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'placeholder': 'JJ/MM/AAAA', 'class': 'form-control', 'type': 'date'}
            ),
            'numero_facture': forms.TextInput(attrs={'class': 'form-control'}),
            'total_acte': IntegerNumberInput(attrs={'class': 'form-control'}),
            'tiers_payant': IntegerNumberInput(attrs={'class': 'form-control'}),
            'total_paye': IntegerNumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # si c'est une création (pas d'instance en base)
        if not self.instance.pk:
            today = timezone.localdate()
            self.fields['date_acte'].initial    = today
            self.fields['date_facture'].initial = today
        
        # Formats d’entrée pour les dates
        for fname in ('date_naissance', 'date_acte', 'date_facture'):
            self.fields[fname].input_formats = ['%Y-%m-%d', '%d/%m/%Y']

        # Rendre certains champs facultatifs
        for fname in ('tiers_payant', 'total_paye', 'numero_facture',
                      'code_acte', 'total_acte'):
            self.fields[fname].required = False

        # Pré-remplissage du paiement existant, si on édite
        if self.instance.pk:
            try:
                paiement = self.instance.paiement
                self.fields['modalite_paiement'].initial = paiement.modalite_paiement
                self.fields['banque'].initial = paiement.banque
                self.fields['porteur'].initial = paiement.porteur
            except Paiement.DoesNotExist:
                pass

        # Réordonnancement : modalite_paiement, banque, porteur après total_paye
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

        # Paiement par chèque → banque et porteur obligatoires
        if cleaned.get('modalite_paiement') == 'Chèque':
            if not cleaned.get('banque'):
                self.add_error('banque', "Ce champ est requis pour les paiements par chèque.")
            if not cleaned.get('porteur'):
                self.add_error('porteur', "Ce champ est requis pour les paiements par chèque.")

        # Régime longue maladie → numero_facture obligatoire
        if cleaned.get('regime_lm') and not cleaned.get('numero_facture'):
            self.add_error('numero_facture',
                "Le numéro de facture est requis pour un régime longue maladie."
            )

        return cleaned

    def save(self, commit=True):
        # On récupère d'abord l'instance sans l'enregistrer
        fact = super().save(commit=False)
        user_num = self.cleaned_data.get('numero_facture')
        code = fact.code_acte

        if user_num:
            # L'utilisateur a saisi manuellement un numéro → on le garde
            fact.numero_facture = user_num
        elif code and not code.parcours_soin:
            # Pas de saisie + hors parcours de soins → on génère automatiquement
            now = timezone.localtime()
            fact.numero_facture = now.strftime("FQ/%Y/%m/%d/%H:%M")
        else:
            # Parcours de soins ou aucune condition → on vide le champ
            fact.numero_facture = ''

        if commit:
            fact.save()

        # Gestion du modèle Paiement
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
