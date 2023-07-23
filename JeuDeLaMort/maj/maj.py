import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'JeuDeLaMort.JeuDeLaMort.settings')
from JeuDeLaMort.JeuDeLaMort.models import Candidat, Pari, Pari_unique

from django.contrib.sites import requests

import datetime

URL = "https://www.wikidata.org/w/api.php"


def maj():
    for candidat in Candidat.objects.all():
        wiki_id = candidat.wiki_id

        # Suppression des fiches candidats inutilisées
        if len(Pari.objects.filter(wiki_id=wiki_id)) == 0 and len(Pari_unique.objects.filter(wiki_id=wiki_id)) == 0:
            try:
                candidat.delete()
            except ValueError:
                pass
        else:
            if candidat.DDD:
                pass
            else:
                # Y a-t-il eu des décès ?
                PARAMS_recherche = {"action": "wbgetclaims", "entity": wiki_id, "format": "json"}
                jsonresponse_recherche = requests.get(URL, PARAMS_recherche).json()
                if "P570" in jsonresponse_recherche["claims"] and not candidat.DDD:
                    candidat.DDD = datetime.strptime(
                        jsonresponse_recherche["claims"]["P570"][0]["mainsnak"]["datavalue"]["value"]["time"],
                        '+%Y-%m-%dT%H:%M:%SZ').date()
                    candidat.mort = True
                    candidat.save()
                    for pari in Pari.objects.filter(wiki_id=candidat.wiki_id):
                        pari.mort = True
                        pari.save()
                else:
                    pass


maj()
