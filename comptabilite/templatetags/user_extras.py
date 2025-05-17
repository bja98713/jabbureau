from django import template
from django.contrib.auth.models import AnonymousUser
from comptabilite.models import UserProfile

register = template.Library()

@register.simple_tag
def get_user_profile(user):
    if isinstance(user, AnonymousUser):
        return None  # ou un objet factice si besoin
    if not hasattr(user, 'userprofile'):
        return UserProfile.objects.create(user=user)
    return user.userprofile
