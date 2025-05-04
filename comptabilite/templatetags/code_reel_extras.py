# app/templatetags/code_reel_extras.py
from django import template

register = template.Library()

@register.filter(
    name='code_reel_default',
    is_safe=False
)
def code_reel_default(value):
    """
    Remplace la valeur None, chaîne vide ou 'None' par 'CS'.
    Autrement, renvoie la valeur d'origine.
    """
    # Si la valeur est falsy (None, '', 0…) ou littéralement 'None'
    if not value or str(value) == "None":
        return "CS"
    return value
