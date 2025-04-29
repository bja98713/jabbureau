from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from .models import Facturation, Code
from .forms import FacturationForm

# Vue de recherche
class FacturationSearchListView(ListView):
    model = Facturation
    template_name = 'comptabilite/facturation_search_list.html'
    context_object_name = 'facturations'

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(dn__icontains=query) |
                Q(nom__icontains=query) |
                Q(prenom__icontains=query) |
                Q(numero_facture__icontains=query) |
                Q(date_acte__icontains=query)
            )
        return queryset

# Vue pour la liste des facturations
class FacturationListView(ListView):
    model = Facturation
    template_name = 'comptabilite/facturation_list.html'
    context_object_name = 'facturations'

# Vue de création avec le formulaire personnalisé
import json
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .models import Facturation, Code
from .forms import FacturationForm

class FacturationCreateView(CreateView):
    model = Facturation
    form_class = FacturationForm
    template_name = 'comptabilite/facturation_form.html'
    success_url = reverse_lazy('facturation_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Charger tous les codes et préparer un dictionnaire avec les données à transmettre
        codes = Code.objects.all()
        codes_data = {}
        for code in codes:
            # On indexe par la valeur du champ code_acte, ou vous pouvez utiliser code.pk
            codes_data[code.code_acte] = {
                'total_acte': str(code.total_acte),
                'tiers_payant': str(code.tiers_payant),
                'total_paye': str(code.total_paye),
            }
        context['codes_data'] = json.dumps(codes_data)
        return context

# Vue de mise à jour avec le formulaire personnalisé
class FacturationUpdateView(UpdateView):
    model = Facturation
    form_class = FacturationForm
    template_name = 'comptabilite/facturation_form.html'
    success_url = reverse_lazy('facturation_list')

class FacturationDeleteView(DeleteView):
    model = Facturation
    template_name = 'comptabilite/facturation_confirm_delete.html'
    success_url = reverse_lazy('facturation_list')

class FacturationDetailView(DetailView):
    model = Facturation
    template_name = 'comptabilite/facturation_detail.html'
    context_object_name = 'facturation'

def check_dn(request):
    dn = request.GET.get('dn')
    if dn:
        try:
            fact = Facturation.objects.filter(dn=dn).latest('id')
            data = {
                'dn': fact.dn,
                'nom': fact.nom,
                'prenom': fact.prenom,
                'date_naissance': fact.date_naissance.strftime('%Y-%m-%d'),  # Format ISO attendu par type="date"
            }
            return JsonResponse({'exists': True, 'patient': data})
        except Facturation.DoesNotExist:
            pass
    return JsonResponse({'exists': False})

def check_acte(request):
    code_value = request.GET.get('code')
    if code_value:
        try:
            # Récupère l'objet Code par sa clé primaire
            code_obj = Code.objects.get(pk=code_value)
            data = {
                'total_acte': str(code_obj.total_acte),
                'tiers_payant': str(code_obj.tiers_payant),
                'total_paye': str(code_obj.total_paye),
            }
            return JsonResponse({'exists': True, 'data': data})
        except Code.DoesNotExist:
            return JsonResponse({'exists': False})
    return JsonResponse({'exists': False})


def print_facture(request, pk):
    facture = Facturation.objects.get(pk=pk)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="facture_{}.pdf"'.format(facture.numero_facture or facture.pk)
    c = canvas.Canvas(response, pagesize=A4)
    largeur, hauteur = A4

    # Récupération des données
    nom = facture.nom
    prenom = facture.prenom
    date_naissance = facture.date_naissance.strftime("%d/%m/%Y") if facture.date_naissance else ""
    dn = facture.dn
    date_facture = facture.date_facture.strftime("%d/%m/%Y") if facture.date_facture else ""
    total_acte = str(facture.total_acte)
    total_paye = str(facture.total_paye)
    tiers_payant = str(facture.tiers_payant)

    code_obj = facture.code_acte
    if code_obj:
        code_acte_normal = code_obj.code_acte_normal or ""
        variable_1 = code_obj.variable_1 or ""
        modificateur = code_obj.modificateur or ""
        variable_2 = code_obj.variable_2 or ""
        ps = "oui" if code_obj.parcours_soin else "non"
    else:
        code_acte_normal = ""
        variable_1 = ""
        modificateur = ""
        variable_2 = ""
        ps = ""

    if code_obj and code_obj.medecin:
        nom_medecin = code_obj.medecin.nom_medecin
        nom_clinique = code_obj.medecin.nom_clinique
        code_m = code_obj.medecin.code_m
    else:
        nom_medecin = ""
        nom_clinique = ""
        code_m = ""

    regime_lm = ""
    if hasattr(facture, 'regime_lm'):
        regime_lm = "oui" if facture.regime_lm else "non"

    c.drawString(2.0 * cm, hauteur - 3.7 * cm, f"{nom}")
    c.drawString(12.5 * cm, hauteur - 3.7 * cm, f"{prenom}")
    c.drawString(16.0 * cm, hauteur - 4.7 * cm, f"{date_naissance}")
    c.drawString(2.0 * cm, hauteur - 4.7 * cm, f"{dn}")
    c.drawString(2.0 * cm, hauteur - 13.0 * cm, f"{nom_medecin}")
    c.drawString(2.0 * cm, hauteur - 13.5 * cm, f"{nom_clinique}")
    c.drawString(10.5 * cm, hauteur - 12.6 * cm, f"{code_m}")
    c.drawString(2.5 * cm, hauteur - 14.8 * cm, f"{ps}")
    c.drawString(0.3 * cm, hauteur - 16.5 * cm, f"{regime_lm}")
    c.drawString(0.5 * cm, hauteur - 20.3 * cm, f"{date_facture}")
    c.drawString(4.0 * cm, hauteur - 20.3 * cm, f"{code_acte_normal}")
    c.drawString(7.0 * cm, hauteur - 20.3 * cm, f"{variable_1}")
    c.drawString(7.5 * cm, hauteur - 20.3 * cm, f"{modificateur}")
    c.drawString(11.5 * cm, hauteur - 20.3 * cm, f"{variable_2}")
    c.drawString(12.5 * cm, hauteur - 20.3 * cm, f"{total_acte}")
    c.drawString(10.0 * cm, hauteur - 24.3 * cm, f"{total_acte}")
    c.drawString(7.5 * cm, hauteur - 27.6 * cm, f"{total_paye}")
    c.drawString(11.5 * cm, hauteur - 27.6 * cm, f"{tiers_payant}")

    c.save()
    return response

from datetime import date
from django.shortcuts import render
from django.db.models import Q
from .models import Facturation

def create_bordereau(request):
    """
    Cette vue crée un bordereau pour les factures destinées à être encaissées.
    Les factures sont sélectionnées si leur tiers_payant > 0 et si le numéro de bordereau n'est pas défini.
    Pour chaque facture, on met à jour le numéro de bordereau et la date du bordereau.
    Le numéro de bordereau est généré selon le format "M-année-mois-semaine-jour_annee".
    La vue calcule également le nombre de factures et la somme totale du tiers_payant.
    """
    # Sélectionner les factures à traiter
    factures = Facturation.objects.filter(tiers_payant__gt=0).filter(
        Q(numero_bordereau__isnull=True) | Q(numero_bordereau="")
    )
    
    if not factures.exists():
        return render(request, 'comptabilite/bordereau.html', {
            'error': "Aucune facture à traiter pour le bordereau."
        })
    
    # Génération du numéro de bordereau
    today = date.today()
    year = today.year
    month = today.month
    week = today.isocalendar()[1]
    day_of_year = today.timetuple().tm_yday
    num_bordereau = f"M-{year}-{month:02d}-{week:02d}-{day_of_year:03d}"
    
    # Mettre à jour chaque facture avec le numéro et la date du bordereau
    for facture in factures:
        facture.numero_bordereau = num_bordereau
        facture.date_bordereau = today
        facture.save()
    
    # Calculer le nombre de factures et la somme totale du tiers_payant
    count = factures.count()
    total_tiers_payant = sum(facture.tiers_payant for facture in factures)
    
    context = {
        'factures': factures,
        'num_bordereau': num_bordereau,
        'date_bordereau': today.strftime("%d/%m/%Y"),
        'count': count,
        'total_tiers_payant': total_tiers_payant,
    }
    return render(request, 'comptabilite/bordereau.html', context)

import tempfile
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML
from datetime import date
from .models import Facturation

def print_bordereau(request, num_bordereau):
    """
    Génère un PDF pour le bordereau identifié par 'num_bordereau'.
    Suppose que toutes les factures associées ont déjà num_bordereau = ce code.
    """
    # Récupérer les factures associées
    factures = Facturation.objects.filter(numero_bordereau=num_bordereau)
    if not factures.exists():
        return HttpResponse("Aucune facture trouvée pour ce bordereau.", status=404)
    
    # Extraire les infos
    count = factures.count()
    total_tiers_payant = sum(f.tiers_payant for f in factures)

    # On suppose que la date_bordereau est la même pour toutes les factures
    # ou on utilise la date du jour par défaut.
    date_bordereau = factures.first().date_bordereau or date.today()

    context = {
        'num_bordereau': num_bordereau,
        'date_bordereau': date_bordereau.strftime("%d/%m/%Y"),
        'count': count,
        'total_tiers_payant': total_tiers_payant,
        'factures': factures,
    }

    # Rendre le template bordereau_pdf.html en chaîne HTML
    html_string = render_to_string('comptabilite/bordereau_pdf.html', context)

    # Convertir en PDF
    pdf_file = HTML(string=html_string).write_pdf()

    # Soit on enregistre sur disque, soit on renvoie comme réponse HTTP
    # Pour enregistrer sur disque, vous pourriez faire :
    filename = f"{num_bordereau}.pdf"
    with open(filename, "wb") as f:
        f.write(pdf_file)

    # Pour renvoyer le PDF au navigateur :
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

from django.views.generic import ListView
from django.db.models import Q
from datetime import datetime
from .models import Facturation

class ActivityListView(ListView):
    model = Facturation
    template_name = 'comptabilite/activity_list.html'
    context_object_name = 'factures'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Récupérer les paramètres de filtre
        date_str = self.request.GET.get('date')          # format attendu: 'YYYY-MM-DD' ou 'DD/MM/YYYY'
        start_date_str = self.request.GET.get('start_date')  # format ISO ou européen
        end_date_str = self.request.GET.get('end_date')
        year_str = self.request.GET.get('year')            # par exemple: '2025'
        
        if date_str:
            # Tenter de parser en format ISO, sinon format européen
            try:
                filter_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                try:
                    filter_date = datetime.strptime(date_str, '%d/%m/%Y').date()
                except ValueError:
                    filter_date = None
            if filter_date:
                queryset = queryset.filter(date_facture=filter_date)
        elif start_date_str and end_date_str:
            # Tenter de parser start_date
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                try:
                    start_date = datetime.strptime(start_date_str, '%d/%m/%Y').date()
                except ValueError:
                    start_date = None
            # Tenter de parser end_date
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                try:
                    end_date = datetime.strptime(end_date_str, '%d/%m/%Y').date()
                except ValueError:
                    end_date = None
            if start_date and end_date:
                queryset = queryset.filter(date_facture__gte=start_date, date_facture__lte=end_date)
        elif year_str:
            # Filtrer par année
            try:
                year = int(year_str)
                queryset = queryset.filter(date_facture__year=year)
            except ValueError:
                pass
        
        # Vous pouvez ajouter d'autres filtres si nécessaire.
        return queryset.order_by('date_facture')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Transmettre les paramètres de recherche pour les réafficher dans le formulaire
        context['date'] = self.request.GET.get('date', '')
        context['start_date'] = self.request.GET.get('start_date', '')
        context['end_date'] = self.request.GET.get('end_date', '')
        context['year'] = self.request.GET.get('year', '')
        return context
