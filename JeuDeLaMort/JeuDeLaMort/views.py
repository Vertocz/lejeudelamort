import gzip
import json
import urllib

from django.core.exceptions import ObjectDoesNotExist
from django import forms
from django.shortcuts import render, redirect
from datetime import datetime, date
from .models import Candidat, Pari, Cercle, Preference, Historique, Prout
from django.contrib.auth.models import User
from .forms import RechercheCandidatForm, PreferenceForm, UpdateUserForm, ProutForm
from django.contrib import messages

import requests

candidats = Candidat.objects.all()
users = User.objects.all()
paris = Pari.objects.all()
cercles = Cercle.objects.all()
URL = "https://www.wikidata.org/w/api.php"


def index(request):
    return render(request, "jdm/index.html")


def score_max(joueur, annee):
    paris = Pari.objects.filter(joueur=joueur, saison=annee, mort=False)
    score = 0
    for pari in paris:
        try:
            candidat = pari.candidat
            points = candidat.points()
            score += points
        except ObjectDoesNotExist:
            pass
    return score


def score_user(paris_user, annee):
    score = 0
    for pari in paris_user.filter(saison=annee, mort=True):
        print(pari.candidat, pari.candidat.points())
        try:
            candidat = pari.candidat
            if candidat.DDD:
                print(candidat.DDD.year)
                if candidat.DDD.year == annee:
                    points = candidat.points()
                    score += points
        except ObjectDoesNotExist:
            pass
    return score


def joker(joueur, annee):
    paris_joueur = Pari.objects.filter(joueur=joueur, saison=annee)
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


def moyenne_age(joueur, annee):
    paris_user = Pari.objects.filter(joueur=joueur, saison=annee)
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


def salle_user(request, id, annee):
    saison_terminee = True
    if datetime.now().year == annee:
        saison_terminee = False

    saisons = []
    for pari in paris.filter(joueur=id):
        if pari.saison not in saisons:
            saisons.append(pari.saison)

    try:
        joueur = User.objects.get(id=id)
        paris_user = Pari.objects.filter(joueur=joueur, saison=annee)
        paris_decedes = Pari.objects.filter(joueur=joueur, saison=annee, mort=True)
        candidats_joueur = []
        for pari in paris_user:
            candidat = candidats.get(wiki_id=pari.candidat.wiki_id)
            candidats_joueur.append(candidat)
        return render(request,
                      'jdm/salle_user.html',
                      {'joueur': joueur, 'poker': joker(joueur, annee), 'score_max': score_max(joueur, annee),
                       'score': score_user(paris_user, annee), 'paris': paris_user, 'deces': paris_decedes,
                       'rap': 10 - len(paris_user) + len(paris_decedes), 'candidats_joueur': candidats_joueur,
                       'moyenne': moyenne_age(joueur, annee), "terminee": saison_terminee, "saisons": saisons,
                       "saison_en_cours": annee})

    except ObjectDoesNotExist:
        messages.success(request, ("Ce joueur n'existe pas/plus"))
        return redirect('classement', 2024)


def recherche_amis(request):
    if request.method == 'POST':
        your_name = request.POST['your_name']
        amis_potentiels = User.objects.filter(username__iexact=your_name)
        return render(request, 'jdm/recherche_amis.html', {'liste': amis_potentiels})
    else:
        classement(request)


def classement(request, annee):
    saison_en_cours = annee
    liste = liste_amis(request.user, annee)
    saisons = []
    for pari in paris:
        if pari.saison not in saisons:
            saisons.append(pari.saison)
    saisons.sort(key=lambda saison: saison)
    return render(request, 'jdm/classement.html',
                  {'liste': liste[0], 'en_devenir': liste[1], "saisons": saisons, "saison_en_cours": saison_en_cours})


def liste_amis(joueur, saison):
    liste = []
    for user in users:
        if user.id == 11 and saison > 2023:
            pass
        else:
            if len(Cercle.objects.filter(joueur=joueur, ami=user)) != 0:
                est_un_ami = True
            else:
                est_un_ami = False
            paris_user = Pari.objects.filter(joueur=user, saison=saison)
            nominations = len(paris_user)
            score_user_x = score_user(paris_user, saison)
            succes = 0
            for pari in Pari.objects.filter(joueur=user, saison=saison):
                if pari.mort:
                    if pari.candidat.DDD.year == saison:
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
    annee = datetime.now().year
    ami = User.objects.get(id=id)
    liste = liste_amis(request.user.id, datetime.now().year)[0]
    if Cercle.objects.filter(ami=ami, joueur=request.user):
        messages.success(request, (str(User.objects.get(id=id).username) + " est déjà dans votre cercle"))
        return render(request, 'jdm/classement.html', {'liste': liste})
    if id == request.user.id:
        messages.success(request, ("Vous voudriez vraiment être ami.e avec vous-même ?"))
        return render(request, 'jdm/classement.html', {'liste': liste})
    else:
        Cercle(ami=ami, joueur=request.user).save()
        return render(request, 'jdm/nouvel_ami.html', {'ami': ami, 'annee': annee})


