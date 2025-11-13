from django.contrib import admin
from .models import BiopsyReminder, CourrierPhoto, Bibliographie, CorrespondantEmail


@admin.register(BiopsyReminder)
class BiopsyReminderAdmin(admin.ModelAdmin):
    list_display = ("dn", "nom", "prenom", "type_examen", "destination", "exam_date", "send_on", "sent")
    list_filter = ("type_examen", "destination", "sent", "send_on")
    search_fields = ("dn", "nom", "prenom")
@admin.register(CourrierPhoto)
class CourrierPhotoAdmin(admin.ModelAdmin):
    list_display = ("id", "courrier", "position", "uploaded_at")
    list_filter = ("position", "uploaded_at")
    search_fields = ("courrier__dn", "courrier__nom", "courrier__prenom")


@admin.register(Bibliographie)
class BibliographieAdmin(admin.ModelAdmin):
    list_display = ("titre", "reference", "codes_cim10", "updated_at")
    search_fields = ("titre", "reference", "codes_cim10")
    list_filter = ("updated_at",)


@admin.register(CorrespondantEmail)
class CorrespondantEmailAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "updated_at")
    search_fields = ("name", "email", "notes")
    list_filter = ("updated_at",)
    ordering = ("name",)
from .models import Code, Medecin, Message, Patient
from .models import ParametrageFacturation

@admin.register(Code)
class CodeAdmin(admin.ModelAdmin):
    # On récupère tous les champs non-relationnels sauf la PK, puis on trie par ordre alphabétique
    field_names = sorted(
        f.name for f in Code._meta.get_fields()
        if not (
            f.many_to_many or       # pas de M2M
            f.one_to_many or         # pas de reverse FK
            f.primary_key            # on exclut la PK (id)
        )
    )

    list_display  = field_names
    fields        = field_names
    ordering      = field_names
    search_fields = ('code_acte', 'code_acte_normal', 'code_reel')


@admin.register(Medecin)
class MedecinAdmin(admin.ModelAdmin):
    list_display  = ('nom_medecin', 'code_m', 'nom_clinique')
    search_fields = ('nom_medecin', 'code_m', 'nom_clinique')

from .models import ParametrageFacturation

@admin.register(ParametrageFacturation)
class ParametrageFacturationAdmin(admin.ModelAdmin):
    list_display = ('prochain_numero',)
    
admin.site.register(Message)


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("dn", "nom", "prenom", "date_naissance", "created_at")
    search_fields = ("dn", "nom", "prenom")
    list_filter = ("date_naissance",)
    ordering = ("nom", "prenom")
