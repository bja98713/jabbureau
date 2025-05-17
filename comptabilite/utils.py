# utils.py
def get_user_profile(user):
    from comptabilite.models import UserProfile
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile
