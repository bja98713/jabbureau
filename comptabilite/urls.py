from django.urls import path
from . import views
from .views import remise_cheque, ComptabiliteSummaryView, FacturationListView, FacturationCreateView
from django.contrib.auth.views import LogoutView
from .views import (
    prevision_list,
    prevision_create,
    prevision_detail,
    prevision_pdf,
    prevision_send_email,
    prevision_update,
    prevision_delete,
    chat_view, 
    get_messages, 
    send_message,
    patients_hospitalises,
    patients_hospitalises_pdf,
    patients_hospitalises_excel,
    print_facture,
    imprimer_fiche_facturation
)

urlpatterns = [
    path('', views.FacturationListView.as_view(), name='facturation_list'),
    path('nouveau/', views.FacturationCreateView.as_view(), name='facturation_create'),
    path('<int:pk>/', views.FacturationDetailView.as_view(), name='facturation_detail'),
    path('<int:pk>/modifier/', views.FacturationUpdateView.as_view(), name='facturation_update'),
    path('<int:pk>/supprimer/', views.FacturationDeleteView.as_view(), name='facturation_delete'),
    path('recherche/', views.FacturationSearchListView.as_view(), name='facturation_search_list'),
    path('ajax/check_dn/', views.check_dn, name='check_dn'),
    path('ajax/check_acte/', views.check_acte, name='check_acte'),
    path('imprimer/<int:pk>/', views.print_facture, name='print_facture'),
    path('bordereau/', views.create_bordereau, name='create_bordereau'),
    path('bordereau/print/<str:num_bordereau>/', views.print_bordereau, name='print_bordereau'),
    path('activity/', views.ActivityListView.as_view(), name='activity_list'),
    path('cheques/choix/', views.choix_date_cheques, name='choix_date_cheques'),
    path('cheques/', views.cheque_listing, name='cheque_listing'),
    path('remise-cheque/', remise_cheque, name='remise_cheque'),
    path('cheques/pdf/', views.print_cheque_listing, name='print_cheque_listing'),
    path('<int:pk>/generate_numero/', views.generate_numero, name='generate_numero'),
    path('comptabilite/', ComptabiliteSummaryView.as_view(), name='comptabilite_summary'),
    path('accounts/logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('previsions/', prevision_list, name='prevision_list'),
    path('previsions/nouveau/', prevision_create, name='prevision_create'),
    path('previsions/<int:pk>/', prevision_detail, name='prevision_detail'),
    path('previsions/<int:pk>/pdf/', prevision_pdf, name='prevision_pdf'),
    path('previsions/<int:pk>/email/', prevision_send_email, name='prevision_send_email'),
    path('previsions/<int:pk>/modifier/', prevision_update, name='prevision_update'),
    path('previsions/<int:pk>/supprimer/', prevision_delete, name='prevision_delete'),
    path('previsions/<int:pk>/envoyer/', prevision_send_email, name='prevision_send_email'),
    path('chat/<int:receiver_id>/', chat_view, name='chat_view'),
    path('chat/get/', get_messages, name='get_messages'),
    path('chat/send/', send_message, name='send_message'),
    path("patients_hospitalises/", patients_hospitalises, name="patients_hospitalises"),
    path("patients_hospitalises/pdf/", patients_hospitalises_pdf, name="patients_hospitalises_pdf"),
    path("patients_hospitalises/excel/", patients_hospitalises_excel, name="patients_hospitalises_excel"),
    path('facture/<int:pk>/print/', print_facture, name='print_facture'),
    path('facturation/<int:pk>/fiche/', imprimer_fiche_facturation, name='imprimer_fiche_facturation'),
]