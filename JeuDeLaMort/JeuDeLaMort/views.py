from django.shortcuts import render, redirect
from datetime import datetime, date
from .models import Candidat, Pari, Cercle, Pari_unique, Ligue, Ligue_user
from django.contrib.auth.models import User
from .forms import RechercheCandidatForm, CercleForm, LigueForm, Ligue_userForm
from django.contrib import messages
import requests

candidats = Candidat.objects.all()
users = User.objects.all()
paris = Pari.objects.all()
cercles = Cercle.objects.all()
URL = "https://www.wikidata.org/w/api.php"


def index(request):
    morts_recentes = []
    morts_recentes_perso = []
    paris_amis = []
    for x in liste_amis(request.user.id)[0]:
        if len(Pari.objects.filter(user_id=x[0].id)) > 0:
            for pari in Pari.objects.filter(user_id=x[0].id):
                paris_amis.append(pari)

    mes_paris = Pari.objects.filter(user_id=request.user.id)

    for candidat in candidats:
        if candidat.DDD is not None:
            try:
                if datetime.date(request.user.last_login) <= candidat.DDD:
                    for pari in paris_amis:
                        if candidat.wiki_id == pari.wiki_id:
                            if candidat not in morts_recentes:
                                morts_recentes.append(candidat)
                    for pari in mes_paris:
                        if candidat.wiki_id == pari.wiki_id:
                            morts_recentes_perso.append(candidat)
            except AttributeError:
                pass

    if len(morts_recentes) > 0 or len(morts_recentes_perso) > 0:
        return render(request, "jdm/news.html", {"deces": morts_recentes, 'paris_amis': paris_amis, "mes_deces": morts_recentes_perso})
    else:
        return render(request, "jdm/index.html", context={"date": datetime.today(), "candidats": candidats})


def score_max(id):
    paris = Pari.objects.filter(user_id=id)
    score = 0
    for pari in paris:
        candidat = Candidat.objects.get(wiki_id=pari.wiki_id)
        points = candidat.points()
        score += points
    return score


def score_user(paris_user):
    score = 0
    for pari in paris_user:
        candidat = Candidat.objects.get(wiki_id=pari.wiki_id)
        if candidat.DDD:
            points = candidat.points()
            score += points
    return score


def joker(id):
    paris_joueur = Pari.objects.filter(user_id=id)
    record = date.fromisoformat("1900-01-01")
    if len(paris_joueur) > 0:
        recordman = paris_joueur[0]
        for pari in paris_joueur:
            candidat = Candidat.objects.get(wiki_id=pari.wiki_id)
            if candidat.DDN > record:
                record = candidat.DDN
                recordman = candidat
        return recordman
    else:
        pass


def moyenne_age(id):
    paris_user = Pari.objects.filter(user_id=id)
    total_age = 0
    if len(paris_user) > 0:
        for pari in paris_user:
            x = Candidat.objects.get(wiki_id=pari.wiki_id)
            age = x.calcul_age()
            total_age += age
        moyenne = round(total_age / len(paris_user))
        return moyenne
    else:
        pass


def salle_attente(request):
    id = request.user.id
    candidats_salle = Candidat.objects.filter(wiki_id__in=Pari.objects.filter(user_id=id))
    joueur = User.objects.get(id=id)
    paris_user = Pari.objects.filter(user_id=id)
    paris_decedes = Pari.objects.filter(user_id=id, mort=True)
    user = User.objects.get(id=request.user.id)
    reste_a_parier = 10 - len(paris_user.filter(mort=False))
    poker = joker(id)
    moyenne = moyenne_age(id)
    return render(request,
                  'jdm/salle_attente.html',
                  {'joueur': joueur, 'candidats_salle': candidats_salle, 'score_max': score_max(id),
                   'paris': paris_user, 'deces': paris_decedes, 'score_user': score_user(paris_user), 'poker': poker, 'moyenne': moyenne,
                   'rap': reste_a_parier, 'user': user, 'candidats': Candidat.objects.all()})


def recherche_amis(request):
    form = CercleForm(request.POST)
    if form.is_valid():
        amis_potentiels = User.objects.filter(username__iexact=form.data['ami_name'])
        return render(request, 'jdm/recherche_amis.html', {'form': form, 'liste': amis_potentiels})

    else:
        form = CercleForm()
        return render(request, 'jdm/recherche_amis.html', {'form': form, 'users': users})


def amis(request):
    liste = liste_amis(request.user.id)
    return render(request, 'jdm/mes_amis.html', {'liste': liste[0], 'en_devenir': liste[1]})


