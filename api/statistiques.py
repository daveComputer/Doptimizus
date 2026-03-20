import re
import json
import os
from api.optimiseur_top3 import  mapper_points_vers_axes

# 1. VOS MULTIPLICATEURS HARDCODÉS (La base fixe)
# Ce sont les poids "théoriques" de chaque stat
BASE_MULTIPLIERS = {
    "coeff_stat_principal": 2,
    "coeff_pa": 400,
    "coeff_pm": 360,
    "coeff_po": 100,
    "coeff_invoc": 60,
    "coeff_sagesse":2,
    "coeff_ini":0.2,
    "coeff_fuite": 8,
    "coeff_tacle": 8,
    "coeff_res_pourcentage": 12,
    "coeff_crit": 20,
    "coeff_re_fixe": 4,
    "coeff_re_pa/pm":14,
    "coeff_soins":20,
    "coeff_do":10,
    "coeff_pui":4
}

def extraire_donnees(config_user):
    """
    Extrait les scores de désirabilité directement depuis l'objet 
    de configuration en mémoire.
    """
    if not config_user:
        print("Erreur : Aucune configuration utilisateur reçue.")
        return {}

    # On accède directement aux clés du dictionnaire envoyé par le frontend
    # Note : Assure-toi que ton JS envoie bien cette structure (radar_stats -> details)
    try:
        details = config_user.get('radar_stats', {}).get('details', [])
        
        desirabilite = { 
            item['caracteristique']: float(item['score_desirabilite']) 
            for item in details 
        }
        return desirabilite
        
    except (KeyError, TypeError) as e:
        print(f"Erreur lors de l'extraction des données de désirabilité : {e}")
        return {}
    

