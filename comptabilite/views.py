from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from .models import Facturation, Code, Paiement
from .forms import FacturationForm
from django.utils import timezone

import pdfkit
from django.conf import settings

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

from datetime import timedelta
import calendar

from decimal import Decimal

from django.template.loader import get_template
from django.http import HttpResponse
from weasyprint import HTML
import tempfile

from django.core.mail import EmailMessage

from django.db import models




# Vue de recherche
class FacturationSearchListView(ListView):from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
import calendar

class FacturationSearchListView(LoginRequiredMixin, ListView):
    login_url = 'login'
    redirect_field_name = 'next'   # paramètre renvoyé après login
    model = Facturation
    template_name = 'comptabilite/facturation_search_list.html'
    context_object_name = 'facturations'

    def get_queryset(self):
        qs = super().get_queryset()

        # 1) Recherche textuelle "q"
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(
                Q(dn__icontains=q) |
                Q(nom__icontains=q) |
                Q(prenom__icontains=q) |
                Q(numero_facture__icontains=q) |
                Q(date_acte__icontains=q) |
                Q(code_acte__code_acte__icontains=q)
            )

        # 2) Filtrage selon la période
        today = timezone.localdate()
        if self.request.GET.get('today'):
            qs = qs.filter(date_acte=today)

        if self.request.GET.get('week'):
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week   = start_of_week + timedelta(days=6)
            qs = qs.filter(date_acte__gte=start_of_week,
                           date_acte__lte=end_of_week)

        if self.request.GET.get('month'):
            first_of_month = today.replace(day=1)
            last_day       = calendar.monthrange(today.year, today.month)[1]
            last_of_month  = today.replace(day=last_day)
            qs = qs.filter(date_acte__gte=first_of_month,
                           date_acte__lte=last_of_month)

        return qs.order_by('-date_acte')  # ou l'ordre que vous préférez


# Vue pour la liste des facturations
class FacturationListView(LoginRequiredMixin, ListView):
    login_url = 'login'
    redirect_field_name = 'next'   # paramètre renvoyé après login
    model = Facturation
    template_name = 'comptabilite/facturation_list.html'
    context_object_name = 'facturations'

    def get_queryset(self):
        qs = super().get_queryset()
        # Si on a coché la case “today” dans le GET, on ne garde que les factures du jour
        if self.request.GET.get('today'):
            today = timezone.localdate()
            qs = qs.filter(date_acte=today)
        return qs

# Vue de création avec le formulaire personnalisé
import json
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .models import Facturation, Code
from .forms import FacturationForm

class FacturationCreateView(LoginRequiredMixin, CreateView):
    login_url = 'login'
    redirect_field_name = 'next'   # paramètre renvoyé après login
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
class FacturationUpdateView(LoginRequiredMixin, UpdateView):
    login_url = 'login'
    redirect_field_name = 'next'   # paramètre renvoyé après login
    model = Facturation
    form_class = FacturationForm
    template_name = 'comptabilite/facturation_form.html'
    success_url = reverse_lazy('facturation_list')

class FacturationDeleteView(DeleteView):
    model = Facturation
    template_name = 'comptabilite/facturation_confirm_delete.html'
    success_url = reverse_lazy('facturation_list')

class FacturationDetailView(LoginRequiredMixin, DetailView):
    login_url = 'login'
    redirect_field_name = 'next'   # paramètre renvoyé après login
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
                'total_acte': str(int(round(code_obj.total_acte))),
                'tiers_payant': str(int(round(code_obj.tiers_payant))),
                'total_paye': str(int(round(code_obj.total_paye))),
            }
            return JsonResponse({'exists': True, 'data': data})
        except Code.DoesNotExist:
            return JsonResponse({'exists': False})
    return JsonResponse({'exists': False})


from django.shortcuts import get_object_or_404
from django.utils import timezone