def liste_amis(id):
    amis = Cercle.objects.filter(user_id=id)
    liste= []
    for x in amis:
        ami = User.objects.get(id=x.ami_id)
        score_max_x = score_max(ami.id)
        paris_user = Pari.objects.filter(id=ami.id)
        score_user_x = score_user(paris_user)
        moyenne_x = moyenne_age(ami.id)
        joker_x = joker(ami.id)
        liste.append((ami, score_user_x, score_max_x, moyenne_x, joker_x))
    liste.sort(key=lambda x: x[2], reverse=True)
    liste.sort(key=lambda x: x[1], reverse=True)

    pas_encore_amis = Cercle.objects.filter(ami_id=id)
    amis_en_devenir = []
    for ami in pas_encore_amis:
        if len(Cercle.objects.filter(user_id=id, ami_id=ami.user_id)) < 1:
            amis_en_devenir.append(User.objects.get(id=ami.user_id))

    return liste, amis_en_devenir


def nouvel_ami(request, id):
    ami = User.objects.get(id=id)
    liste = liste_amis(request.user.id)[0]
    if Cercle.objects.filter(ami_name=ami.username, ami_id=ami.id, username=request.user.username,
                             user_id=request.user.id):
        return render(request, 'jdm/mes_amis.html', {'liste': liste})
    if id == request.user.id:
        return render(request, 'jdm/mes_amis.html', {'liste': liste})
    else:
        Cercle(ami_name=ami.username, ami_id=ami.id, username=request.user.username, user_id=request.user.id).save()
        return render(request, 'jdm/nouvel_ami.html', {'ami': ami})


def retirer_ami(request, id):
    Cercle.objects.get(ami_id=id, user_id=request.user.id).delete()
    messages.success(request, (str(User.objects.get(id=id).username)+" a été retiré.e de votre cercle"))
    return redirect('mes-amis')


def ligues(request):
    liste_ligues = Ligue_user.objects.filter(user_id=request.user.id)
    creer_form = LigueForm(request.POST)
    if creer_form.is_valid():
        new_ligue = Ligue.objects.create(nom=creer_form.cleaned_data['nom'], description=creer_form.cleaned_data['description'], public=creer_form.cleaned_data['public'], createur=request.user)
        new_ligue.save()
        Ligue_user.objects.create(ligue=new_ligue, user_id=request.user.id, identifiant=new_ligue.id)
        messages.success(request, "Le nouveau cercle de jeu a bien été créé")
        infos = recuperer_infos_joueurs_ligue(request, new_ligue.id)
        return render(request, 'jdm/cercle.html', {'users': infos, 'ligue': new_ligue})
    else:
        creer_form = LigueForm()

    rejoindre_form = Ligue_userForm(request.POST)

    if rejoindre_form.is_valid():
        id = rejoindre_form.cleaned_data['identifiant']
        rejoindre_form = Ligue_userForm()
        rejoindre(request, id)

    else:
        rejoindre_form = Ligue_userForm()

    ligues_publiques = []
    for ligue_publique in Ligue.objects.filter(public=True):
        if len(Ligue_user.objects.filter(user_id=request.user.id, ligue=ligue_publique)) == 0:
            ligues_publiques.append(ligue_publique)

    return render(request, 'jdm/mes_cercles.html', {'cercles': liste_ligues, 'form': creer_form, 'rejoindre': rejoindre_form, 'cercles_publics': ligues_publiques})


def recuperer_infos_joueurs_ligue(request, id):
    users_ligue = []
    for ligue_user in Ligue_user.objects.filter(ligue=id):
        joueur = User.objects.get(id=ligue_user.user_id)
        paris_user = []
        for pari in Pari_unique.objects.filter(ligue=id):
            candidat = Candidat.objects.get(wiki_id=pari.wiki_id)
            if pari.user_id == joueur.id:
                paris_user.append(candidat)
        score = score_user(paris_user)
        users_ligue.append([joueur, paris_user, score])
    return users_ligue