def retirer_ami(request, id):
    annee = datetime.now().year
    Cercle.objects.get(ami=User.objects.get(id=id), joueur=request.user.id).delete()
    messages.success(request, (str(User.objects.get(id=id).username) + " a été retiré.e de votre cercle"))
    return redirect('classement', annee)


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
                        if pari.candidat == candidat_potentiel and pari.saison == datetime.now().year:
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
    nb_paris = len(Pari.objects.filter(joueur=joueur, mort=False, saison=int(datetime.now().year)))
    annee = datetime.now().year
    if Pari.objects.filter(joueur=joueur, candidat=candidat, saison=int(datetime.now().year)):
        messages.success(request, ("Ce candidat est déjà dans votre liste"))
        return redirect('candidat-create')
    elif nb_paris < 10:
        Pari(candidat=candidat, joueur=joueur, saison=int(datetime.now().year)).save()
        candidat = Candidat.objects.get(wiki_id=qqn)
        return render(request, 'jdm/candidat_valide.html', {'candidat': candidat, 'nb_paris': nb_paris, 'annee': annee})
    else:
        return redirect('jdm-index')


def candidat_detail(request, id):
    annee = datetime.now().year
    if len(Candidat.objects.filter(id=id)) != 0:
        candidat = Candidat.objects.get(id=id)
        paris_candidat = Pari.objects.filter(candidat=candidat, saison=annee)
        paris_amis = []
        if request.user.is_authenticated:
            for pari in paris_candidat:
                if cercles.filter(joueur=request.user, ami=pari.joueur):
                    paris_amis.append(pari.joueur)
        return render(request, 'jdm/candidat_detail.html',
                      context={'candidat': candidat, 'paris': paris_amis, 'cercles': cercles, 'annee': annee})
    else:
        messages.success(request, ("Cette page candidat n'existe pas/plus."))
        return redirect('jdm-index')


def favoris(request):
    favoris = []
    for candidat in candidats:
        age_candidat = candidat.calcul_age()
        nb_paris = len(Pari.objects.filter(candidat=candidat, saison=int(datetime.now().year)))
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

    for year in range(2023, datetime.now().year + 1):
        liste_annee = []
        for candidat in candidats_decedes:
            if candidat.DDD.year == year:
                nb_paris = Pari.objects.filter(candidat=candidat, saison=year)
                liste_annee.append((candidat, nb_paris))
        liste_annee.sort(key=lambda x: x[0].DDN, reverse=True)
        liste.append((year, liste_annee))

    return render(request, "jdm/dans_nos_coeurs.html", {'liste': reversed(liste)})


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
            candidat.save()
            for pari in paris:
                if pari.candidat == candidat:
                    pari.mort = True
                    pari.save()
                    deces.append(candidat)
                if pari.candidat.DDD and pari.mort == False:
                    pari.mort = True
                    pari.save()

        if len(deces) > 0:
            for user in users:
                for pari in Pari.objects.filter():
                    pass

            gagnants = []
            for candidat in deces:
                for pari in Pari.objects.filter(candidat=candidat, saison=int(datetime.now().year)):
                    if User.objects.get(id=pari.joueur.id) not in gagnants:
                        gagnants.append(pari.joueur)
                resultats.append([candidat, gagnants])
    envoyer_mail()
    return redirect('resume')


def maj_annuelle(request):
    for user in users:
        if len(Historique.objects.filter(joueur=user, saison=int(datetime.now().year) - 1)) == 0:
            Historique(joueur=user, saison=int(datetime.now().year) - 1,
                       score=score_user(Pari.objects.filter(joueur=user), int(datetime.now().year) - 1), ).save()
    saison = int(datetime.now().year - 1)
    for pari in Pari.objects.filter(saison=saison):
        pari.passe = True
        pari.save()
    return redirect('jdm-index')


def change_password(request):
    pass


