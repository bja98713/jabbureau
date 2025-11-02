from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic.base import RedirectView as BaseRedirectView
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('accounts/', include('django.contrib.auth.urls')),
    # page de logout (redirection vers la login)
    path('accounts/logout/',
         auth_views.LogoutView.as_view(),
         name='logout'),
    path('admin/', admin.site.urls),
    path('facturation/', include('comptabilite.urls')),
    path('', RedirectView.as_view(url='facturation/patients/')),  # Redirige '/' vers la liste des patients
    # Favicon pour éviter les 404 et afficher une icône personnalisée
    path('favicon.ico', BaseRedirectView.as_view(url=staticfiles_storage.url('images/favicon.svg'), permanent=False)),
]
