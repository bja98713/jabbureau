from django import template
from comptabilite.models import UserProfile

register = template.Library()

@register.simple_tag
def get_user_profile(user):
    if user and user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=user)
        return profile
    return None
