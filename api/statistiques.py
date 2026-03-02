import re
import json
import os
from optimiseur_top3 import charger_blacklist, mapper_points_vers_axes

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

def extraire_donnees(filename):
    chemin_json = filename
    
    if not os.path.exists(chemin_json):
        print("Erreur : Le fichier JSON n'existe pas encore.")
        return None

    with open(chemin_json, 'r') as f:
        data = json.load(f)
    
    desirabilite = { 
        item['caracteristique']: float(item['score_desirabilite']) 
        for item in data['radar_stats']['details'] 
    }
    return desirabilite

# --- 3. VOTRE LOGIQUE DE CALCUL ---
def executer_calcul_perso(config_user=None, filename=None):
    if config_user is None:
        print("Aucune configuration utilisateur fournie, utilisation des valeurs par défaut.")
    desir= extraire_donnees(filename)
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
    
    scores_finaux["Puissance"]= desir.get("Caractéristique(s) principale(s)", 1) * BASE_MULTIPLIERS["coeff_stat_principal"]
    scores_finaux["PA"]= desir.get("PA", 1) * BASE_MULTIPLIERS["coeff_pa"]
    scores_finaux["PM"]= desir.get("PM", 1) * BASE_MULTIPLIERS["coeff_pm"]
    scores_finaux["PO"]= desir.get("PO", 1) * BASE_MULTIPLIERS["coeff_po"]
    scores_finaux["Invocations"]= desir.get("Invocations", 1) * BASE_MULTIPLIERS["coeff_invoc"]
    scores_finaux["Initiative"]= desir.get("Initiative", 1) * BASE_MULTIPLIERS["coeff_ini"]
    scores_finaux["Fuite"]= desir.get("Fuite", 1) * BASE_MULTIPLIERS["coeff_fuite"]
    scores_finaux["Tacle"]= desir.get("Tacle", 1) * BASE_MULTIPLIERS["coeff_tacle"]
    scores_finaux["% Rés."]= desir.get("Résistances", 1) * BASE_MULTIPLIERS["coeff_res_pourcentage"]
    dommage_moyen=lvl*4*(1-desir.get("Résistances", 1)/20*0.35)
    scores_finaux["Rés. fixe"]= desir.get("Résistances", 1)*300/dommage_moyen * BASE_MULTIPLIERS["coeff_re_fixe"]
    scores_finaux["Esquive PA"]= desir.get("PA", 1)/desir.get("PM", 1) * BASE_MULTIPLIERS["coeff_re_pa/pm"]
    scores_finaux["Esquive PM"]= desir.get("PM", 1)/desir.get("PA", 1) * BASE_MULTIPLIERS["coeff_re_pa/pm"]
    scores_finaux["Dommages"]= desir.get("Caractéristique(s) principale(s)", 1)*20/moyenne_sort* BASE_MULTIPLIERS["coeff_do"]
    scores_finaux["Dommages Eau"]= desir.get("Caractéristique(s) principale(s)", 1)*20/moyenne_sort* BASE_MULTIPLIERS["coeff_do"] * CHANCE/SUM_CARAC
    scores_finaux["Dommages Terre"]= desir.get("Caractéristique(s) principale(s)", 1)*20/moyenne_sort* BASE_MULTIPLIERS["coeff_do"] * FORCE/1.5/SUM_CARAC
    scores_finaux["Dommages Neutre"]= desir.get("Caractéristique(s) principale(s)", 1)*20/moyenne_sort* BASE_MULTIPLIERS["coeff_do"] * FORCE/3/SUM_CARAC
    scores_finaux["Dommages Air"]= desir.get("Caractéristique(s) principale(s)", 1)*20/moyenne_sort* BASE_MULTIPLIERS["coeff_do"] * AGILITE/SUM_CARAC
    scores_finaux["Dommages Feu"]= desir.get("Caractéristique(s) principale(s)", 1)*20/moyenne_sort* BASE_MULTIPLIERS["coeff_do"] * INTELLIGENCE/SUM_CARAC
    scores_finaux["Soins"]= desir.get("Soins",1) * BASE_MULTIPLIERS["coeff_soins"]
    scores_finaux["Critique"]= desir.get("Critique", 1) * BASE_MULTIPLIERS["coeff_crit"]
    scores_finaux["Retrait PA"]= desir.get("Retrait PA", 1) * BASE_MULTIPLIERS["coeff_re_pa/pm"]
    scores_finaux["Retrait PM"]= desir.get("Retrait PM", 1) * BASE_MULTIPLIERS["coeff_re_pa/pm"]
    scores_finaux["Dommages Poussée"]= desir.get("Dommages Poussée", 1) * BASE_MULTIPLIERS["coeff_do"]
    
    poids_details = {
        "Intelligence": {
            "Intelligence": (desir.get("Caractéristique(s) principale(s)", 1) * BASE_MULTIPLIERS["coeff_stat_principal"] * INTELLIGENCE / SUM_CARAC),
            "Initiative": (desir.get("Initiative", 1) * BASE_MULTIPLIERS["coeff_ini"] * (1 - INTELLIGENCE)),
            "Soins": 0.1*scores_finaux["Soins"]
        },
        "Force": {
            "Force": (desir.get("Caractéristique(s) principale(s)", 1) * BASE_MULTIPLIERS["coeff_stat_principal"] * FORCE / SUM_CARAC),
            "Initiative": (desir.get("Initiative", 1) * BASE_MULTIPLIERS["coeff_ini"] * (1.5 - FORCE))
        },
        "Chance": {
            "Chance": (desir.get("Caractéristique(s) principale(s)", 1) * BASE_MULTIPLIERS["coeff_stat_principal"] * CHANCE / SUM_CARAC),
            "Initiative": (desir.get("Initiative", 1) * BASE_MULTIPLIERS["coeff_ini"] * (1 - CHANCE)),
            "Fuite": 0.1*scores_finaux["Fuite"]
        },
        "Agilité": {
            "Agilité": (desir.get("Caractéristique(s) principale(s)", 1) * BASE_MULTIPLIERS["coeff_stat_principal"] * AGILITE / SUM_CARAC),
            "Initiative": (desir.get("Initiative", 1) * BASE_MULTIPLIERS["coeff_ini"] * (1 - AGILITE)),
            "Tacle": 0.1*scores_finaux["Tacle"]
        },
        "Sagesse": {
            "Retrait PA": desir.get("Retrait PA", 1) * BASE_MULTIPLIERS["coeff_re_pa/pm"]/10,
            "Retrait PM": desir.get("Retrait PM", 1) * BASE_MULTIPLIERS["coeff_re_pa/pm"]/10,
            "Esquive PA": BASE_MULTIPLIERS["coeff_re_pa/pm"]/10,
            "Esquive PM": BASE_MULTIPLIERS["coeff_re_pa/pm"]/10
        },
        "Dommages Critique": {
            "Dommages": scores_finaux["Dommages"] * (desir.get("Critique", 1)/10+0.2)*(0.5+(1-(desir.get("Critique", 1)/10+0.2))/2),
            "Critique": scores_finaux["Dommages"] * (desir.get("Critique", 1)/10+0.2)*(desir.get("Critique", 1)/10+0.2)/2
        }
    }
    
    print("Scores finaux calculés :")
    for stat, score in scores_finaux.items():
        print(f"  - {stat} : {score:.2f}")
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