def print_facture(request, pk):
    facture = get_object_or_404(Facturation, pk=pk)
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
        ps = "X" if code_obj.parcours_soin else ""
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
        regime_lm = "X" if facture.regime_lm else ""

    # Si hors parcours de soins ET pas encore de numéro, on le génère et on enregistre
    if not facture.code_acte.parcours_soin and not facture.numero_facture:
        now = timezone.localtime()
        facture.numero_facture = now.strftime("JA/%Y/%m/%d/%H:%M")
        facture.save()

    c.drawString(2.0 * cm, hauteur - 3.7 * cm, f"{nom}")
    c.drawString(12.5 * cm, hauteur - 3.7 * cm, f"{prenom}")
    c.drawString(16.0 * cm, hauteur - 4.7 * cm, f"{date_naissance}")
    c.drawString(2.0 * cm, hauteur - 4.7 * cm, f"{dn}")
    c.drawString(2.0 * cm, hauteur - 13.0 * cm, f"{nom_medecin}")
    c.drawString(2.0 * cm, hauteur - 13.5 * cm, f"{nom_clinique}")
    c.drawString(10.5 * cm, hauteur - 12.6 * cm, f"{code_m}")
    c.drawString(2.5 * cm, hauteur - 14.8 * cm, f"{ps}")
    if facture.regime_lm:
        c.drawString(0.3 * cm, hauteur - 16.5 * cm, f"{regime_lm}")
    c.drawString(0.5 * cm, hauteur - 20.3 * cm, f"{date_facture}")
    c.drawString(4.0 * cm, hauteur - 20.3 * cm, f"{code_acte_normal}")
    c.drawString(7.0 * cm, hauteur - 20.3 * cm, f"{variable_1}")
    c.drawString(7.5 * cm, hauteur - 20.3 * cm, f"{modificateur}")
    c.drawString(11.5 * cm, hauteur - 20.3 * cm, f"{variable_2}")
    c.drawString(12.5 * cm, hauteur - 20.3 * cm, f"{total_acte}")
    c.drawString(10.0 * cm, hauteur - 24.3 * cm, f"{total_acte}")
    if facture.regime_lm or facture.tiers_payant and facture.tiers_payant != Decimal('0'):
        c.drawString(7.5 * cm, hauteur - 27.6 * cm, f"{total_paye}")
        c.drawString(11.5 * cm, hauteur - 27.6 * cm, f"{tiers_payant}")

    c.save()
    return response

from datetime import date
from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from .models import Facturation

@login_required
def create_bordereau(request):
    """
    Aperçu des factures à bordereauter, triées par numero_facture,
    sans rien modifier en base.
    """
    factures = (
        Facturation.objects
        .filter(tiers_payant__gt=0)
        .filter(Q(numero_bordereau__isnull=True) | Q(numero_bordereau=""))
        .order_by('numero_facture')
    )

    if not factures.exists():
        return render(request, 'comptabilite/bordereau.html', {
            'error': "Aucune facture à traiter pour le bordereau."
        })

    today = date.today()
    week = today.isocalendar()[1]
    day_of_year = today.timetuple().tm_yday
    num_bordereau = f"M{today.year}-{today.month:02d}-{week:02d}-{day_of_year:03d}"

    context = {
        'factures': factures,
        'num_bordereau': num_bordereau,
        'date_bordereau': today.strftime("%d/%m/%Y"),
        'count': factures.count(),
        'total_tiers_payant': factures.aggregate(total=Sum('tiers_payant'))['total'] or 0,
    }
    return render(request, 'comptabilite/bordereau.html', context)


from datetime import date
from django.db.models import Sum, Q
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from .models import Facturation

def print_bordereau(request, num_bordereau):
    """
    Impression du bordereau :
    - On sélectionne les factures non encore bordereautées.
    - On les matérialise dans une liste pour l’affichage.
    - On les met à jour en base.
    - On génère le PDF à partir de la liste déjà chargée.
    """
    # 1) QuerySet initial
    qs = (Facturation.objects
          .filter(tiers_payant__gt=0)
          .filter(Q(numero_bordereau__isnull=True) | Q(numero_bordereau=""))
          .order_by('numero_facture'))

    if not qs.exists():
        return HttpResponse("Aucune facture à imprimer pour ce bordereau.", status=404)

    # 2) On matérialise avant update
    factures_list = list(qs)

    # 3) Totaux
    count = len(factures_list)
    total_tiers = sum(f.tiers_payant for f in factures_list)

    # 4) Mise à jour en base
    today = date.today()
    qs.update(numero_bordereau=num_bordereau, date_bordereau=today)

    # 5) Contexte, on passe la liste « figée »
    context = {
        'num_bordereau':      num_bordereau,
        'date_bordereau':     today.strftime("%d/%m/%Y"),
        'count':              count,
        'total_tiers_payant': total_tiers,
        'factures':           factures_list,
    }

    # 6) Génération du PDF
    html_string = render_to_string('comptabilite/bordereau_pdf.html', context)
    pdf_file    = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{num_bordereau}.pdf"'
    return response


