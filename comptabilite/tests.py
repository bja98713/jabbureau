from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .forms import BibliographieForm, FacturationForm
from .models import ActiviteFacturation, Bibliographie, Facturation, ParametrageFacturation
from .views import _activite_annuelle_context, _dashboard_context


class BibliographieFormTest(TestCase):
	def test_codes_are_normalized(self):
		form = BibliographieForm(data={
			'titre': 'Test fiche',
			'reference': 'Réf. 123',
			'resume': 'Texte bref',
			'texte': 'Texte complet',
			'lien': '',
			'codes_cim10': ' a01 ; B02  b02 '}
		)
		self.assertTrue(form.is_valid())
		self.assertEqual(form.cleaned_data['codes_cim10'], 'A01, B02')


class FacturationFormTest(TestCase):
	def test_numero_facture_is_prefilled_from_counter(self):
		ParametrageFacturation.objects.create(prochain_numero=42)

		form = FacturationForm()

		self.assertEqual(form.fields['numero_facture'].initial, '42')

	def test_prefilled_numero_advances_counter_on_create(self):
		ParametrageFacturation.objects.create(prochain_numero=42)
		form = FacturationForm(data={
			'dn': '1234567',
			'nom': 'Dupont',
			'prenom': 'Jean',
			'date_naissance': '1980-01-01',
			'date_acte': '2026-06-22',
			'date_facture': '2026-06-22',
			'regime': 'Sécurité Sociale',
			'droit_ouvert': '',
			'regime_tp': '',
			'regime_lm': '',
			'lieu_acte': 'Cabinet',
			'numero_facture': '42',
			'statut_dossier': 'RAS',
			'modalite_paiement': '',
		})

		self.assertTrue(form.is_valid(), form.errors)
		facture = form.save()

		self.assertEqual(facture.numero_facture, '42')
		self.assertEqual(ParametrageFacturation.objects.get().prochain_numero, 43)
		self.assertTrue(Facturation.objects.filter(numero_facture='42').exists())


class BibliographieListViewTest(TestCase):
	def setUp(self):
		user_model = get_user_model()
		self.user = user_model.objects.create_user(username='tester', password='pass1234')
		Bibliographie.objects.create(
			titre='Maladie de Crohn',
			reference='Lancer et al.',
			resume='Résumé crohn',
			texte='Texte',
			codes_cim10='K50, K51'
		)
		Bibliographie.objects.create(
			titre='RGO',
			reference='Dupont',
			resume='Résumé rgo',
			texte='Texte',
			codes_cim10='K21'
		)

	def test_requires_authentication(self):
		response = self.client.get(reverse('bibliographie_list'))
		self.assertEqual(response.status_code, 302)
		self.assertIn('/accounts/login/', response['Location'])

	def test_search_by_code_is_case_insensitive(self):
		self.client.login(username='tester', password='pass1234')
		response = self.client.get(reverse('bibliographie_list'), {'q': 'k50'})
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Maladie de Crohn')
		self.assertNotContains(response, 'RGO')