# --- 3. VOTRE LOGIQUE DE CALCUL ---
def executer_calcul_perso(config_user=None):
    if config_user is None:
        print("Aucune configuration utilisateur fournie, utilisation des valeurs par défaut.")
    desir= extraire_donnees(config_user)
    if not desir: return
    lvl = config_user.get('lvl', 200)
    moyenne_sort = config_user.get('moyenne_sort', 30)
    elements_choisis = config_user.get('elements', [])

    # On définit les variables binaires pour tes formules
    FORCE = 1.5 if "Force" in elements_choisis else 0
    INTELLIGENCE = 1 if "Intelligence" in elements_choisis else 0
    CHANCE = 1 if "Chance" in elements_choisis else 0
    AGILITE = 1 if "Agilité" in elements_choisis else 0
    SUM_CARAC = FORCE + INTELLIGENCE + CHANCE + AGILITE

    

    scores_finaux = {}
    
    scores_finaux["Puissance"]= {"rarete":  BASE_MULTIPLIERS["coeff_stat_principal"],
                                 "desir": desir.get("Caractéristique(s) principale(s)", 1)}
    scores_finaux["PA"]= {"rarete":  BASE_MULTIPLIERS["coeff_pa"],
                          "desir": desir.get("PA", 1)}
    scores_finaux["PM"]= {"rarete":  BASE_MULTIPLIERS["coeff_pm"],
                          "desir": desir.get("PM", 1)}
    scores_finaux["PO"]= {"rarete":  BASE_MULTIPLIERS["coeff_po"],
                          "desir": desir.get("PO", 1)}
    scores_finaux["Invocations"]= {"rarete":  BASE_MULTIPLIERS["coeff_invoc"],
                                   "desir": desir.get("Invocations", 1)}
    scores_finaux["Initiative"]= {"rarete":  BASE_MULTIPLIERS["coeff_ini"],
                                   "desir": desir.get("Initiative", 1)}
    scores_finaux["Fuite"]= {"rarete":  BASE_MULTIPLIERS["coeff_fuite"],
                             "desir": desir.get("Fuite", 1)}
    scores_finaux["Tacle"]= {"rarete":  BASE_MULTIPLIERS["coeff_tacle"],
                             "desir": desir.get("Tacle", 1)}
    scores_finaux["% Rés."]= {"rarete":  BASE_MULTIPLIERS["coeff_res_pourcentage"],
                              "desir": desir.get("Résistances", 1)}
    dommage_moyen=lvl*4*(1-desir.get("Résistances", 1)/20*0.35)
    scores_finaux["Rés. fixe"]= {"rarete":  BASE_MULTIPLIERS["coeff_re_fixe"]*300/dommage_moyen,
                                 "desir": desir.get("Résistances", 1)}
    scores_finaux["Esquive PA"]= {"rarete":  BASE_MULTIPLIERS["coeff_re_pa/pm"]/2,
                                  "desir": desir.get("PA", 1)/desir.get("PM", 1)}
    scores_finaux["Esquive PM"]= {"rarete":  BASE_MULTIPLIERS["coeff_re_pa/pm"]/2,
                                  "desir": desir.get("PM", 1)/desir.get("PA", 1)}
    scores_finaux["Dommages"]= {"rarete":  BASE_MULTIPLIERS["coeff_do"]*20/moyenne_sort,
                                 "desir": desir.get("Caractéristique(s) principale(s)", 1)}
    scores_finaux["Dommages Eau"]= {"rarete":  BASE_MULTIPLIERS["coeff_do"] * CHANCE/SUM_CARAC*20/moyenne_sort,
                                    "desir": desir.get("Caractéristique(s) principale(s)", 1)}
    scores_finaux["Dommages Neutre"]= {"rarete":  BASE_MULTIPLIERS["coeff_do"] * FORCE/3/SUM_CARAC*20/moyenne_sort,
                                       "desir": desir.get("Caractéristique(s) principale(s)", 1)}
    scores_finaux["Dommages Terre"]= {"rarete":  BASE_MULTIPLIERS["coeff_do"] * FORCE*2/3/SUM_CARAC*20/moyenne_sort,
                                       "desir": desir.get("Caractéristique(s) principale(s)", 1)}
    scores_finaux["Dommages Air"]= {"rarete":  BASE_MULTIPLIERS["coeff_do"] * AGILITE/SUM_CARAC*20/moyenne_sort,
                                    "desir": desir.get("Caractéristique(s) principale(s)", 1)}
    scores_finaux["Dommages Feu"]= {"rarete":  BASE_MULTIPLIERS["coeff_do"] * INTELLIGENCE/SUM_CARAC*20/moyenne_sort,
                                     "desir": desir.get("Caractéristique(s) principale(s)", 1)}
    scores_finaux["Soins"]= {"rarete":  BASE_MULTIPLIERS["coeff_soins"],
                             "desir": desir.get("Soins", 1)}
    scores_finaux["Critique"]= {"rarete":  BASE_MULTIPLIERS["coeff_crit"],
                                 "desir": desir.get("Critique", 1)}
    scores_finaux["Retrait PA"]= {"rarete":  BASE_MULTIPLIERS["coeff_re_pa/pm"],
                                   "desir": desir.get("Retrait PA", 1)}
    scores_finaux["Retrait PM"]= {"rarete":  BASE_MULTIPLIERS["coeff_re_pa/pm"],
                                   "desir": desir.get("Retrait PM", 1)}
    scores_finaux["Dommages Poussée"]= {"rarete":  BASE_MULTIPLIERS["coeff_do"],
                                        "desir": desir.get("Dommages Poussée", 1)}
    global_sum = float(config_user.get('radar_stats', {}).get('global_sum_score', 1))

    chances_crit=(((desir.get("Critique", 1)/global_sum/0.3)**2)*lvl*0.8+20)/100
    if chances_crit>1:
        chances_crit=1
    
    poids_details = {
        "Intelligence": {
            "Intelligence":{"rarete": BASE_MULTIPLIERS["coeff_stat_principal"] * INTELLIGENCE / SUM_CARAC,
                            "desir": desir.get("Caractéristique(s) principale(s)", 1)},
            "Initiative": {"rarete": BASE_MULTIPLIERS["coeff_ini"] * (1 - INTELLIGENCE),
                           "desir": desir.get("Initiative", 1)},
            "Soins": {"rarete": 0.1*scores_finaux["Soins"]["rarete"],
                      "desir": scores_finaux["Soins"]["desir"]}
        },
        "Force": {
            "Force": {"rarete":BASE_MULTIPLIERS["coeff_stat_principal"] * FORCE / SUM_CARAC,
                      "desir": desir.get("Caractéristique(s) principale(s)", 1)},
            "Initiative": {"rarete":BASE_MULTIPLIERS["coeff_ini"] * (1.5 - FORCE),
                           "desir": desir.get("Initiative", 1)}
        },
        "Chance": {
            "Chance": {"rarete": BASE_MULTIPLIERS["coeff_stat_principal"] * CHANCE / SUM_CARAC,
                       "desir": desir.get("Caractéristique(s) principale(s)", 1)},
            "Initiative": {"rarete": BASE_MULTIPLIERS["coeff_ini"] * (1 - CHANCE),
                           "desir": desir.get("Initiative", 1)},
            "Fuite": {"rarete": 0.1*scores_finaux["Fuite"]["rarete"],
                      "desir": scores_finaux["Fuite"]["desir"]}
        },
        "Agilité": {
            "Agilité": {"rarete": BASE_MULTIPLIERS["coeff_stat_principal"] * AGILITE / SUM_CARAC,
                        "desir": desir.get("Caractéristique(s) principale(s)", 1)},
            "Initiative": {"rarete": BASE_MULTIPLIERS["coeff_ini"] * (1 - AGILITE),
                           "desir": desir.get("Initiative", 1)},
            "Tacle": {"rarete": 0.1*scores_finaux["Tacle"]["rarete"],
                      "desir": scores_finaux["Tacle"]["desir"]}
        },
        "Sagesse": {
            "Retrait PA": {"rarete": BASE_MULTIPLIERS["coeff_re_pa/pm"]/10,
                           "desir": desir.get("Retrait PA", 1)},
            "Retrait PM": {"rarete": BASE_MULTIPLIERS["coeff_re_pa/pm"]/10,
                           "desir": desir.get("Retrait PM", 1)},
            "Esquive PA": {"rarete": BASE_MULTIPLIERS["coeff_re_pa/pm"]/20,
                           "desir": desir.get("Esquive PA", 1)},
            "Esquive PM": {"rarete": BASE_MULTIPLIERS["coeff_re_pa/pm"]/20,
                           "desir": desir.get("Esquive PM", 1)}
        },
        "Dommages Critique": {
            "Dommages": {"rarete": scores_finaux["Dommages"]["rarete"] * (chances_crit)*(1-chances_crit/2),
                          "desir": scores_finaux["Dommages"]["desir"]},
            "Critique": {"rarete": scores_finaux["Dommages"]["rarete"] * (chances_crit)*(chances_crit)/2,
                          "desir": scores_finaux["Dommages"]["desir"]}
        }
    }
    
    return scores_finaux, poids_details

