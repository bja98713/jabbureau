from django.urls import path
from . import views
from .views import remise_cheque, ComptabiliteSummaryView, FacturationListView, FacturationCreateView

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
]