def calculer_score_stats(liste_stats, scores_finaux, poids_details=None):
    """
    Calcule le score total en intégrant les malus.
    Les malus impactent négativement le score total et la répartition.
    """
    if not scores_finaux:
        return {"total": 0, "repartition": {}}

    total_score = 0
    details_points = {}

    for stat in liste_stats:
        nom = stat['nom']
        # Attention : extraire_valeur_max doit bien retourner une valeur négative si c'est un malus
        val = extraire_valeur_max(stat['valeur']) 
        points_cette_stat = 0
        categorie = None

        # --- LOGIQUE DE MAPPING ---
        if nom in scores_finaux:
            categorie = nom
            points_cette_stat = val * scores_finaux[nom]
        elif "% Rés." in nom:
            categorie = "% Rés."
            poids = scores_finaux.get("% Rés.", 0)
            points_cette_stat = val * poids * (0.5 if "Neutre" in nom else 1.0)
        elif "Rés." in nom and "%" not in nom:
            categorie = "Rés. fixe"
            poids = scores_finaux.get("Rés. fixe", 0)
            points_cette_stat = val * poids * (0.5 if "Neutre" in nom else 1.0)
        elif "Vitalité" in nom:
            categorie = "Vitalité"
            # Si tu n'as pas de poids pour la vita, on considère 1 par défaut ou 0
            points_cette_stat = val * scores_finaux.get("Vitalité", 1)
        elif "Dommages Critique" in nom:
            if scores_finaux.get("Critique", 0)/BASE_MULTIPLIERS["coeff_crit"] >=8:
                categorie="Dommages"
                points_cette_stat = val * scores_finaux["Dommages"]*0.5
                total_score += points_cette_stat
                details_points[categorie] = details_points.get(categorie, 0) + points_cette_stat
                categorie="Critique"
                points_cette_stat = val* scores_finaux["Dommages"]*0.5
                total_score += points_cette_stat
                details_points[categorie] = details_points.get(categorie, 0) + points_cette_stat
            else:
                for cat, pts in poids_details[nom].items():
                    categorie = cat
                    points_cette_stat = val * pts
                    if categorie and points_cette_stat != 0:
                        total_score += points_cette_stat
                        details_points[categorie] = details_points.get(categorie, 0) + points_cette_stat
        elif nom in poids_details:
            for cat, pts in poids_details[nom].items():
                if cat in scores_finaux:
                    categorie = cat
                    points_cette_stat = val * pts
                    if categorie and points_cette_stat != 0:
                        total_score += points_cette_stat
                        details_points[categorie] = details_points.get(categorie, 0) + points_cette_stat

        # --- ACCUMULATION ---
        if categorie and points_cette_stat != 0 and "Dommages Critique" not in nom and nom not in poids_details:
            total_score += points_cette_stat
            details_points[categorie] = details_points.get(categorie, 0) + points_cette_stat
    # --- CALCUL DES POURCENTAGES ---
    repartition = {}
    
    # On évite la division par zéro. 
    # Note : Si total_score est négatif, l'item est globalement "mauvais".
    if total_score != 0:
        for cat, pts in details_points.items():
            # Si pts est négatif et total_score positif -> % négatif
            # Si pts est positif et total_score positif -> % positif
            pourcentage = (pts / total_score) * 100
            repartition[cat] = round(pourcentage, 1)

    return {
        "total": round(total_score, 2),
        "repartition": repartition
    }