def ligue(request, id):
    ligue_en_cours = Ligue.objects.get(id=id)
    joueur_en_cours = Ligue_user.objects.get(ligue=ligue_en_cours, user_id=request.user.id)
    #récupérer les infos users_ligue (joueurs, compteurs, paris)
    infos = recuperer_infos_joueurs_ligue(request, id)

    form = RechercheCandidatForm(request.POST)
    if form.is_valid():
        recherche = recherche_candidat(form.cleaned_data['nom'])
        if len(recherche) > 0:
            return render(request, 'jdm/candidat_unique.html', {"recherche": recherche, "ligue": ligue_en_cours, "candidats": candidats})
        else:
            form = RechercheCandidatForm()
    else:
        form = RechercheCandidatForm()
    return render(request, 'jdm/cercle.html', {'users': infos, 'ligue': ligue_en_cours, 'tour': joueur_en_cours.tour(), 'form': form, 'on_continue': joueur_en_cours.continuer(), "candidats": candidats})


def rejoindre(request, id):
    if len(Ligue.objects.filter(id=id)) != 0:
        ligue = Ligue.objects.get(id=id)
        if ligue.lancee is False:
            if len(Ligue_user.objects.filter(ligue=ligue, user_id=request.user.id)) == 0:
                ligue_new_user = Ligue_user.objects.create(ligue=ligue, user_id=request.user.id, identifiant=ligue.id)
                ligue_new_user.save()
                rejoindre_form = Ligue_userForm()
                messages.success(request, "Vous avez bien rejoint le cercle de jeu " + ligue.nom)
            else:
                messages.success(request, "Vous avez déjà rejoint le cercle de jeu " + ligue.nom)
        else:
            messages.success(request, ligue.nom + " est un cercle fermé. Vous ne pouvez plus le rejoindre.")
    else:
        messages.success(request, "Aucune ligue ne correspond à cet identifiant.")
    return redirect('cercle', id)


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


def save_pari_unique(request, id, candidat):
    neocandidat = Candidat.objects.get(wiki_id=candidat)
    if len(Pari_unique.objects.filter(ligue=Ligue.objects.get(id=id), wiki_id=candidat)) > 0:
        if Pari_unique.objects.get(ligue=Ligue.objects.get(id=id), wiki_id=candidat).user_id != request.user.id:
            messages.success(request, neocandidat.nom + " est déjà dans la liste de " + str(User.objects.get(id=Pari_unique.objects.get(ligue=Ligue.objects.get(id=id), wiki_id=candidat).user_id)))
        elif Pari_unique.objects.get(ligue=Ligue.objects.get(id=id), wiki_id=candidat).user_id == request.user.id:
            messages.success(request, neocandidat.nom + " est déjà dans votre liste")
    else:
        nouveau_pari = Pari_unique.objects.create(ligue=Ligue.objects.get(id=id), wiki_id=candidat, user_id=request.user.id)
        nouveau_pari.save()
        messages.success(request, neocandidat.nom+" a bien intégré votre liste")
    return redirect('cercle', id)


def lancer_ligue(request, id):
    ligue_a_lancer = Ligue.objects.get(id=id)
    ligue_a_lancer.lancee = True
    ligue_a_lancer.save()
    messages.success(request, "La ligue a bien été lancée")
    return redirect('cercle', id)


def quitter_ligue(request, id):
    Ligue_user.objects.get(ligue=id, user_id=request.user.id).delete()
    for pari in Pari_unique.objects.filter(ligue=id, user_id=request.user.id):
        pari.delete()
    messages.success(request, "Vous avez quitté le cercle de jeu")
    return redirect('mes-cercles')


def salle_user(request, id):
    if len(Cercle.objects.filter(user_id=request.user.id, ami_id=id)) > 0:
        paris_user = Pari.objects.filter(user_id=id)
        paris_decedes = Pari.objects.filter(user_id=id, mort=True)
        candidats_joueur = []
        for pari in paris_user:
            candidat = candidats.get(wiki_id=pari.wiki_id)
            candidats_joueur.append(candidat)
        return render(request,
                      'jdm/salle_user.html',
                      {'joueur': User.objects.get(id=id), 'poker': joker(id), 'score_max': score_max(id),
                       'score': score_user(paris_user), 'paris': Pari.objects.filter(user_id=id), 'deces': paris_decedes,
                       'rap': 10 - len(paris_user), 'candidats_joueur': candidats_joueur,
                       'moyenne': moyenne_age(id)})
    else:
        return redirect('mes-amis')


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
                    if Candidat.objects.filter(nom=candidat, DDN=DDN, wiki_id=wiki_id, description=description,
                                               photo=photo):
                        new_candidat = Candidat.objects.get(wiki_id=wiki_id)
                    else:
                        new_candidat = Candidat(nom=candidat, DDN=DDN, wiki_id=wiki_id, description=description,
                                                photo=photo)
                        new_candidat.save()
                    candidats_potentiels.append(new_candidat)

            if len(candidats_potentiels) >= 1:
                amis = Cercle.objects.filter(user_id=request.user.id)
                paris_amis = []
                for candidat_potentiel in candidats_potentiels:
                    for pari in paris:
                        if pari.wiki_id == candidat_potentiel.wiki_id:
                            for ami in amis:
                                if ami.ami_id == pari.user_id:
                                    paris_amis.append((candidat_potentiel, ami.ami_name))
                return render(request, 'jdm/candidat_choix.html',
                              context={"recherche": candidats_potentiels, "paris": paris, "paris_amis": paris_amis,
                                       "users": User.objects.all()})

            if len(candidats_potentiels) == 0:
                return render(request, 'jdm/candidat_create.html', {'form': form})

    else:
        form = RechercheCandidatForm()
    return render(request, 'jdm/candidat_create.html', {'form': form})