from django.views.generic import ListView
from django.db.models import Q
from datetime import datetime
from .models import Facturation

# comptabilite/views.py
from django.views.generic import ListView
from django.db.models import Sum
from .models import Facturation
from datetime import datetime

class ActivityListView(LoginRequiredMixin, ListView):
    login_url = 'login'
    redirect_field_name = 'next'   # paramètre renvoyé après login
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
        # Récupérer les filtres pour les réafficher (optionnel)
        context['date'] = self.request.GET.get('date', '')
        context['start_date'] = self.request.GET.get('start_date', '')
        context['end_date'] = self.request.GET.get('end_date', '')
        context['year'] = self.request.GET.get('year', '')
        # Calculer les totaux pour les trois dernières colonnes
        aggregates = self.get_queryset().aggregate(
            sum_total_acte=Sum('total_acte'),
            sum_tiers_payant=Sum('tiers_payant'),
            sum_total_paye=Sum('total_paye')
        )
        context['sum_total_acte'] = aggregates['sum_total_acte'] or 0
        context['sum_tiers_payant'] = aggregates['sum_tiers_payant'] or 0
        context['sum_total_paye'] = aggregates['sum_total_paye'] or 0
        return context

# comptabilite/views.py

from django.shortcuts import render, redirect
from datetime import datetime, date
from django.db.models import Sum
from .models import Paiement

from django.shortcuts import render, redirect
from datetime import date
from django.db.models import Sum
from .models import Paiement

@login_required
def cheque_listing(request):
    # POST : on coche tous les chèques non listés dont la date ≤ aujourd'hui
    if request.method == 'POST':
        Paiement.objects.filter(
            modalite_paiement="Chèque",
            date__lte=date.today(),
            liste=False
        ).update(liste=True)
        return redirect('cheque_listing')

    # GET : on n'affiche que ceux qui ne sont pas encore listés
    cheques = Paiement.objects.filter(
        modalite_paiement="Chèque",
        date__lte=date.today(),
        liste=False
    )
    count = cheques.count()
    total_montant = cheques.aggregate(total=Sum('montant'))['total'] or 0

    return render(request, 'comptabilite/cheque_listing.html', {
        'cheques': cheques,
        'count': count,
        'total_montant': total_montant,
        'filter_date': date.today().strftime("%d/%m/%Y"),
    })




from datetime import date, datetime
from django.shortcuts import render, redirect

def choix_date_cheques(request):
    """
    Permet de choisir la date pour la remise des chèques.
    Si l'utilisateur sélectionne "Aujourd'hui", on redirige avec la date du jour.
    Sinon, on utilise la date saisie.
    """
    if request.method == 'POST':
        option = request.POST.get('date_option')
        if option == 'today':
            chosen_date = date.today().strftime('%Y-%m-%d')
            return redirect(f"/facturation/cheques/?date={chosen_date}")
        elif option == 'other':
            other_date = request.POST.get('other_date')
            if other_date:
                # On s'assure que la date est valide ; ici, on suppose qu'elle est saisie en format ISO.
                try:
                    datetime.strptime(other_date, '%Y-%m-%d')
                    return redirect(f"/facturation/cheques/?date={other_date}")
                except ValueError:
                    # Si la date n'est pas au format attendu, on peut réafficher le formulaire avec une erreur.
                    context = {'error': "Format de date invalide. Veuillez utiliser le format AAAA-MM-JJ."}
                    return render(request, 'comptabilite/choix_date_cheques.html', context)
    return render(request, 'comptabilite/choix_date_cheques.html', {})


from django.forms.widgets import NumberInput

class IntegerNumberInput(NumberInput):
    def format_value(self, value):
        if value is None or value == '':
            return ''
        try:
            # Convertir en entier pour enlever les décimales.
            return str(int(round(float(value))))
        except (ValueError, TypeError):
            return super().format_value(value)

