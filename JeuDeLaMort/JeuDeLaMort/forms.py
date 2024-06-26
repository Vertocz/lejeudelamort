from django import forms
from .models import Candidat, Preference, Prout
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


class PreferenceForm(forms.ModelForm):
    class Meta:
        model = Preference
        fields = ['newsletter', 'infos']


class UpdateUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email')


class ProutForm(forms.ModelForm):
    class Meta:
        model = Prout
        fields = '__all__'

