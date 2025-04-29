from django.forms.widgets import Select, NumberInput

class IntegerNumberInput(NumberInput):
    def format_value(self, value):
        if value is None or value == '':
            return ''
        try:
            # Convertir en float, arrondir et convertir en entier
            return str(int(round(float(value))))
        except (ValueError, TypeError):
            return super().format_value(value)

# comptabilite/widgets.py

from django import forms
from django.forms.models import ModelChoiceIteratorValue
from .models import Code

class CodeSelectWidget(forms.Select):
    """
    Un Select qui ajoute en data-attributes les montants liés au code d'acte
    pour pouvoir préremplir total_acte, tiers_payant et total_paye côté JS.
    Cette version gère la ModelChoiceIteratorValue pour en extraire la vraie PK.
    """
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(
            name, value, label, selected,
            index, subindex=subindex, attrs=attrs
        )

        # On récupère la vraie PK : si 'value' est un ModelChoiceIteratorValue, on prend value.value
        if isinstance(value, ModelChoiceIteratorValue):
            raw_pk = value.value
        else:
            raw_pk = value

        if not raw_pk:
            # pas de code sélectionné
            return option

        try:
            code_obj = Code.objects.get(pk=raw_pk)
        except (Code.DoesNotExist, ValueError):
            return option

        def to_int_str(v):
            if v is None:
                return "0"
            try:
                return str(int(round(v)))
            except Exception:
                return "0"

        option['attrs'].update({
            'data-total_acte':   to_int_str(code_obj.total_acte),
            'data-tiers_payant': to_int_str(code_obj.tiers_payant),
            'data-total_paye':   to_int_str(code_obj.total_paye),
        })
        return option


