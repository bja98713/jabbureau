from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.signals import user_logged_in
from .models import UserProfile

@receiver(post_save, sender=User)
def create_profile_on_user_creation(sender, instance, created, **kwargs):
    if created and instance and isinstance(instance, User):
        UserProfile.objects.get_or_create(user=instance)

@receiver(user_logged_in)
def ensure_profile_on_login(sender, request, user, **kwargs):
    if user and isinstance(user, User):
        UserProfile.objects.get_or_create(user=user)
