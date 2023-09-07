import time

from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect
from datetime import datetime, date
from .models import Candidat, Pari, Cercle, Preference
from django.contrib.auth.models import User
from .forms import RechercheCandidatForm, PreferenceForm
from django.contrib import messages
import requests

candidats = Candidat.objects.all()
users = User.objects.all()
paris = Pari.objects.all()
cercles = Cercle.objects.all()
URL = "https://www.wikidata.org/w/api.php"


def index(request):
    return render(request, "jdm/index.html")


def score_max(joueur):
    paris = Pari.objects.filter(joueur=joueur, mort=False)
    score = 0
    for pari in paris:
        try:
            candidat = pari.candidat
            points = candidat.points()
            score += points
        except ObjectDoesNotExist:
            pass
    return score


def score_user(paris_user):
    score = 0
    for pari in paris_user:
        try:
            candidat = pari.candidat
            if candidat.DDD:
                points = candidat.points()
                score += points
        except ObjectDoesNotExist:
            pass
    return score


def joker(joueur):
    paris_joueur = Pari.objects.filter(joueur=joueur)
    record = date.fromisoformat("1900-01-01")
    if len(paris_joueur) > 0:
        recordman = paris_joueur[0]
        for pari in paris_joueur:
            try:
                candidat = pari.candidat
                if candidat.DDN > record:
                    record = candidat.DDN
                    recordman = candidat
            except ObjectDoesNotExist:
                pass
        return recordman
    else:
        pass


def moyenne_age(joueur):
    paris_user = Pari.objects.filter(joueur=joueur)
    total_age = 0
    if len(paris_user) > 0:
        for pari in paris_user:
            try:
                age = pari.candidat.calcul_age()
                total_age += age
            except ObjectDoesNotExist:
                pass
        moyenne = round(total_age / len(paris_user))
        return moyenne
    else:
        pass


def salle_user(request, id):
    try:
        joueur = User.objects.get(id=id)
        if len(Cercle.objects.filter(joueur=request.user, ami=joueur)) > 0 or request.user == joueur:
            paris_user = Pari.objects.filter(joueur=joueur)
            paris_decedes = Pari.objects.filter(joueur=joueur, mort=True)
            candidats_joueur = []
            for pari in paris_user:
                candidat = candidats.get(wiki_id=pari.candidat.wiki_id)
                candidats_joueur.append(candidat)
            return render(request,
                          'jdm/salle_user.html',
                          {'joueur': joueur, 'poker': joker(joueur), 'score_max': score_max(joueur),
                           'score': score_user(paris_user), 'paris': Pari.objects.filter(joueur=joueur), 'deces': paris_decedes,
                           'rap': 10 - len(paris_user) + len(paris_decedes), 'candidats_joueur': candidats_joueur,
                           'moyenne': moyenne_age(joueur)})
        else:
            messages.success(request, ("Ce joueur ne fait pas partie de votre cercle"))
            return redirect('classement')
    except ObjectDoesNotExist:
        messages.success(request, ("Ce joueur ne fait pas partie de votre cercle"))
        return redirect('classement')


def recherche_amis(request):
    if request.method == 'POST':
        your_name = request.POST['your_name']
        amis_potentiels = User.objects.filter(username__iexact=your_name)
        return render(request, 'jdm/recherche_amis.html', {'liste': amis_potentiels})
    else:
        classement(request)


def classement(request):
    liste = liste_amis(request.user)
    return render(request, 'jdm/classement.html', {'liste': liste[0], 'en_devenir': liste[1]})


def liste_amis(joueur):
    liste = []
    for user in users:
        if len(Cercle.objects.filter(joueur=joueur, ami=user)) == 0 and score_user(Pari.objects.filter(joueur=user)) == 0 and user != joueur:
            pass
        else:
            if len(Cercle.objects.filter(joueur=joueur, ami=user)) != 0:
                est_un_ami = True
            else:
                est_un_ami = False
            paris_user = Pari.objects.filter(joueur=user)
            nominations = len(paris_user)
            score_user_x = score_user(paris_user)
            succes = 0
            for pari in Pari.objects.filter(joueur=user):
                if pari.mort:
                    succes += 1
            liste.append((user, est_un_ami, score_user_x, nominations, succes))
    liste.sort(key=lambda x: x[3], reverse=True)
    liste.sort(key=lambda x: x[2], reverse=True)

    cercles_pas_encore_amis = Cercle.objects.filter(ami=joueur)
    amis_en_devenir = []
    for cercle in cercles_pas_encore_amis:
        if len(Cercle.objects.filter(joueur=joueur, ami=cercle.joueur)) < 1:
            amis_en_devenir.append(cercle.joueur)

    return liste, amis_en_devenir


