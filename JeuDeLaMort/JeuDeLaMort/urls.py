from django.urls import path, include
from django.contrib import auth, admin
from .views import index, resume, candidat_create, candidat_detail, candidat_valide, salle_user, \
    classement, favoris, nouvel_ami, recherche_amis, retirer_ami, change_password, maj, parametres, diapo

urlpatterns = [
    path('', index, name="jdm-index"),
    path('resume/', resume, name='resume'),
    path('candidats/<int:id>/', candidat_detail, name='candidat-detail'),
    path('joueurs/<int:id>/', salle_user, name="salle-user"),
    path('joueurs/add/', candidat_create, name='candidat-create'),
    path('joueurs/add/<str:qqn>/', candidat_valide, name='candidat-valide'),
    path('members/', include('django.contrib.auth.urls')),
    path('members/', include('members.urls')),
    path('favoris/', favoris, name='favoris'),
    path('classement/', classement, name='classement'),
    path('recherche/', recherche_amis, name='recherche-amis'),
    path('nouvel_ami/<int:id>', nouvel_ami, name='nouvel-ami'),
    path('admin/', admin.site.urls),
    path('retirer/<int:id>', retirer_ami, name='retirer-ami'),
    path('maj/', maj, name='maj'),
    path('change_password/', change_password, name='change-password'),
    path('parametres/', parametres, name='parametres'),
    path('diapo/', diapo, name='diapo'),
]