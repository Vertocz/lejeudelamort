from django.contrib import admin
from .models import *


class CandidatAdmin(admin.ModelAdmin):
    list_display = ('nom', 'DDN', 'DDD')


class PariAdmin(admin.ModelAdmin):
    list_display = ('joueur', 'candidat', 'mort')


class RechercheAdmin(admin.ModelAdmin):
    list_display = ('nom', 'DDN', 'description')


class CercleAdmin(admin.ModelAdmin):
    list_display = ('joueur', 'ami')


class PreferenceAdmin(admin.ModelAdmin):
    list_display = ('joueur', 'newsletter', 'infos')


class HistoriqueAdmin(admin.ModelAdmin):
    list_display = ('joueur', 'saison', 'score')


class ProutAdmin(admin.ModelAdmin):
    list_display = ('auteur', 'performance')


admin.site.register(Candidat, CandidatAdmin)
admin.site.register(Pari, PariAdmin)
admin.site.register(Cercle, CercleAdmin)
admin.site.register(Preference, PreferenceAdmin)
admin.site.register(Historique, HistoriqueAdmin)
admin.site.register(Prout, ProutAdmin)
