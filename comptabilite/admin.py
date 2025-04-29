from django.contrib import admin
from .models import Code, Medecin

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