def extraire_valeur_max(valeur_str):
    """
    Transforme "201 à 250" en 250, ou "10" en 10.
    Utilise la logique de votre script : max(valeur1, valeur2).
    """
    if isinstance(valeur_str, int):
        return valeur_str
    
    nombres = re.findall(r'-?\d+', str(valeur_str))
    if not nombres:
        return 0
    vals = [int(n) for n in nombres]
    return max(vals)

def calculer_score_stats(liste_stats, scores_finaux, poids_details=None, config_user=None):
    """
    Calcule le score total en intégrant les malus.
    Les malus impactent négativement le score total et la répartition.
    """
    if not scores_finaux:
        return {"total": 0, "repartition": {}}

    total_score = 0
    details_points = {}
    score_norm=0
    details_points_total = {}

    for stat in liste_stats:
        nom = stat['nom']
        # Attention : extraire_valeur_max doit bien retourner une valeur négative si c'est un malus
        val = extraire_valeur_max(stat['valeur']) 
        points_cette_stat = 0
        points_norm=0
        categorie = None

        # --- LOGIQUE DE MAPPING ---
        if nom in scores_finaux:
            categorie = nom
            points_cette_stat = val * scores_finaux[nom]["rarete"]*scores_finaux[nom]["desir"]
            points_norm = val * scores_finaux[nom]["rarete"]
        elif "% Rés." in nom:
            categorie = "% Rés."
            poids = scores_finaux.get("% Rés.", 0)["rarete"]
            points_cette_stat = val * poids * (0.5 if "Neutre" in nom else 1.0) *scores_finaux.get("% Rés.", 0)["desir"]
            points_norm = val * poids * (0.5 if "Neutre" in nom else 1.0)
        elif "Rés." in nom and "%" not in nom:
            categorie = "Rés. fixe"
            poids = scores_finaux.get("Rés. fixe", 0)["rarete"]
            points_cette_stat = val * poids * (0.5 if "Neutre" in nom else 1.0) * scores_finaux.get("Rés. fixe", 0)["desir"]
            points_norm = val * poids * (0.5 if "Neutre" in nom else 1.0)
        elif "Vitalité" == nom:
            categorie = "Vitalité"
            # Si tu n'as pas de poids pour la vita, on considère 1 par défaut ou 0
            points_cette_stat = val
            points_norm = val
        elif nom in poids_details:
            for cat, pts in poids_details[nom].items():
                categorie = cat
                points_cette_stat = val * pts["rarete"] * pts["desir"]
                points_norm = val * pts["rarete"]
                if categorie and points_cette_stat != 0:
                    total_score +=  points_cette_stat
                    score_norm+=points_norm
                    details_points_total[categorie] = details_points_total.get(categorie, 0) + points_cette_stat
                    details_points[categorie] = details_points.get(categorie, 0) + points_norm

        # --- ACCUMULATION ---
        if categorie and points_cette_stat != 0 and nom not in poids_details:
            total_score += points_cette_stat
            score_norm+=points_norm
            details_points_total[categorie] = details_points_total.get(categorie, 0) + points_cette_stat
            details_points[categorie] = details_points.get(categorie, 0) + points_norm
    # --- CALCUL DES POURCENTAGES ---
    repartition = {}
    
    # On évite la division par zéro. 
    # Note : Si total_score est négatif, l'item est globalement "mauvais".
    if score_norm != 0:
        for cat, pts in details_points.items():
            # Si pts est négatif et total_score positif -> % négatif
            # Si pts est positif et total_score positif -> % positif
            pourcentage = (pts / score_norm) * 100
            repartition[cat] = round(pourcentage, 1)
    else:
        for cat, pts in details_points.items():
            repartition[cat] = 0.0

    return {
        "total": round(total_score, 2),
        "repartition": repartition,
        "details_points": details_points_total
    }


