from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.templatetags.static import static
from django.http import HttpResponseRedirect
from django.contrib.auth import views as auth_views


def _favicon_redirect(request):
    return HttpResponseRedirect(static('images/favicon.svg'))

urlpatterns = [
    path('accounts/', include('django.contrib.auth.urls')),
    # page de logout (redirection vers la login)
    path('accounts/logout/',
         auth_views.LogoutView.as_view(),
         name='logout'),
    path('admin/', admin.site.urls),
    path('facturation/', include('comptabilite.urls')),
    path('', RedirectView.as_view(url='facturation/patients/')),  # Redirige '/' vers la liste des patients
    # Icônes: évalue l'URL statique à l'exécution pour éviter les erreurs à l'import (prod/manifests)
    path('favicon.ico', _favicon_redirect),
    path('apple-touch-icon.png', _favicon_redirect),
    path('apple-touch-icon-precomposed.png', _favicon_redirect),
]