def nouvel_ami(request, id):
    ami = User.objects.get(id=id)
    liste = liste_amis(request.user.id)[0]
    if Cercle.objects.filter(ami=ami, joueur=request.user):
        messages.success(request, (str(User.objects.get(id=id).username) + " est déjà dans votre cercle"))
        return render(request, 'jdm/classement.html', {'liste': liste})
    if id == request.user.id:
        messages.success(request, ("Vous voudriez vraiment être ami.e avec vous-même ?"))
        return render(request, 'jdm/classement.html', {'liste': liste})
    else:
        Cercle(ami=ami, joueur=request.user).save()
        return render(request, 'jdm/nouvel_ami.html', {'ami': ami})


def retirer_ami(request, id):
    Cercle.objects.get(ami=User.objects.get(id=id), joueur=request.user.id).delete()
    messages.success(request, (str(User.objects.get(id=id).username)+" a été retiré.e de votre cercle"))
    return redirect('classement')


def recherche_candidat(nom):
    PARAMS = {"action": "wbsearchentities", "language": "fr", "uselang": "fr", "format": "json", "search": nom}
    response = requests.get(URL, PARAMS)
    jsonresponse = response.json()
    candidats_potentiels = []
    if len(jsonresponse["search"]) > 0:
        for i in range(0, len(jsonresponse["search"])):
            qqn = jsonresponse["search"][i]["id"]
            PARAMS_recherche = {"action": "wbgetclaims", "entity": qqn, "props": "value", "format": "json"}
            jsonresponse_recherche = requests.get(URL, PARAMS_recherche).json()
            candidat = jsonresponse["search"][i]["display"]["label"]["value"]

            # Verification que les candidats soient vivants
            if "P569" in jsonresponse_recherche["claims"] and "P570" not in jsonresponse_recherche["claims"]:
                try:
                    DDN = datetime.strptime(
                        jsonresponse_recherche["claims"]["P569"][0]["mainsnak"]["datavalue"]["value"]["time"],
                        '+%Y-%m-%dT%H:%M:%SZ').date()
                except ValueError:
                    DDN = datetime.today().date()
                wiki_id = jsonresponse["search"][i]["id"]
                try:
                    photo = jsonresponse_recherche["claims"]["P18"][0]["mainsnak"]["datavalue"]["value"].replace(
                        " ", "_")
                except KeyError:
                    photo = ''
                try:
                    description = jsonresponse["search"][i]["description"]
                except KeyError:
                    description = ''
                if Candidat.objects.filter(nom=candidat, DDN=DDN, wiki_id=wiki_id, description=description,
                                           photo=photo):
                    new_candidat = Candidat.objects.get(wiki_id=wiki_id)
                else:
                    new_candidat = Candidat(nom=candidat, DDN=DDN, wiki_id=wiki_id, description=description,
                                            photo=photo)
                    new_candidat.save()
                candidats_potentiels.append(new_candidat)
    return candidats_potentiels


def candidat_create(request):
    if request.method == 'POST':
        form = RechercheCandidatForm(request.POST)
        nom = form.data['nom']
        PARAMS = {"action": "wbsearchentities", "language": "fr", "uselang": "fr", "format": "json", "search": nom}
        response = requests.get(URL, PARAMS)
        jsonresponse = response.json()
        candidats_potentiels = []

        if len(jsonresponse["search"]) > 0:
            for i in range(0, len(jsonresponse["search"])):
                qqn = jsonresponse["search"][i]["id"]
                PARAMS_recherche = {"action": "wbgetclaims", "entity": qqn, "props": "value", "format": "json"}
                jsonresponse_recherche = requests.get(URL, PARAMS_recherche).json()
                candidat = jsonresponse["search"][i]["display"]["label"]["value"]

                # Verification que les candidats soient vivants
                if "P569" in jsonresponse_recherche["claims"] and "P570" not in jsonresponse_recherche["claims"]:
                    try:
                        DDN = datetime.strptime(
                            jsonresponse_recherche["claims"]["P569"][0]["mainsnak"]["datavalue"]["value"]["time"],
                            '+%Y-%m-%dT%H:%M:%SZ').date()
                    except ValueError:
                        DDN = datetime.today().date()
                    wiki_id = jsonresponse["search"][i]["id"]
                    try:
                        photo = jsonresponse_recherche["claims"]["P18"][0]["mainsnak"]["datavalue"]["value"].replace(
                            " ", "_")
                    except KeyError:
                        photo = ''
                    try:
                        description = jsonresponse["search"][i]["description"]
                    except KeyError:
                        description = ''
                    if Candidat.objects.filter(wiki_id=wiki_id):
                        new_candidat = Candidat.objects.get(wiki_id=wiki_id)
                    else:
                        new_candidat = Candidat(nom=candidat, DDN=DDN, wiki_id=wiki_id, description=description,
                                                photo=photo)
                        new_candidat.save()
                    candidats_potentiels.append(new_candidat)

            if len(candidats_potentiels) >= 1:
                amis = Cercle.objects.filter(joueur=request.user)
                paris_amis = []
                for candidat_potentiel in candidats_potentiels:
                    for pari in paris:
                        if pari.candidat == candidat_potentiel:
                            for ami in amis:
                                if ami.ami == pari.joueur:
                                    paris_amis.append((candidat_potentiel, ami.ami))
                return render(request, 'jdm/candidat_choix.html',
                              context={"recherche": candidats_potentiels, "paris": paris, "paris_amis": paris_amis,
                                       "users": User.objects.all()})

            if len(candidats_potentiels) == 0:
                return render(request, 'jdm/candidat_create.html', {'form': form})

    else:
        form = RechercheCandidatForm()
    return render(request, 'jdm/candidat_create.html', {'form': form})