def enrichir_base_de_donnees(input_file, output_file, filename, config_user=None):
    """Lit le JSON, calcule les scores/répartitions et sauvegarde."""
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    scores_finaux,poids_details = executer_calcul_perso(config_user=config_user, filename=filename)

    for entry in data:
        # Cas 1 : C'est un item
        if "stats" in entry:
            resultat = calculer_score_stats(entry["stats"], scores_finaux, poids_details)
            entry["score"] = resultat["total"]
            entry["repartition_stats"] = resultat["repartition"] # Nouveau champ
        
        # Cas 2 : C'est un bonus de panoplie
        elif "type" in entry and entry["type"] == "bonus_panoplie":
            for palier in entry.get("paliers", []):
                resultat_palier = calculer_score_stats(palier["bonus"], scores_finaux, poids_details)
                palier["score"] = resultat_palier["total"]
                palier["repartition_stats"] = resultat_palier["repartition"]

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)



def extraire_top_3_par_type(input_file, lvl_max):
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    items_exclus = charger_blacklist()
    print("Items exclus chargés :", items_exclus)
    # 1. Listes de regroupement
    TYPES_ARMES = [
        "Épée", "Arc", "Dagues", "Bâton", "Marteau", 
        "Pelle", "Hache", "Baguette", "Pioche", "Faux"
    ]
    TYPES_CAPES = ["Cape", "Sac"]
    
    # 2. Filtrage (On garde les items avec stats et sous le niveau max)
    items_valides = [
        entry for entry in data 
        if "stats" in entry and entry.get("niveau", 0) <= lvl_max and entry.get("nom", "") not in items_exclus
    ]
    print(f"{len(items_valides)} items valides trouvés pour le niveau {lvl_max} après filtrage.")
    # 3. Groupement par type
    classement_par_type = {}
    for item in items_valides:
        type_nom = item.get("type_objet", "Inconnu")
        
        # Logique de regroupement
        if type_nom in TYPES_ARMES:
            type_nom = "Armes"
        elif type_nom in TYPES_CAPES:
            type_nom = "Capes/Sacs"
            
        if type_nom not in classement_par_type:
            classement_par_type[type_nom] = []
        classement_par_type[type_nom].append(item)
    
    # 4. Tri et formatage des résultats (Top 5 comme dans ton code)
    resultats_finaux = {}
    for type_nom, liste_items in classement_par_type.items():
        # Tri par score décroissant
        liste_triee = sorted(liste_items, key=lambda x: x.get("score", 0), reverse=True)
        resultat=[]
        for it in liste_triee[:3]:
            points_par_stat = {}
            rep = it.get("repartition_stats", {})
            sc=it.get("score", 0)
            for stat, pct in rep.items():
                points = sc * (pct / 100)
                points_par_stat[stat] = points

            points_par_axe = mapper_points_vers_axes(points_par_stat)
            # On construit un objet propre pour le frontend
            resultat.append({
                    "nom": it.get("nom"),
                    "niveau": it.get("niveau"),
                    "score": it.get("score", 0),
                    "repartition": points_par_axe, # Les fameux % par stat
                    "image": it.get("image_url", ""), # Si tu as les images
                    "stats_completes": it.get("stats") # Pour afficher le détail au survol
                })
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

# # --- EXEMPLE D'UTILISATION ---
# ratios, vit_moy = calculer_stats_moyennes_relatives('database_scores.json', 10, 200)

# if ratios:
#     print(f"Vitalité moyenne dans cette tranche : {vit_moy:.2f}")
#     print("\nPoids relatif des caractéristiques (Base Vitalité = 1.0) :")
#     # Tri par importance pour une meilleure lecture
#     for nom, ratio in sorted(ratios.items(), key=lambda x: x[1], reverse=True):
#         print(f"  - {nom} : {ratio}")
