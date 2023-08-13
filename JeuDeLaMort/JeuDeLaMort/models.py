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
    candidat = models.ForeignKey(Candidat, on_delete=models.CASCADE, null=True)
    joueur = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    mort = models.BooleanField(default=False)


class Cercle(models.Model):
    joueur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='joueur', null=True)
    ami = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ami', null=True)
