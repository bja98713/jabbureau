from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .forms import BibliographieForm, FacturationForm
from .models import Bibliographie, Facturation, ParametrageFacturation
from .views import _dashboard_context


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
