from django.contrib import admin
from .models import Candidat, Pari, Cercle, Preference


class CandidatAdmin(admin.ModelAdmin):
    list_display = ('nom', 'DDN', 'DDD')


class PariAdmin(admin.ModelAdmin):
    list_display = ('joueur', 'candidat')


class RechercheAdmin(admin.ModelAdmin):
    list_display = ('nom', 'DDN', 'description')


class CercleAdmin(admin.ModelAdmin):
    list_display = ('joueur', 'ami')


class PreferenceAdmin(admin.ModelAdmin):
    list_display = ('joueur', 'newsletter', 'infos')


admin.site.register(Candidat, CandidatAdmin)
admin.site.register(Pari, PariAdmin)
admin.site.register(Cercle, CercleAdmin)
admin.site.register(Preference, PreferenceAdmin)