def parametres(request):
    if len(Preference.objects.filter(joueur=request.user)) == 0:
        Preference(joueur=request.user).save()
    prefs = Preference.objects.get(joueur=request.user)
    user = User.objects.get(id=request.user.id)

    if request.method == 'POST':
        if 'informations' in request.POST:
            form = UpdateUserForm(request.POST, instance=user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Vos paramètres ont été mis à jour')
                return redirect('parametres')

        elif 'communication' in request.POST:
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


def pet(request):
    musiciens = []
    prouts = Prout.objects.all()
    for prout in prouts:
        if prout.auteur not in musiciens:
            musiciens.append(prout.auteur)
    if request.method == 'POST':
        form = ProutForm(request.POST, request.FILES)
        if form.is_valid():
            if str(form.cleaned_data.get('performance')).lower().endswith(('.mp3', '.m4a', '.ogg')):
                Prout(auteur=request.user, performance=form.cleaned_data.get('performance')).save()
                messages.success(request, 'Le prout a bien été ajouté')
                prouts = Prout.objects.all()
                for prout in prouts:
                    if prout.auteur not in musiciens:
                        musiciens.append(prout.auteur)
                return render(request, 'jdm/akikileprout.html',
                              {"form": form, 'musiciens': musiciens, 'prouts': prouts})
            else:
                messages.error(request, 'Ce format de fichier n\'est pas pris en charge')
                form = ProutForm(initial={'auteur': request.user})
                return render(request, 'jdm/akikileprout.html',
                              {'form': form, 'musiciens': musiciens, 'prouts': prouts})
        else:
            messages.error(request, 'Quelque chose ne s\'est pas passé correctement')
            form = ProutForm(initial={'auteur': request.user})
            return render(request, 'jdm/akikileprout.html', {'form': form, 'musiciens': musiciens, 'prouts': prouts})

    else:
        print('else', request.method)
        form = ProutForm(initial={'auteur': request.user})
        return render(request, 'jdm/akikileprout.html', {'form': form, 'musiciens': musiciens, 'prouts': prouts})


def bingo(request):
    class JoueurForm(forms.Form):
        joueur = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'placeholder': 'WackyJacky101'}))

    if request.method == 'POST':
        form = JoueurForm(request.POST)
        if form.is_valid():
            joueur = form.data['joueur']
            return render(request, 'jdm/bingo.html', {'form': form, 'matches': bingo_joueur(joueur), 'joueur': joueur})
    else:
        form = JoueurForm()
        return render(request, 'jdm/bingo.html', {'form': form})