def candidat_valide(request, qqn):
    id = request.user.id
    candidat = Candidat.objects.get(wiki_id=qqn)
    if Pari.objects.filter(user_id=id, wiki_id=qqn):
        return render(request, 'jdm/redite.html')
    elif len(Pari.objects.filter(user_id=id, mort=False)) < 10:
        Pari(wiki_id=qqn, user_id=id, candidat_nom=candidat.nom, username=request.user.username).save()
        candidat = Candidat.objects.get(wiki_id=qqn)
        return render(request, 'jdm/candidat_valide.html', {'candidat': candidat})
    else:
        return render(request, 'jdm/liste_terminee.html')


def candidat_detail(request, id):
    if len(Candidat.objects.filter(id=id)) != 0:
        users = User.objects.all()
        candidat = Candidat.objects.get(id=id)
        paris_candidat = Pari.objects.filter(wiki_id=candidat.wiki_id)
        paris_amis = []
        for pari in paris_candidat:
            if cercles.filter(user_id=request.user.id, ami_id=pari.user_id):
                paris_amis.append(User.objects.get(id=pari.user_id))
        return render(request, 'jdm/candidat_detail.html',
                      context={'candidat': candidat, 'paris': paris_amis, 'users': users, 'cercles': cercles})
    else:
        messages.success(request, ("Cette page candidat n'existe pas/plus."))
        return redirect('jdm-index')


def favoris(request):
    favoris = []
    for candidat in candidats:
        age_candidat = candidat.calcul_age()
        nb_paris = len(Pari.objects.filter(wiki_id=candidat.wiki_id))
        if nb_paris > 1:
            favoris.append((candidat, nb_paris, age_candidat))
    if len(favoris) > 2:
        favoris.sort(key=lambda favori: favori[2])
        favoris.sort(key=lambda favori: favori[1], reverse=True)
    if len(favoris) > 5:
        favoris = favoris[0:5]
    return render(request, 'jdm/favoris.html', {'favoris': favoris, 'candidats': candidats})


def resume(request):
    candidats_decedes = Candidat.objects.filter(DDD__isnull=False)
    liste = []
    for candidat in candidats_decedes:
        nb_paris = Pari.objects.filter(wiki_id=candidat.wiki_id)
        liste.append((candidat, nb_paris))
    liste.sort(key=lambda x: x[0].DDN, reverse=True)
    return render(request, "jdm/resume.html", {'candidats_decedes': liste})


def maj(request):
    for candidat in candidats:
        wiki_id = candidat.wiki_id

        # Suppression des fiches candidats inutilisées
        if len(Pari.objects.filter(wiki_id=wiki_id)) == 0 and len(Pari_unique.objects.filter(wiki_id=wiki_id)) == 0:
            try:
                candidat.delete()
            except ValueError:
                pass

        # Y a-t-il eu des décès ?
        PARAMS_recherche = {"action": "wbgetclaims", "entity": wiki_id, "format": "json"}
        jsonresponse_recherche = requests.get(URL, PARAMS_recherche).json()
        if candidat.DDD:
            pass
        elif "P570" in jsonresponse_recherche["claims"] and not candidat.DDD:
            DDD = datetime.strptime(
                jsonresponse_recherche["claims"]["P570"][0]["mainsnak"]["datavalue"]["value"]["time"],
                '+%Y-%m-%dT%H:%M:%SZ').date()
            candidat.DDD = DDD
            candidat.mort = True
            candidat.save()
            for pari in paris:
                if pari.wiki_id == candidat.wiki_id:
                    pari.mort = True
                    pari.save()
    return redirect('resume')

