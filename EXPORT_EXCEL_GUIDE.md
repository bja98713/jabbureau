# Fonctionnalité d'Export Excel - Guide d'utilisation

## 📊 Description
Nouvelle fonctionnalité permettant d'exporter toutes les données de facturation au format Excel avec les colonnes souhaitées.

## 🎯 Colonnes exportées

### Export Standard (`export_all_data_excel`)
- **date** : Date de l'acte (format DD/MM/YYYY)
- **nom** : Nom complet du patient (Nom + Prénom)  
- **total** : Montant total de l'acte (formaté en XPF)
- **lieu** : Lieu de l'acte (Cabinet/Clinique)
- **mois** : Numéro du mois (1-12)
- **annee** : Année de l'acte
- **code_reel** : Code réel provenant du référentiel des actes

### Export Filtré (`export_filtered_data_excel`)
- Même structure de colonnes que l'export standard

## 🚀 Comment utiliser

### 1. Export Rapide (toutes les données)
- Aller sur la page de liste des facturations : `/`
- Cliquer sur le bouton **"Export Rapide"**
- Le fichier `facturation_complete_YYYYMMDD.xlsx` se télécharge automatiquement

### 2. Export avec Options de Filtrage
- Aller sur la page de liste des facturations : `/`  
- Cliquer sur le bouton **"Export Excel"**
- Choisir les filtres souhaités :
  - **Date de début** : Filtrer à partir de cette date
  - **Date de fin** : Filtrer jusqu'à cette date  
  - **Lieu** : Filtrer par Cabinet ou Clinique
- Cliquer sur **"Exporter avec Filtres"**

### 3. URLs disponibles
- Export complet : `/export/excel/`
- Export filtré : `/export/excel/filtered/?date_debut=2025-01-01&date_fin=2025-12-31&lieu=Cabinet`
- Page d'options : `/export/`

## 📋 Fonctionnalités techniques

### Formatage Excel
- **En-têtes stylisés** : Police blanche sur fond bleu
- **Colonnes ajustées** : Largeur optimisée pour la lisibilité
- **Format monétaire** : Totaux affichés avec "XPF"
- **Tri des données** : Par date décroissante (plus récent en premier)

### Noms de fichiers générés
- Export complet : `facturation_complete_20251026.xlsx`
- Export filtré avec dates : `facturation_2025-01-01_to_2025-12-31_20251026.xlsx`
- Export filtré par lieu : `facturation_cabinet_20251026.xlsx`

## 🔧 Fonctions développées

### Dans `comptabilite/views.py`
```python
@login_required
def export_all_data_excel(request):
    """Export de toutes les données sans filtre"""
    
@login_required  
def export_filtered_data_excel(request):
    """Export avec filtres optionnels (date_debut, date_fin, lieu)"""
    
@login_required
def export_excel_page(request):
    """Page d'interface pour choisir les options d'export"""
```

### Templates ajoutés
- `comptabilite/templates/comptabilite/export_excel.html` : Page d'options d'export

### URLs ajoutées
```python
path('export/excel/', views.export_all_data_excel, name='export_all_data_excel'),
path('export/excel/filtered/', views.export_filtered_data_excel, name='export_filtered_data_excel'), 
path('export/', views.export_excel_page, name='export_excel_page'),
```

## ✅ Tests effectués
- ✅ Création de données de test (3 facturations)
- ✅ Export Excel avec formatage correct
- ✅ Gestion des dates et totaux
- ✅ Filtrage par date et lieu
- ✅ Interface utilisateur fonctionnelle
- ✅ Serveur Django opérationnel

## 📝 Exemple d'utilisation
1. Créer quelques facturations via l'interface web
2. Aller à l'URL `/export/` 
3. Choisir "Export Complet" ou configurer des filtres
4. Le fichier Excel se télécharge automatiquement
5. Ouvrir dans Excel/LibreOffice pour visualiser les données

## 🎉 Résultat
Un fichier Excel professionnel avec toutes vos données de facturation, prêt pour l'analyse ou l'archivage !