def enrichir_base_de_donnees(input_file, output_file, config_user=None):
    """Lit le JSON, calcule les scores/répartitions et sauvegarde."""
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    scores_finaux,poids_details = executer_calcul_perso(config_user=config_user)
    print("Scores finaux calculés :")
    for cat, stats in scores_finaux.items():
        print(f"  {cat}: {stats}")
    print("Poids détaillés :")
    for nom, poids in poids_details.items():
        print(f"  {nom}: {poids}")


    for entry in data:
        # Cas 1 : C'est un item
        if "stats" in entry:
            croum_factor=1
            global_sum = float(config_user.get('radar_stats', {}).get('global_sum_score', 1))
            estimation_resistance_percentage= scores_finaux["% Rés."]["desir"]/global_sum*20 * config_user.get('lvl', 200)/20
            if estimation_resistance_percentage>35:
                estimation_resistance_percentage=35
            resultat = calculer_score_stats(entry["stats"], scores_finaux, poids_details,config_user=config_user)
            if entry["nom"]=="Croum" or entry["nom"]=="El Scarador":
                if estimation_resistance_percentage>9 and estimation_resistance_percentage<29:
                    croum_factor=2*(1-(estimation_resistance_percentage/40-0.225))
                elif (estimation_resistance_percentage<29):
                    croum_factor=2
            elif("Bwak" in entry["nom"]):
                resultat=choisir_meilleure_stat(resultat)
            entry["score"] = resultat["total"]*croum_factor
            entry["repartition_stats"] = resultat["repartition"]
        
        # Cas 2 : C'est un bonus de panoplie
        elif "type" in entry and entry["type"] == "bonus_panoplie":
            for palier in entry.get("paliers", []):
                resultat_palier = calculer_score_stats(palier["bonus"], scores_finaux, poids_details,config_user=config_user)
                palier["score"] = resultat_palier["total"]
                palier["repartition_stats"] = resultat_palier["repartition"]

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    return calculer_poids_final(scores_finaux,poids_details)

