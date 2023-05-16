from django.contrib import admin
from .models import Candidat, Pari, Cercle, Ligue, Ligue_user


class CandidatAdmin(admin.ModelAdmin):
    list_display = ('nom', 'DDN', 'DDD')


class PariAdmin(admin.ModelAdmin):
    list_display = ('username', 'candidat_nom')


class RechercheAdmin(admin.ModelAdmin):
    list_display = ('nom', 'DDN', 'description')


class CercleAdmin(admin.ModelAdmin):
    list_display = ('username', 'ami_name')


class LigueAdmin(admin.ModelAdmin):
    list_display = ('nom', 'description', 'lancee')


class Ligue_userAdmin(admin.ModelAdmin):
    list_display = ('ligue', 'user_id')

admin.site.register(Candidat, CandidatAdmin)
admin.site.register(Pari, PariAdmin)
admin.site.register(Cercle, CercleAdmin)
admin.site.register(Ligue, LigueAdmin)
admin.site.register(Ligue_user, Ligue_userAdmin)