class DashboardContextTest(TestCase):
	def test_activity_volume_is_graduated_from_zero_to_500000_xpf(self):
		today = timezone.localdate()
		first_day = today.replace(day=1)
		second_day = first_day.replace(day=2)

		Facturation.objects.create(
			dn='1234567',
			nom='Dupont',
			prenom='Jean',
			date_naissance='1980-01-01',
			date_acte=first_day,
			date_facture=first_day,
			regime='Sécurité Sociale',
			lieu_acte='Cabinet',
			total_acte=125000,
			statut_dossier='RAS',
		)
		Facturation.objects.create(
			dn='7654321',
			nom='Martin',
			prenom='Anne',
			date_naissance='1981-01-01',
			date_acte=first_day,
			date_facture=first_day,
			regime='Sécurité Sociale',
			lieu_acte='Cabinet',
			total_acte=125000,
			statut_dossier='RAS',
		)
		Facturation.objects.create(
			dn='2222222',
			nom='Durand',
			prenom='Paul',
			date_naissance='1982-01-01',
			date_acte=second_day,
			date_facture=second_day,
			regime='Sécurité Sociale',
			lieu_acte='Cabinet',
			total_acte=600000,
			statut_dossier='RAS',
		)

		context = _dashboard_context()
		activity_by_day = {
			row['date'].day: row
			for row in context['activite_mois']
		}

		self.assertEqual(activity_by_day[1]['nb'], 2)
		self.assertEqual(activity_by_day[1]['total'], 250000)
		self.assertEqual(activity_by_day[1]['volume_montant_pct'], 50)
		self.assertEqual(activity_by_day[2]['nb'], 1)
		self.assertEqual(activity_by_day[2]['total'], 600000)
		self.assertEqual(activity_by_day[2]['volume_montant_pct'], 100)

	def test_pending_bordereaux_count_and_amount_use_bordereau_scope(self):
		today = timezone.localdate()

		Facturation.objects.create(
			dn='1234567',
			nom='Dupont',
			prenom='Jean',
			date_naissance='1980-01-01',
			date_acte=today,
			date_facture=today,
			regime='Sécurité Sociale',
			lieu_acte='Cabinet',
			total_acte=100000,
			tiers_payant=40000,
			statut_dossier='RAS',
		)
		Facturation.objects.create(
			dn='7654321',
			nom='Martin',
			prenom='Anne',
			date_naissance='1981-01-01',
			date_acte=today,
			date_facture=today,
			regime='Sécurité Sociale',
			lieu_acte='Cabinet',
			total_acte=200000,
			tiers_payant=60000,
			statut_dossier='RAS',
		)
		Facturation.objects.create(
			dn='2222222',
			nom='Durand',
			prenom='Paul',
			date_naissance='1982-01-01',
			date_acte=today,
			date_facture=today,
			regime='Sécurité Sociale',
			lieu_acte='Cabinet',
			total_acte=300000,
			tiers_payant=90000,
			statut_dossier='RAS',
			numero_bordereau='M2026-06-01-001',
		)
		Facturation.objects.create(
			dn='3333333',
			nom='Bernard',
			prenom='Luc',
			date_naissance='1983-01-01',
			date_acte=today,
			date_facture=today,
			regime='Sécurité Sociale',
			lieu_acte='Cabinet',
			total_acte=400000,
			tiers_payant=100000,
			statut_dossier='Impayé',
		)

		context = _dashboard_context()

		self.assertEqual(context['bordereaux_attente'], 2)
		self.assertEqual(context['montant_bordereaux_attente'], 100000)

	def test_annual_activity_chart_uses_activity_table_monthly_average(self):
		ActiviteFacturation.objects.create(date_acte=date(2005, 1, 10), total_acte=900000)
		ActiviteFacturation.objects.create(date_acte=date(2024, 1, 10), total_acte=900000)
		ActiviteFacturation.objects.create(date_acte=date(2024, 1, 10), total_acte=100000)
		ActiviteFacturation.objects.create(date_acte=date(2024, 2, 10), total_acte=200000)
		ActiviteFacturation.objects.create(date_acte=date(2026, 1, 10), total_acte=3432813)
		ActiviteFacturation.objects.create(date_acte=date(2026, 2, 10), total_acte=4997587)
		ActiviteFacturation.objects.create(date_acte=date(2026, 3, 10), total_acte=4533897)
		ActiviteFacturation.objects.create(date_acte=date(2026, 4, 10), total_acte=4721877)

		context = _activite_annuelle_context(date(2026, 4, 15))
		rows = {row['label']: row for row in context['activite_annuelle_rows']}

		self.assertEqual(context['activite_annees_representees'], 3)
		self.assertEqual(context['activite_annees_reference'], [2024, 2025])
		self.assertEqual(context['activite_annees_exclues'], [])
		self.assertEqual(context['activite_mois_exclus'], [])
		self.assertEqual(rows['Jan']['moyenne'], 2365967)
		jan_seuils = {seuil['label']: seuil['value'] for seuil in rows['Jan']['seuils']}
		self.assertEqual(jan_seuils['+10%'], 2602564)
		self.assertEqual(jan_seuils['+20%'], 2839160)
		self.assertEqual(jan_seuils['+30%'], 3075757)
		self.assertEqual(jan_seuils['+40%'], 3312354)
		self.assertEqual(jan_seuils['-10%'], 2129370)
		self.assertEqual(jan_seuils['-20%'], 1892774)
		self.assertEqual(jan_seuils['-30%'], 1656177)
		self.assertEqual(jan_seuils['-40%'], 1419580)
		self.assertEqual(rows['Jan']['moyenne_mensuelle'], 2365967)
		self.assertEqual(rows['Jan']['annees_actives'], 3)
		self.assertEqual(rows['Jan']['annee'], 3432813)
		self.assertEqual(rows['Jan']['ecart_pct'], 45.1)
		self.assertTrue(rows['Jan']['ecart_positive'])
		self.assertEqual(rows['Fev']['moyenne'], 6630173)
		self.assertEqual(rows['Fev']['moyenne_mensuelle'], 4264206)
		self.assertEqual(rows['Fev']['annees_actives'], 3)
		self.assertEqual(rows['Fev']['annee'], 8430400)
		self.assertEqual(rows['Fev']['ecart_pct'], 27.2)
		self.assertEqual(rows['Fev']['ecart_label'], '+27.2%')
		self.assertTrue(rows['Fev']['ecart_positive'])
		self.assertEqual(rows['Mar']['moyenne'], 9631428)
		self.assertEqual(rows['Mar']['moyenne_mensuelle'], 3001255)
		self.assertEqual(rows['Mar']['annees_actives'], 3)
		self.assertEqual(rows['Mar']['annee'], 12964297)
		self.assertEqual(rows['Mar']['ecart_pct'], 34.6)
		self.assertTrue(rows['Mar']['ecart_positive'])
		self.assertEqual(rows['Avr']['moyenne'], 13269578)
		self.assertEqual(rows['Avr']['moyenne_mensuelle'], 3638150)
		self.assertEqual(rows['Avr']['annees_actives'], 3)
		self.assertEqual(rows['Avr']['annee'], 17686174)
		self.assertEqual(rows['Avr']['ecart_pct'], 33.3)
		self.assertTrue(rows['Avr']['ecart_positive'])
		self.assertTrue(rows['Avr']['current_visible'])
		self.assertFalse(rows['Mai']['current_visible'])
		self.assertEqual(
			[seuil['label'] for seuil in context['activite_annuelle_seuils']],
			['+10%', '+20%', '+30%', '+40%', '-10%', '-20%', '-30%', '-40%']
		)
		self.assertTrue(all(seuil['points'] for seuil in context['activite_annuelle_seuils']))

	def test_activity_table_mirrors_facturation_date_and_total_only(self):
		first_day = date(2026, 1, 10)
		second_day = date(2026, 2, 10)
		facture = Facturation.objects.create(
			dn='1234567',
			nom='Dupont',
			prenom='Jean',
			date_naissance='1980-01-01',
			date_acte=first_day,
			date_facture=first_day,
			regime='Sécurité Sociale',
			lieu_acte='Cabinet',
			total_acte=100000,
			statut_dossier='RAS',
		)
		Facturation.objects.create(
			dn='7654321',
			nom='Martin',
			prenom='Anne',
			date_naissance='1981-01-01',
			date_acte=first_day,
			date_facture=first_day,
			regime='Sécurité Sociale',
			lieu_acte='Cabinet',
			total_acte=50000,
			statut_dossier='RAS',
		)

		self.assertEqual(ActiviteFacturation.objects.filter(date_acte=first_day).count(), 2)
		self.assertEqual(
			sum(row.total_acte for row in ActiviteFacturation.objects.filter(date_acte=first_day)),
			150000
		)

		facture.date_acte = second_day
		facture.date_facture = second_day
		facture.total_acte = 200000
		facture.save()

		self.assertEqual(ActiviteFacturation.objects.filter(date_acte=first_day).count(), 1)
		self.assertEqual(ActiviteFacturation.objects.get(date_acte=first_day).total_acte, 50000)
		self.assertEqual(ActiviteFacturation.objects.filter(date_acte=second_day).count(), 1)
		self.assertEqual(ActiviteFacturation.objects.get(date_acte=second_day).total_acte, 200000)

		facture.delete()

		self.assertFalse(ActiviteFacturation.objects.filter(date_acte=second_day).exists())
