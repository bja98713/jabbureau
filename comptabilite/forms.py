from django import forms
from django.utils import timezone
from .models import Facturation, Paiement, ParametrageFacturation
from .widgets import IntegerNumberInput, CodeSelectWidget

### forms.py (extrait corrigé avec incrémentation fiable)

from django import forms
from django.utils import timezone
from .models import Facturation, Paiement, ParametrageFacturation
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
            try:
                param = ParametrageFacturation.objects.first()
                if param:
                    numero = f"{param.prochain_numero}"
                    self.fields['numero_facture'].initial = numero
            except ParametrageFacturation.DoesNotExist:
                self.fields['numero_facture'].initial = "1"

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
        creating = self.instance._state.adding  # fiable
        fact = super().save(commit=False)
        fact.regime_lm = (fact.total_paye in (0, 230, 396))

        user_num = self.cleaned_data.get('numero_facture')
        if user_num:
            fact.numero_facture = user_num

        if commit:
            fact.save()

            if creating:
                param = ParametrageFacturation.objects.first()
                if param:
                    param.prochain_numero += 1
                    param.save()

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
 