import pdfkit
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.conf import settings
from .models import Paiement
from django.utils import timezone
from django.template.loader import render_to_string

def remise_cheque(request):
    """
    Affiche la liste des paiements (chèques) non listés et à date <= aujourd'hui,
    puis, quand on valide (POST), marque 'listé' = True et renvoie le PDF.
    """
    today = timezone.localdate()

    # Si on vient de valider le formulaire (méthode POST)
    if request.method == 'POST':
        # Récupère tous les chèques encore non listés, date <= aujourd'hui
        cheques = Paiement.objects.filter(
            modalite_paiement='Chèque',
            date__lte=today,
            liste=False
        )
        # Marquer chacun comme listé
        cheques.update(liste=True)

        # Recalculer le contexte pour le PDF
        count = cheques.count()
        total = cheques.aggregate(total=models.Sum('montant'))['total'] or 0

        context = {
            'cheques': cheques,
            'count': count,
            'date_cheque': today.strftime('%d/%m/%Y'),
            'total_montant': total,
        }

        # Rendre le HTML du bordereau
        html = render_to_string('comptabilite/remise_cheque_pdf.html', context)

        # Générer le PDF
        pdf = pdfkit.from_string(html, False, options=settings.PDFKIT_OPTIONS)

        # Renvoyer le PDF au navigateur
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="remise_cheque_{today}.pdf"'
        return response

    # Sinon (GET), on affiche le listing et le bouton de validation
    cheques = Paiement.objects.filter(
        modalite_paiement='Chèque',
        date__lte=today,
        liste=False
    )
    count = cheques.count()
    total = cheques.aggregate(total=models.Sum('montant'))['total'] or 0

    return render(request, 'comptabilite/remise_cheque.html', {
        'cheques': cheques,
        'count': count,
        'date_cheque': today.strftime('%d/%m/%Y'),
        'total_montant': total,
    })

import io
from datetime import datetime, date
from django.db.models import Sum
from django.shortcuts import redirect
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from .models import Paiement

def print_cheque_listing(request):
    from datetime import datetime, date
    import io
    from django.db.models import Sum
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas
    from .models import Paiement

    # 1. Récupération de la date
    d_str = request.GET.get('date')
    if d_str:
        try:
            filter_date = datetime.strptime(d_str, '%Y-%m-%d').date()
        except ValueError:
            try:
                filter_date = datetime.strptime(d_str, '%d/%m/%Y').date()
            except ValueError:
                filter_date = date.today()
    else:
        filter_date = date.today()

    # 2. Requête initiale (liste=False)
    qs = Paiement.objects.filter(
        modalite_paiement="Chèque",
        date__lte=filter_date,
        liste=False
    ).order_by('date')

    # 3. On cashe en mémoire AVANT le .update()
    cheques = list(qs)
    if not cheques:
        # rien à lister → retour à la liste
        return redirect('cheque_listing')

    count = len(cheques)
    total_montant = sum(ch.montant for ch in cheques)

    # 4. On marque TOUTES ces lignes comme « listées »
    qs.update(liste=True)

    # 5. Construction du PDF
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 2*cm
    c.setFont('Helvetica-Bold', 16)
    c.drawString(2*cm, y, "Dr. Jean-Ariel BRONSTEIN | Gastroentérologue")
    y -= 1*cm

    y = height - 2*cm
    c.setFont('Helvetica-Bold', 16)
    c.drawString(2*cm, y, "Rue Lagarde | Papeete")
    y -= 1*cm

    c.setFont('Helvetica-Bold', 16)
    c.drawString(2*cm, y, f"Remise de {count} Chèqu(es)")
    y -= 1*cm

    c.setFont('Helvetica', 12)
    c.drawString(2*cm, y, f"Date de remise : {filter_date.strftime('%d/%m/%Y')}")
    y -= 1*cm

    # En‑tête du tableau
    c.setFont('Helvetica-Bold', 12)
    xs = [2*cm, 6*cm, 10*cm, 14*cm]
    for x, title in zip(xs, ["Date", "Banque", "Porteur", "Montant"]):
        c.drawString(x, y, title)
    y -= 0.7*cm

    # Lignes détaillées
    c.setFont('Helvetica', 11)
    for ch in cheques:
        if y < 2*cm:
            c.showPage()
            y = height - 2*cm
            # on ré‑affiche l’en‑tête
            c.setFont('Helvetica-Bold', 12)
            for x, title in zip(xs, ["Date", "Banque", "Porteur", "Montant"]):
                c.drawString(x, y, title)
            y -= 0.7*cm
            c.setFont('Helvetica', 11)

        c.drawString(xs[0], y, ch.date.strftime('%d/%m/%Y'))
        c.drawString(xs[1], y, ch.banque or "")
        c.drawString(xs[2], y, ch.porteur or "")
        c.drawRightString(xs[3] + 3*cm, y, f"{int(ch.montant)}")
        y -= 0.7*cm

    # Total en bas
    y -= 1*cm
    c.setFont('Helvetica-Bold', 12)
    c.drawString(2*cm, y, f"Nombre de chèque(s) : {count}   Total des montants : {int(total_montant)}")

    c.save()
    buffer.seek(0)

    # 6. Retour HTTP
    filename = f"remise_cheque_{filter_date.strftime('%Y%m%d')}.pdf"
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from .models import Facturation

