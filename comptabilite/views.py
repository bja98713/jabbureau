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
        facture.numero_facture = now.strftime("FQ/%Y/%m/%d/%H:%M")
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
    if facture.regime_lm:
        c.drawString(7.5 * cm, hauteur - 27.6 * cm, f"{total_paye}")
        c.drawString(11.5 * cm, hauteur - 27.6 * cm, f"{tiers_payant}")

    c.save()
    return response

from datetime import date
from django.shortcuts import render
from django.db.models import Q
from .models import Facturation

from datetime import date
from django.shortcuts import render
from django.db.models import Q
from .models import Facturation

def create_bordereau(request):
    """
    Affiche un aperçu du bordereau sans enregistrer les champs en base.
    Les factures concernées sont celles à tiers_payant > 0 et sans numéro de bordereau.
    """
    # Sélectionner les factures à traiter
    factures = Facturation.objects.filter(tiers_payant__gt=0).filter(
        Q(numero_bordereau__isnull=True) | Q(numero_bordereau="")
    )

    if not factures.exists():
        return render(request, 'comptabilite/bordereau.html', {
            'error': "Aucune facture à traiter pour le bordereau."
        })

    # Génération du numéro de bordereau (aperçu)
    today = date.today()
    year = today.year
    month = today.month
    week = today.isocalendar()[1]
    day_of_year = today.timetuple().tm_yday
    num_bordereau = f"M-{year}-{month:02d}-{week:02d}-{day_of_year:03d}"

    # Calculer les totaux pour l’aperçu
    count = factures.count()
    total_tiers_payant = sum(f.tiers_payant for f in factures)

    # Contexte pour le template (aperçu uniquement, pas de save())
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

from datetime import date
from django.db.models import Q
from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML

from .models import Facturation

def print_bordereau(request, num_bordereau):
    """
    Génère un PDF pour le bordereau.
    Si les factures n'ont pas encore le numéro en base (aperçu),
    on les sélectionne selon les mêmes critères que create_bordereau().
    Puis on enregistre numero_bordereau/date_bordereau et on génère le PDF.
    """
    # 1) Retenter de récupérer celles déjà validées,
    # sinon reprendre la sélection d'aperçu
    factures = Facturation.objects.filter(numero_bordereau=num_bordereau)
    if not factures.exists():
        factures = Facturation.objects.filter(
            tiers_payant__gt=0
        ).filter(
            Q(numero_bordereau__isnull=True) | Q(numero_bordereau="")
        )

    if not factures.exists():
        return HttpResponse("Aucune facture à imprimer pour ce bordereau.", status=404)

    # 2) Validation : on écrit enfin en base
    today = date.today()
    for facture in factures:
        facture.numero_bordereau = num_bordereau
        facture.date_bordereau   = today
        facture.save(update_fields=['numero_bordereau', 'date_bordereau'])

    # 3) Préparation du contexte pour le PDF
    count             = factures.count()
    total_tiers       = sum(f.tiers_payant for f in factures)
    context = {
        'num_bordereau':    num_bordereau,
        'date_bordereau':   today.strftime("%d/%m/%Y"),
        'count':            count,
        'total_tiers_payant': total_tiers,
        'factures':         factures,
    }

    # 4) Rendu du PDF
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
    c.drawString(2*cm, y, "Dr. Florence FOURQUET | Dermatologie | Av. du Prince HINOI | Papeete")
    y -= 1*cm

    y = height - 2*cm
    c.setFont('Helvetica-Bold', 16)
    c.drawString(2*cm, y, "Av. du Prince HINOI | Papeete")
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
            f"FQ/{now.year}/{now.month:02d}/{now.day:02d}/"
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

class ComptabiliteSummaryView(LoginRequiredMixin, ListView):
    login_url = 'login'
    redirect_field_name = 'next'   # paramètre renvoyé après login
    model = Facturation
    template_name = 'comptabilite/comptabilite_summary.html'
    context_object_name = 'summary_rows'
    login_url = 'login'
    redirect_field_name = 'next'

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

        # paramètres de la vue
        ctx['period_choices'] = [
            ('', 'Toutes'),
            ('today', "Aujourd'hui"),
            ('week', 'Cette semaine'),
            ('month', 'Ce mois'),
            ('year', "Cette année"),
        ]
        ctx['period'] = self.request.GET.get('period', '')

        # lire si chaque case est cochée
        ctx['group_regime']      = bool(self.request.GET.get('group_regime'))
        ctx['group_modalite']    = bool(self.request.GET.get('group_modalite'))
        ctx['group_code_reel']   = bool(self.request.GET.get('group_code_reel'))

        # pivot par régime
        if ctx['group_regime']:
            rows = qs.values('regime') \
                     .annotate(count=Count('id'),
                               total_acte=Sum('total_acte'),
                               total_paye=Sum('total_paye'))
        else:
            rows = []
        ctx['pivot_regime'] = rows
        ctx['totals_regime'] = {
            'count': sum(r['count'] for r in rows),
            'total_acte': sum(r['total_acte'] or 0 for r in rows),
            'total_paye': sum(r['total_paye'] or 0 for r in rows),
        }

        # pivot par modalité
        if ctx['group_modalite']:
            tmp = (qs.select_related('paiement')
                     .values('paiement__modalite_paiement')
                     .annotate(count=Count('id'),
                               total_acte=Sum('total_acte'),
                               total_paye=Sum('total_paye'))
                     .order_by('paiement__modalite_paiement'))
            rows = [
                {'label': r['paiement__modalite_paiement'], **r}
                for r in tmp
            ]
        else:
            rows = []
        ctx['pivot_modalite'] = rows
        ctx['totals_modalite'] = {
            'count': sum(r['count'] for r in rows),
            'total_acte': sum(r['total_acte'] or 0 for r in rows),
            'total_paye': sum(r['total_paye'] or 0 for r in rows),
        }

        # pivot par code réel
        if ctx['group_code_reel']:
            tmp = (qs.select_related('code_acte')
                     .values('code_acte__code_reel')
                     .annotate(count=Count('id'),
                               total_acte=Sum('total_acte'),
                               total_paye=Sum('total_paye'))
                     .order_by('code_acte__code_reel'))
            rows = [
                {'code_reel': r['code_acte__code_reel'], **r}
                for r in tmp
            ]
        else:
            rows = []
        ctx['pivot_code_reel'] = rows
        ctx['totals_code_reel'] = {
            'count': sum(r['count'] for r in rows),
            'total_acte': sum(r['total_acte'] or 0 for r in rows),
            'total_paye': sum(r['total_paye'] or 0 for r in rows),
        }

        return ctx