def choisir_meilleure_stat(resultat):
    """
    Pour les items comme les Bwak qui ont plusieurs stats, on peut choisir de ne prendre en compte que la meilleure.
    Ici, on prend la stat qui apporte le plus de points (en valeur absolue) au score total.
    """
    if not resultat.get("details_points"):
        return resultat
    
    meilleure_stat = max(resultat["details_points"], key=lambda k: abs(resultat["details_points"][k]))
    meilleur_score = resultat["details_points"][meilleure_stat]
    
    # On remet à zéro les autres stats
    for stat in resultat["details_points"]:
        if stat != meilleure_stat:
            resultat["details_points"][stat] = 0
            resultat["repartition"][stat] = 0
    resultat["total"] = meilleur_score  # On retire l'impact des autres stats
    return resultat

def extraire_top_3_par_type(input_file, lvl_max, exclus=None):
    """
    Extrait le top 3 par type en filtrant par niveau et blacklist.
    'exclus' est maintenant une liste (ou set) venant de SQLite.
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Conversion en set pour une recherche instantanée (O(1) au lieu de O(n))
    items_exclus = set(exclus) if exclus else set()
    
    TYPES_ARMES = ["Épée", "Arc", "Dagues", "Bâton", "Marteau", "Pelle", "Hache", "Baguette", "Pioche", "Faux"]
    TYPES_CAPES = ["Cape", "Sac"]
    TYPES_MONTURE = ["Familier", "Dragodinde","Montilier"]
    
    # Filtrage : On exclut les items dans la blacklist SQLite
    items_valides = [
        entry for entry in data 
        if "stats" in entry 
        and entry.get("niveau", 0) <= lvl_max 
        and entry.get("nom") not in items_exclus
    ]

    classement_par_type = {}
    for item in items_valides:
        type_nom = item.get("type_objet", "Inconnu")
        if type_nom in TYPES_ARMES: type_nom = "Armes"
        elif type_nom in TYPES_CAPES: type_nom = "Capes/Sacs"
        elif type_nom in TYPES_MONTURE: type_nom = "Montures"
            
        if type_nom not in classement_par_type:
            classement_par_type[type_nom] = []
        classement_par_type[type_nom].append(item)
    
    resultats_finaux = {}
    for type_nom, liste_items in classement_par_type.items():
        liste_triee = sorted(liste_items, key=lambda x: x.get("score", 0), reverse=True)
        
        resultat = []
        i = 0
        # Sécurité : on s'arrête si on a 3 éléments OU si on a épuisé la liste
        while len(resultat) < 3 and i < len(liste_triee):
            it = liste_triee[i]
            sc_reel = it.get("score", 0)
            sc_arrondi = round(sc_reel, 2)
            
            # Calcul de la répartition
            rep = it.get("repartition_stats", {})
            points_par_stat = {stat: sc_reel * (pct / 100) for stat, pct in rep.items()}
            points_par_axe = mapper_points_vers_axes(points_par_stat)
            
            # VÉRIFICATION : Est-ce un doublon parfait du précédent ?
            # On vérifie d'abord si 'resultat' n'est pas vide pour éviter le crash
            if resultat and resultat[-1]["score"] == sc_arrondi:
                # On fusionne le nom sans incrémenter le compteur d'éléments
                if it.get("nom") not in resultat[-1]["nom"]: # Évite de doubler si l'item est déjà cité
                    resultat[-1]["nom"] += " / " + it.get("nom")
            else:
                # C'est un nouvel item ou le premier de la liste
                resultat.append({
                    "nom": it.get("nom"),
                    "niveau": it.get("niveau"),
                    "score": sc_arrondi,
                    "repartition": points_par_axe,
                    "image": it.get("image_url", ""),
                    "stats_completes": it.get("stats")
                })
            
            i += 1 # On passe à l'élément suivant dans liste_triee
            
        resultats_finaux[type_nom] = resultat
                
    return resultats_finaux

def calculer_stats_moyennes_relatives(json_file, lvl_min, lvl_max):
    """
    Calcule la moyenne de chaque stat divisée par la moyenne de la Vitalité
    pour tous les items dans la tranche de niveau [lvl_min, lvl_max].
    """
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 1. Filtrage des items par niveau
    items_tranche = [
        it for it in data 
        if "stats" in it and lvl_min <= it.get("niveau", 0) <= lvl_max
    ]

    if not items_tranche:
        print(f"Aucun item trouvé entre les niveaux {lvl_min} et {lvl_max}.")
        return None

    # 2. Accumulation des valeurs
    # On utilise un dictionnaire pour stocker la somme totale de chaque caractéristique
    sommes_stats = {}
    nb_items = len(items_tranche)

    for it in items_tranche:
        for stat in it["stats"]:
            nom = stat["nom"]
            # Utilisation de votre logique de jet maximum
            valeur = extraire_valeur_max(stat["valeur"])
            
            if nom not in sommes_stats:
                sommes_stats[nom] = 0
            sommes_stats[nom] += valeur

    # 3. Calcul des moyennes
    moyennes = {nom: (total / nb_items) for nom, total in sommes_stats.items()}

    # 4. Calcul des ratios par rapport à la Vitalité
    vitalite_moyenne = moyennes.get("Vitalité", 0)
    
    if vitalite_moyenne == 0:
        print("Erreur : La vitalité moyenne est de 0, impossible de calculer les ratios.")
        return None

    ratios_relatifs = {}
    for nom, moy in moyennes.items():
        # Ratio = Moyenne Stat / Moyenne Vitalité
        ratios_relatifs[nom] = round(moy / vitalite_moyenne, 4)

    return ratios_relatifs, vitalite_moyenne


def calculer_poids_final(scores_finaux,poids_details):
    """
    Calcule un poids final pour chaque caractéristique en multipliant le score de désirabilité par la rareté.
    Ce poids peut être utilisé pour ajuster l'importance de chaque stat dans d'autres calculs ou affichages.
    """
    poids_final = {}
    for nom, stats in scores_finaux.items():
        rarete = stats.get("rarete", 0)
        desir = stats.get("desir", 0)
        poids_final[nom] = round(rarete * desir, 4)

    for nom, poids in poids_details.items():
        poids_final[nom] = 0
        for cat, stats in poids.items():
            rarete = stats.get("rarete", 0)
            desir = stats.get("desir", 0)
            poids_final[nom] += round(rarete * desir, 4)

    return poids_final

# # --- EXEMPLE D'UTILISATION ---
# ratios, vit_moy = calculer_stats_moyennes_relatives('database_scores.json', 10, 200)

# if ratios:
#     print(f"Vitalité moyenne dans cette tranche : {vit_moy:.2f}")
#     print("\nPoids relatif des caractéristiques (Base Vitalité = 1.0) :")
#     # Tri par importance pour une meilleure lecture
#     for nom, ratio in sorted(ratios.items(), key=lambda x: x[1], reverse=True):
#         print(f"  - {nom} : {ratio}")