def generate_numero(request, pk):
    """
    Génère et sauvegarde un numero_facture pour la Facturation pk
    si elle n'en a pas encore et que parcours_soin == False.
    """
    facture = get_object_or_404(Facturation.objects.select_related('code_acte'), pk=pk)
    code = facture.code_acte
    # seulement si pas déjà généré et hors parcours de soins
    if not facture.numero_facture and not (code and code.parcours_soin):
        now = timezone.localtime()
        facture.numero_facture = (
            f"JA/{now.year}/{now.month:02d}/{now.day:02d}/"
            f"{now.hour:02d}:{now.minute:02d}"
        )
        facture.save(update_fields=['numero_facture'])
    return JsonResponse({'numero_facture': facture.numero_facture or ""})

# views.py

from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
from .models import Facturation

from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
from .models import Facturation

class ComptabiliteSummaryView(LoginRequiredMixin, ListView):
    login_url = 'login'
    redirect_field_name = 'next'
    model = Facturation
    template_name = 'comptabilite/comptabilite_summary.html'
    context_object_name = 'summary_rows'

    def get_queryset(self):
        qs = super().get_queryset()
        period = self.request.GET.get('period', '')
        today = timezone.localdate()

        if period == 'today':
            qs = qs.filter(date_facture=today)
        elif period == 'week':
            start = today - timedelta(days=today.weekday())
            end = start + timedelta(days=6)
            qs = qs.filter(date_facture__range=(start, end))
        elif period == 'month':
            qs = qs.filter(date_facture__year=today.year, date_facture__month=today.month)
        elif period == 'year':
            qs = qs.filter(date_facture__year=today.year)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        qs = self.get_queryset()

        # Période (pour réaffichage)
        ctx['period_choices'] = [
            ('', 'Toutes'),
            ('today', "Aujourd'hui"),
            ('week', 'Cette semaine'),
            ('month', 'Ce mois'),
            ('year', "Cette année"),
        ]
        ctx['period'] = self.request.GET.get('period', '')

        # Lecture des cases à cocher
        ctx['group_regime']    = bool(self.request.GET.get('group_regime'))
        ctx['group_modalite']  = bool(self.request.GET.get('group_modalite'))
        ctx['group_code_reel'] = bool(self.request.GET.get('group_code_reel'))
        ctx['group_lieu']      = bool(self.request.GET.get('group_lieu'))

        # Pivot par régime
        if ctx['group_regime']:
            rows = (qs.values('regime')
                     .annotate(
                         count=Count('id'),
                         total_acte=Sum('total_acte'),
                         total_paye=Sum('total_paye')
                     )
                  )
        else:
            rows = []
        ctx['pivot_regime'] = rows
        ctx['totals_regime'] = {
            'count': sum(r['count'] for r in rows),
            'total_acte': sum(r['total_acte'] or 0 for r in rows),
            'total_paye': sum(r['total_paye'] or 0 for r in rows),
        }

        # Pivot par modalité
        if ctx['group_modalite']:
            tmp = (qs.select_related('paiement')
                     .values('paiement__modalite_paiement')
                     .annotate(
                         count=Count('id'),
                         total_acte=Sum('total_acte'),
                         total_paye=Sum('total_paye')
                     )
                     .order_by('paiement__modalite_paiement')
                  )
            rows_mod = [
                {'label': r['paiement__modalite_paiement'], **r}
                for r in tmp
            ]
        else:
            rows_mod = []
        ctx['pivot_modalite'] = rows_mod
        ctx['totals_modalite'] = {
            'count': sum(r['count'] for r in rows_mod),
            'total_acte': sum(r['total_acte'] or 0 for r in rows_mod),
            'total_paye': sum(r['total_paye'] or 0 for r in rows_mod),
        }

        # Pivot par code réel
        if ctx['group_code_reel']:
            tmp = (qs.select_related('code_acte')
                     .values('code_acte__code_reel')
                     .annotate(
                         count=Count('id'),
                         total_acte=Sum('total_acte'),
                         total_paye=Sum('total_paye')
                     )
                     .order_by('code_acte__code_reel')
                  )
            rows_code = [
                {'code_reel': r['code_acte__code_reel'], **r}
                for r in tmp
            ]
        else:
            rows_code = []
        ctx['pivot_code_reel'] = rows_code
        ctx['totals_code_reel'] = {
            'count': sum(r['count'] for r in rows_code),
            'total_acte': sum(r['total_acte'] or 0 for r in rows_code),
            'total_paye': sum(r['total_paye'] or 0 for r in rows_code),
        }

        # Pivot par lieu d'acte
        if ctx['group_lieu']:
            tmp = (qs.values('lieu_acte')
                     .annotate(
                         count=Count('id'),
                         total_acte=Sum('total_acte'),
                         total_paye=Sum('total_paye')
                     )
                     .order_by('lieu_acte')
                  )
            rows_lieu = [
                {'lieu_acte': r['lieu_acte'], **r}
                for r in tmp
            ]
        else:
            rows_lieu = []
        ctx['pivot_lieu'] = rows_lieu
        ctx['totals_lieu'] = {
            'count': sum(r['count'] for r in rows_lieu),
            'total_acte': sum(r['total_acte'] or 0 for r in rows_lieu),
            'total_paye': sum(r['total_paye'] or 0 for r in rows_lieu),
        }

        return ctx


