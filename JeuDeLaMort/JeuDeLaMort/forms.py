from django import forms
from .models import Candidat, Cercle, Ligue, Ligue_user


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
        model = Cercle
        fields = ['ami_name']


class LigueForm(forms.ModelForm):
    class Meta:
        model = Ligue
        fields = ['nom', 'description', 'public']


class Ligue_userForm(forms.ModelForm):
    class Meta:
        model = Ligue_user
        fields = ['identifiant']