def bingo_joueur(joueur):
    key = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqdGkiOiI2MjE2MWUwMC0wNDk1LTAxM2QtYmMzYS0zZTk5NDk5ZjNlY2UiLCJpc3MiOiJnYW1lbG9ja2VyIiwiaWF0IjoxNzE3NTAxMzIyLCJwdWIiOiJibHVlaG9sZSIsInRpdGxlIjoicHViZyIsImFwcCI6ImJpbmdvLXB1YmcifQ.Fm-PsL47ALnAjzAU78ER7LZmPRdl8Ye2nrl_J3R45j4"
    URL = "https://api.pubg.com/shards/steam/"
    header = {
        "Authorization": "Bearer " + key,
        "Accept": "application/vnd.api+json",
    }

    player_stat_url = "players?filter[playerNames]=" + joueur
    match_url = "matches/"

    r = requests.get(URL + player_stat_url, headers=header)
    jsonresponse = r.json()

    matches = []
    # récupération des données des 6 derniers matches pour chaque match du joueur
    limite = 10
    if len(jsonresponse['data'][0]['relationships']['matches']['data']) < 10:
        limite = len(jsonresponse['data'][0]['relationships']['matches']['data'])
    for i in range(0, limite):
        # 1 Prendre un ramassage d'urgence
        EmPickup = False
        # 2 conduire un ULM
        ulm = False
        # 3 faire top 1
        top1 = False
        # 4 looter un drop
        crate = False
        # 5 +100m kill
        kill_100m = False
        # 6 parcourir 3km sur la route
        ride_distance = False
        # 7 tuer un vrai joueur
        real_kill = False
        # 8 kill au pistolet
        pistol_kill = False
        # 9 atterrir à Stalber
        stalber = False
        reynerie = False
        # 10 KOBE
        kobe = False
        # 11 écraser quelqu'un
        smash = False
        # 12 kill en zone bleue
        bz_kill = False
        # 13 spike strip un véhicule
        spiked = False
        # 14 tuer 3 bots
        bots_killer = False
        bots_killed = 0
        # 15 utiliser 5 flashes
        flasher = False
        used_flashes = 0
        # 16 drive-by kill
        driveby = False
        # 17 survivre 10 min
        survivor = False
        # 18 réanimer 3 fois un teammate
        camille = False

        positions = []

        match_id = jsonresponse['data'][0]['relationships']['matches']['data'][i]['id']
        r = requests.get(URL + match_url + match_id, headers=header)
        jsonresponse_match = r.json()

        # récupération de la date du match
        date = datetime.strptime(jsonresponse_match['data']['attributes']['createdAt'], '%Y-%m-%dT%H:%M:%SZ').date()
        gamers = []
        equipe = []

        telemetry = jsonresponse_match['data']['relationships']['assets']['data'][0]['id']

        game_mode = jsonresponse_match['data']['attributes']['gameMode']
        team = jsonresponse_match['data']['attributes']['gameMode']

        for dict in jsonresponse_match["included"]:
            if dict['type'] == 'participant':
                if 'account' in dict["attributes"]["stats"]["playerId"]:
                    # on récupère le classement
                    if joueur == dict["attributes"]['stats']['name']:
                        classement = dict["attributes"]['stats']['winPlace']

                    # on établit la liste des joueurs réels
                    if dict["attributes"]['stats']['name'] not in gamers:
                        gamers.append(dict["attributes"]['stats']['name'])

                if joueur == dict["attributes"]['stats']['name']:
                    classement = dict["attributes"]['stats']['winPlace']
                    if dict["attributes"]['stats']['longestKill'] > 100:
                        kill_100m = True
                    if dict["attributes"]['stats']['rideDistance'] > 3000:
                        ride_distance = True
                    if dict["attributes"]['stats']['roadKills'] > 0:
                        driveby = True
                    if dict["attributes"]['stats']['timeSurvived'] > 600:
                        survivor = True
                    if dict["attributes"]['stats']['revives'] > 1:
                        camille = True

            # récupération du json des événements du match
            if dict['id'] == telemetry:
                telemetry_url = dict["attributes"]["URL"]
                with urllib.request.urlopen(telemetry_url) as url:
                    with gzip.open(url, 'r') as fin:
                        data = json.loads(fin.read().decode('utf-8'))

        for donnee in data:
            try:
                if donnee['_T'] == 'LogVehicleDamage':
                    if donnee['attacker']['name'] == joueur and donnee['damageCauserName'] == "Item_Weapon_SpikeTrap_C":
                        spiked = True

                if donnee['_T'] == "LogPlayerKillV2":
                    if donnee['killer']['name'] == joueur:
                        if donnee['victim']['type'] == 'user_ai':
                            bots_killed += 1
                        elif donnee['victim']['type'] == 'user':
                            real_kill = True
                        if donnee['killerDamageInfo']['damageCauserName'] in ["WeapSawnoff_C", "WeapRhino_C", "WeapNagantM1895_C", "WeapM9_C", "WeapM1911_C", "WeapG18_C", "WeapDesertEagle_C"]:
                            pistol_kill = True
                        elif donnee['killerDamageInfo']['damageCauserName'] == "ProjGrenade_C":
                            kobe = True
                        elif donnee['killerDamageInfo']['damageCauserName'] == "Damage_VehicleHit":
                            smash = True
                        if donnee['victim']['isInBlueZone']:
                            bz_kill = True

                if donnee['_T'] == "LogVehicleRide":
                    if donnee['character']['name'] == joueur and 'glider' in donnee['vehicle']['vehicleId']:
                        ulm = True

                if donnee['_T'] == "LogItemPickupFromCarepackage":
                    if donnee['character']['name'] == joueur:
                        crate = True

                if donnee['_T'] == "LogPlayerPosition":
                    if donnee['character']['name'] == joueur:
                        positions.append(donnee)

                if donnee['_T'] == "LogEmPickupLiftOff":
                    for p in range(0, 3):
                        try:
                            if donnee['riders'][p]['name'] == joueur:
                                EmPickup = True
                        except IndexError:
                            pass
                if donnee['_T'] == 'LogItemUse':
                    if donnee['item']['itemId'] == "Item_Heal_FirstAid_C" and donnee['character']['name'] == joueur:
                        used_flashes += 1

            except KeyError:
                pass
            except TypeError:
                pass

        if bots_killed >= 3:
            bots_killer = True

        if used_flashes >= 1:
            flasher = True

        if len(positions) < 7:
            limite = len(positions) - 1
        else:
            limite = 6
        for position in positions:
            try:
                # if position['character']['zone'][0] == "school":
                #     stalber = True
                if 435000 < position['character']['location']['x'] < 450000 and 326000.0 < position['character']['location']['y'] < 341000 and position['elapsedTime'] < 200:
                    reynerie = True
            except IndexError:
                pass

        if classement == 1:
            top1 = True

        bingo = [ulm, top1, EmPickup, crate, kill_100m, ride_distance, real_kill, pistol_kill, reynerie, kobe, smash,
                 bz_kill, bots_killer, spiked, flasher, driveby, survivor, camille]
        matches.append([match_id, date, equipe, gamers, classement, bingo, game_mode])

    matches.sort(key=lambda x: x[1], reverse=True)

    return matches
