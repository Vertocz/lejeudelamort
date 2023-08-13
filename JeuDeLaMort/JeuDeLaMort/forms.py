from django import forms
from .models import Candidat, Cercle
from django.contrib.auth.models import User


class ContactUsForm(forms.Form):
    nom = forms.CharField(max_length=200, required=False)
    email = forms.EmailField()
    message = forms.CharField(max_length=1000)


class RechercheCandidatForm(forms.ModelForm):
    class Meta:
        model = Candidat
        fields = ['nom']


class SavePersonneForm(forms.ModelForm):
    class Meta:
        model = Candidat
        fields = '__all__'


class CercleForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username']


