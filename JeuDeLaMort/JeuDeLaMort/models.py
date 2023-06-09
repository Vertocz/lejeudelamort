from django.contrib.auth.models import User
from django.db import models
import math
from datetime import datetime


class Candidat(models.Model):
    nom = models.CharField(max_length=200, null=True)
    DDN = models.DateField('Date de Naissance', default='1900-10-10')
    DDD = models.DateField('Date de Décès', null=True, blank=True)
    wiki_id = models.CharField(max_length=20, null=False)
    description = models.CharField(max_length=500, null=True, blank=True)
    photo = models.CharField(max_length=500, null=True, blank=True)

    def calcul_age(self):
        if self.DDD:
            age = math.floor((self.DDD - self.DDN).days / 365)
        else:
            age = math.floor((datetime.today().date() - self.DDN).days / 365)
        return age

    def points(self):
        scores = ((0, 55, 10), (55, 65, 9), (65, 75, 8), (75, 80, 7), (80, 85, 5), (85, 90, 3), (90, 2000, 1))
        for x in scores:
            if x[0] < self.calcul_age() <= x[1]:
                points = x[2]
                return points

    def __str__(self):
        return f'{self.nom}'

    class Meta:
        ordering = ['DDN']


class Pari(models.Model):
    wiki_id = models.CharField(max_length=20, null=True)
    user_id = models.IntegerField()
    candidat_nom = models.CharField(max_length=250, null=True)
    username = models.CharField(max_length=250, null=True)
    mort = models.BooleanField(default=False)


class Cercle(models.Model):
    username = models.CharField(max_length=250, null=True)
    ami_name = models.CharField(verbose_name='', max_length=250, null=True)
    user_id = models.IntegerField()
    ami_id = models.IntegerField()


class Ligue(models.Model):
    nom = models.CharField(max_length=60, null=False)
    description = models.CharField(max_length=250, null=True)
    lancee = models.BooleanField(default=False)
    public = models.BooleanField(verbose_name='Ce cercle est public', default=False)
    createur = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return f'{self.nom}'


class Ligue_user(models.Model):
    ligue = models.ForeignKey(Ligue, on_delete=models.CASCADE, null=False)
    user_id = models.IntegerField()
    identifiant = models.IntegerField(verbose_name='', null=True)

    def compteur(self):
        compteur = 0
        for pari in Pari_unique.objects.filter(ligue=self.ligue, user_id=self.user_id):
            if pari.mort is False:
                compteur += 1
        return compteur

    def continuer(self):
        continuer = False
        if len(Pari_unique.objects.filter(ligue=self.ligue, user_id=self.user_id)) < 10:
            continuer = True
        return continuer

    def tour(self):
        tour = False
        if self.continuer():
            compteur_max = 0
            for ligue_user in Ligue_user.objects.filter(ligue=self.ligue):
                compteur_user = ligue_user.compteur()
                if compteur_user > compteur_max and ligue_user.user_id != self.user_id :
                    compteur_max = compteur_user
            if self.compteur() <= compteur_max:
                tour = True
        return tour


class Pari_unique(models.Model):
    ligue = models.ForeignKey(Ligue, on_delete=models.CASCADE, null=False)
    wiki_id = models.CharField(max_length=20, null=True)
    user_id = models.IntegerField()
    mort = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.wiki_id}'