from django.shortcuts import render, redirect, get_object_or_404
from .models import PrevisionHospitalisation
from .forms import PrevisionHospitalisationForm

from django.utils.timezone import localtime

def prevision_list(request):
    previsions = PrevisionHospitalisation.objects.all().order_by('-date_entree')
    today = localtime().date()

    return render(request, 'comptabilite/prevision_list.html', {
        'previsions': previsions,
        'today': today,
    })


def prevision_create(request):
    form = PrevisionHospitalisationForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('prevision_list')
    return render(request, 'comptabilite/prevision_form.html', {'form': form})

def prevision_detail(request, pk):
    prevision = get_object_or_404(PrevisionHospitalisation, pk=pk)
    return render(request, 'comptabilite/prevision_detail.html', {'prevision': prevision})

from django.conf import settings
from weasyprint import HTML, CSS
import os

def prevision_pdf(request, pk):
    prevision = get_object_or_404(PrevisionHospitalisation, pk=pk)
    template = get_template('comptabilite/prevision_detail.html')
    logo_abspath = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')

    html_content = template.render({
        'prevision': prevision,
        'logo_path': logo_abspath,
    })

    css_path = os.path.join(settings.BASE_DIR, 'static', 'css', 'pdf_styles.css')

    with tempfile.NamedTemporaryFile(delete=True, suffix=".pdf") as output:
        HTML(string=html_content, base_url=request.build_absolute_uri()).write_pdf(
            output.name,
            stylesheets=[CSS(filename=css_path)]
        )
        output.seek(0)
        response = HttpResponse(output.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="prevision_{prevision.pk}.pdf"'
        return response

from django.core.mail import EmailMessage
from django.template.loader import get_template
from weasyprint import HTML, CSS
import tempfile
import os
from django.conf import settings

def prevision_send_email(request, pk):
    prevision = get_object_or_404(PrevisionHospitalisation, pk=pk)

    # chemins vers logo et CSS
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')
    css_path = os.path.join(settings.BASE_DIR, 'static', 'css', 'pdf_styles.css')

    # rendu HTML
    template = get_template('comptabilite/prevision_detail.html')
    html_content = template.render({'prevision': prevision, 'logo_path': logo_path})

    # ✅ destinataires selon le lieu d’hospitalisation
    if prevision.lieu_hospitalisation == "Médecine":
        destinataires = [
            "ejosse@polyclinique-paofai.pf",
            "secretariat@bronstein.fr",
            "medecine@polyclinique-paofai.pf",
            "docteur@bronstein.fr"
        ]
    else:
        destinataires = [
            "anesthesiepaofai@gmail.com",
            "ebarce@polyclinique-paofai.pf",
            "bronstein.tahiti@proton.me",
            "secretariat@bronstein.fr",
            "docteur@bronstein.fr"
        ]

    # génération du PDF
    with tempfile.NamedTemporaryFile(delete=True, suffix=".pdf") as pdf_file:
        HTML(string=html_content, base_url=request.build_absolute_uri()).write_pdf(
            pdf_file.name, stylesheets=[CSS(filename=css_path)]
        )
        pdf_file.seek(0)

        # composition du mail
        email = EmailMessage(
            subject=f"Prévision d’hospitalisation – {prevision.nom} {prevision.prenom} {prevision.date_naissance}",
            body="Bonjour,\n\nVeuillez trouver ci-joint la fiche de prévision d'hospitalisation.\n\nBien cordialement,\nDr. Bronstein",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=destinataires,
        )
        email.attach(f"prevision_{prevision.pk}.pdf", pdf_file.read(), 'application/pdf')
        email.send()

    return redirect('prevision_detail', pk=prevision.pk)


def prevision_update(request, pk):
    prevision = get_object_or_404(PrevisionHospitalisation, pk=pk)
    form = PrevisionHospitalisationForm(request.POST or None, instance=prevision)
    if form.is_valid():
        form.save()
        return redirect('prevision_list')
    return render(request, 'comptabilite/prevision_form.html', {'form': form})

def prevision_delete(request, pk):
    prevision = get_object_or_404(PrevisionHospitalisation, pk=pk)
    if request.method == 'POST':
        prevision.delete()
        return redirect('prevision_list')
    return render(request, 'comptabilite/prevision_confirm_delete.html', {'prevision': prevision})

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from .models import Message
from django.contrib.auth.models import User

@login_required
def chat_view(request, receiver_id):
    receiver = get_object_or_404(User, pk=receiver_id)
    return render(request, 'comptabilite/chat.html', {'receiver': receiver})

@login_required
def get_messages(request):
    receiver_id = request.GET.get('receiver_id')
    messages = Message.objects.filter(
        sender=request.user, receiver_id=receiver_id
    ) | Message.objects.filter(
        sender_id=receiver_id, receiver=request.user
    )
    # ✅ marquer les messages reçus comme lus
    Message.objects.filter(sender_id=receiver_id, receiver=request.user, lu=False).update(lu=True)

    data = [{
        'sender_id': m.sender.id,
        'sender_name': m.sender.get_full_name() or m.sender.username,
        'content': m.content,
        'timestamp': m.timestamp.isoformat(),
        'lu': m.lu
    } for m in messages]

    return JsonResponse({'messages': data})


@login_required
def send_message(request):
    if request.method == 'POST':
        content = request.POST.get('content')
        receiver_id = request.POST.get('receiver_id')
        Message.objects.create(
            sender=request.user,
            receiver_id=receiver_id,
            content=content
        )
        return JsonResponse({'status': 'ok'})

from django.utils import timezone
from django.shortcuts import render
from django.db.models import Q
from .models import PrevisionHospitalisation

@login_required
def patients_hospitalises(request):
    context = get_patients_hospitalises()
    return render(request, "comptabilite/patients_hospitalises.html", context)

from django.template.loader import get_template
from weasyprint import HTML
from django.http import HttpResponse
from django.utils.timezone import now
from django.db.models import Q
from .models import PrevisionHospitalisation
import tempfile

from weasyprint import HTML, CSS
import os

@login_required
def patients_hospitalises_pdf(request):
    context = get_patients_hospitalises()
    context['user'] = request.user

    html_string = render_to_string("comptabilite/patients_hospitalises_pdf.html", context)

    # Chemin absolu du fichier CSS
    css_path = os.path.join(settings.BASE_DIR, 'static', 'css', 'pdf_styles.css')

    pdf = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf(
        stylesheets=[CSS(filename=css_path)]
    )

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="patients_hospitalises.pdf"'
    return response




def get_patients_hospitalises():
    today = now().date()
    qs = PrevisionHospitalisation.objects.filter(
        date_entree__lte=today
    ).filter(
        Q(date_sortie__gte=today) | Q(date_sortie__isnull=True)
    )
    return {
        "today_formatted": today,  # ← on laisse le formatage à Django
        "bloc": qs.filter(lieu_hospitalisation='Bloc'),
        "medecine": qs.filter(lieu_hospitalisation='Médecine'),
        "soins_continus": qs.filter(lieu_hospitalisation='Soins continus'),
    }



import openpyxl
from django.http import HttpResponse

def patients_hospitalises_excel(request):
    today = timezone.localdate()
    hospitalises = PrevisionHospitalisation.objects.filter(
        date_entree__lte=today
    ).filter(Q(date_sortie__gte=today) | Q(date_sortie__isnull=True))

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Patients hospitalisés"

    headers = ['DN', 'Nom', 'Prénom', 'Date Naissance', 'Entrée', 'Sortie Théorique', 'Sortie', 'Lieu']
    ws.append(headers)

    for p in hospitalises:
        sortie_theorique = p.date_sortie or (p.date_entree + timezone.timedelta(days=1))
        ws.append([
            p.dn, p.nom, p.prenom,
            p.date_naissance.strftime('%d/%m/%Y'),
            p.date_entree.strftime('%d/%m/%Y') if p.date_entree else '',
            sortie_theorique.strftime('%d/%m/%Y'),
            p.date_sortie.strftime('%d/%m/%Y') if p.date_sortie else '',
            p.lieu_hospitalisation
        ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=patients_hospitalises_{today}.xlsx'
    wb.save(response)
    return response

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from .models import Facturation
from django.utils.formats import date_format
from django.utils.translation import activate
from reportlab.lib.styles import getSampleStyleSheet
import datetime

def imprimer_fiche_facturation(request, pk):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from decimal import Decimal
    from django.http import HttpResponse
    from django.utils import timezone
    from .models import Facturation
    from django.shortcuts import get_object_or_404

    activate('fr')  # Pour forcer les dates au format français

    facture = get_object_or_404(Facturation, pk=pk)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="facture_{facture.numero_facture or facture.pk}.pdf"'
    c = canvas.Canvas(response, pagesize=A4)
    largeur, hauteur = A4

    today_str = date_format(timezone.localdate(), format='d F Y', use_l10n=True)

    # En-tête
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2 * cm, hauteur - 2 * cm, "Dr. Jean-Ariel BRONSTEIN")
    c.setFont("Helvetica", 12)
    c.drawString(2 * cm, hauteur - 2.7 * cm, "Gastro-entérologue")
    c.drawString(2 * cm, hauteur - 3.4 * cm, "Adresse : Clinique Paofai | Tel : 40.81.48.48")
    c.drawString(2 * cm, hauteur - 4.1 * cm, f"Date : {today_str}")

    # Corps de la facture
    c.setFont("Helvetica", 11)
    y = hauteur - 5.5 * cm
    lignes = [
        f"Facture n° : {facture.numero_facture or 'Non attribué'}",
        f"Patient : {facture.nom} {facture.prenom}",
        f"Date de naissance : {date_format(facture.date_naissance, 'd F Y') if facture.date_naissance else ''}",
        f"DN : {facture.dn}",
        f"Date de l'acte : {date_format(facture.date_acte, 'd F Y') if facture.date_acte else ''}",
        f"Date de la facture : {date_format(facture.date_facture, 'd F Y') if facture.date_facture else ''}",
        f"Code Acte : {facture.code_acte.code_acte if facture.code_acte else ''}",
        f"Montant total : {facture.total_acte} XPF",
        #f"Tiers Payant : {facture.tiers_payant or 0} XPF",
        #f"Total Payé : {facture.total_paye or 0} XPF",
        "",
        f"Payé le : {today_str}",
        "",
        "Signature : Dr. Jean-Ariel Bronstein"
    ]
    for line in lignes:
        c.drawString(2 * cm, y, line)
        y -= 1 * cm

    c.save()
    return response