def candidat_valide(request, qqn):
    joueur = request.user
    candidat = Candidat.objects.get(wiki_id=qqn)
    nb_paris = len(Pari.objects.filter(joueur=joueur, mort=False))
    if Pari.objects.filter(joueur=joueur, candidat=candidat):
        messages.success(request, ("Ce candidat est déjà dans votre liste"))
        return redirect('candidat-create')
    elif nb_paris < 10:
        Pari(candidat=candidat, joueur=joueur).save()
        candidat = Candidat.objects.get(wiki_id=qqn)
        return render(request, 'jdm/candidat_valide.html', {'candidat': candidat, 'nb_paris': nb_paris})
    else:
        return redirect('jdm/classement.html')


def candidat_detail(request, id):
    if len(Candidat.objects.filter(id=id)) != 0:
        candidat = Candidat.objects.get(id=id)
        paris_candidat = Pari.objects.filter(candidat=candidat)
        paris_amis = []
        if request.user.is_authenticated:
            for pari in paris_candidat:
                if cercles.filter(joueur=request.user, ami=pari.joueur):
                    paris_amis.append(pari.joueur)
        return render(request, 'jdm/candidat_detail.html',
                      context={'candidat': candidat, 'paris': paris_amis, 'cercles': cercles})
    else:
        messages.success(request, ("Cette page candidat n'existe pas/plus."))
        return redirect('jdm-index')


def favoris(request):
    favoris = []
    for candidat in candidats:
        age_candidat = candidat.calcul_age()
        nb_paris = len(Pari.objects.filter(candidat=candidat))
        if nb_paris > 1:
            favoris.append((candidat, nb_paris, age_candidat))
    if len(favoris) > 2:
        favoris.sort(key=lambda favori: favori[2])
        favoris.sort(key=lambda favori: favori[1], reverse=True)
    if len(favoris) > 5:
        favoris = favoris[0:3]
    return render(request, 'jdm/favoris.html', {'favoris': favoris, 'candidats': candidats})


def resume(request):
    candidats_decedes = Candidat.objects.filter(DDD__isnull=False)
    liste = []
    for candidat in candidats_decedes:
        nb_paris = Pari.objects.filter(candidat=candidat)
        liste.append((candidat, nb_paris))
    liste.sort(key=lambda x: x[0].DDN, reverse=True)
    return render(request, "jdm/resume.html", {'candidats_decedes': liste})


def envoyer_mail():
    pass


def maj(request):
    resultats = []
    for candidat in candidats:
        # Suppression des fiches candidats inutilisées
        if len(Pari.objects.filter(candidat=candidat)) == 0:
            try:
                candidat.delete()
            except ValueError:
                pass

        # Y a-t-il eu des décès ?
        deces = []
        PARAMS_recherche = {"action": "wbgetclaims", "entity": candidat.wiki_id, "format": "json"}
        jsonresponse_recherche = requests.get(URL, PARAMS_recherche).json()
        if candidat.DDD:
            pass
        elif "P570" in jsonresponse_recherche["claims"] and not candidat.DDD:
            DDD = datetime.strptime(
                jsonresponse_recherche["claims"]["P570"][0]["mainsnak"]["datavalue"]["value"]["time"],
                '+%Y-%m-%dT%H:%M:%SZ').date()
            candidat.DDD = DDD
            #candidat.mort = True
            candidat.save()
            for pari in paris:
                if pari.wiki_id == candidat.wiki_id:
                    #pari.mort = True
                    #pari.save()
                    deces.append(candidat)

        if len(deces) > 0:
            for user in users:
                for pari in Pari.objects.filter():
                    pass

            gagnants = []
            for candidat in deces:
                for pari in Pari.objects.filter(candidat=candidat):
                    if User.objects.get(id=pari.user_id) not in gagnants:
                        gagnants.append(pari.joueur)
                resultats.append([candidat, gagnants])
    envoyer_mail()
    return redirect('resume')


def change_password(request):
    pass


def parametres(request):
    if len(Preference.objects.filter(joueur=request.user)) == 0:
        Preference(joueur=request.user).save()
    prefs = Preference.objects.get(joueur=request.user)

    if request.method == 'POST':
        form = PreferenceForm(request.POST, instance=prefs)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vos paramètres ont été mis à jour')
            return redirect('parametres')

    else:
        form = PreferenceForm(instance=prefs)
        return render(request, "jdm/parametres.html", {'joueur': request.user, 'form': form})


def diapo(request):
    return render(request, 'jdm/diapo.html', {'candidats': candidats})

