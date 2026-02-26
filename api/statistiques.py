import re
import json
import os

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
    scores_finaux["Sagesse"]= (desir.get("Retrait PA", 1)+ desir.get("Retrait PM", 1)) * BASE_MULTIPLIERS["coeff_sagesse"] + BASE_MULTIPLIERS["coeff_re_pa/pm"]/10
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
    if(desir.get("Critique", 0) < 8):
        scores_finaux["Dommages Critique"]= (desir.get("Critique", 1)/10+0.2)*scores_finaux["Dommages"]
    else:
        scores_finaux["Dommages Critique"]= scores_finaux["Dommages"]
    scores_finaux["Soins"]= desir.get("Soins",1) * BASE_MULTIPLIERS["coeff_soins"]
    scores_finaux["Critique"]= desir.get("Critique", 1) * BASE_MULTIPLIERS["coeff_crit"]
    scores_finaux["Retrait PA"]= desir.get("Retrait PA", 1) * BASE_MULTIPLIERS["coeff_re_pa/pm"]
    scores_finaux["Retrait PM"]= desir.get("Retrait PM", 1) * BASE_MULTIPLIERS["coeff_re_pa/pm"]
    scores_finaux["Chance"] = desir.get("Caractéristique(s) principale(s)", 1) * BASE_MULTIPLIERS["coeff_stat_principal"]*CHANCE/SUM_CARAC + desir.get("Initiative", 1) * BASE_MULTIPLIERS["coeff_ini"]*(1-CHANCE) + scores_finaux["Fuite"]*0.1
    scores_finaux["Agilité"] = desir.get("Caractéristique(s) principale(s)", 1) * BASE_MULTIPLIERS["coeff_stat_principal"]*AGILITE/SUM_CARAC+ desir.get("Initiative", 1) * BASE_MULTIPLIERS["coeff_ini"]*(1-AGILITE) + scores_finaux["Tacle"]*0.1
    scores_finaux["Force"] = desir.get("Caractéristique(s) principale(s)", 1) * BASE_MULTIPLIERS["coeff_stat_principal"]*FORCE/SUM_CARAC + desir.get("Initiative", 1) * BASE_MULTIPLIERS["coeff_ini"]*(1.5-FORCE)
    scores_finaux["Intelligence"] = desir.get("Caractéristique(s) principale(s)", 1) * BASE_MULTIPLIERS["coeff_stat_principal"]*INTELLIGENCE/SUM_CARAC + desir.get("Initiative", 1) * BASE_MULTIPLIERS["coeff_ini"]*(1-INTELLIGENCE) + scores_finaux["Soins"]*0.1
    print("Scores finaux calculés :")
    for stat, score in scores_finaux.items():
        print(f"  - {stat} : {score:.2f}")
    return scores_finaux

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

def calculer_score_stats(liste_stats, scores_finaux):
    """
    Calcule le score total d'un item en utilisant le dictionnaire 
    scores_finaux qui contient les poids par caractéristique.
    """
    # 1. On récupère le dictionnaire généré dynamiquement
    # contenant les clés comme "Force", "PA", "% Rés.", etc.
    
    
    if not scores_finaux:
        return 0

    total_score = 0

    for stat in liste_stats:
        nom = stat['nom'] # Nom exact de la DB (ex: "Force", "% Rés. Air")
        val = extraire_valeur_max(stat['valeur'])
        
        # 2. LOGIQUE DE MAPPING ET CALCUL
        
        # Cas A : Correspondance exacte (PA, PM, Force, Dommages Eau, Fuite, etc.)
        if nom in scores_finaux:
            total_score += val * scores_finaux[nom]
            
        # Cas B : Les Résistances en % (Toutes les résistances utilisent le même score "% Rés.")
        elif "% Rés." in nom:
            if "Neutre" in nom:
                total_score += val * scores_finaux.get("% Rés.", 0) * 0.5  # Moins important que les autres résistances
            else:
                total_score += val * scores_finaux.get("% Rés.", 0)
            
        # Cas C : Les Résistances fixes (Rés. Air, Rés. Eau, etc. -> utilisent "Rés. fixe")
        elif "Rés." in nom and "%" not in nom:
            if "Neutre" in nom:
                total_score += val * scores_finaux.get("Rés. fixe", 0) * 0.5  # Moins important que les autres résistances
            else:
                total_score += val * scores_finaux.get("Rés. fixe", 0)
            
        # Cas E : La Vitalité (si elle est nommée "Vitalité" dans ta DB)
        elif "Vitalité" in nom:
            # Si tu n'as pas défini de score pour la Vitalité dans scores_finaux,
            # on peut mettre un score par défaut ou le récupérer via une clé "Vitalité"
            total_score += val

    return round(total_score, 2)


def enrichir_base_de_donnees(input_file, output_file, filename, config_user=None):
    """Lit le JSON, calcule les scores et sauvegarde le résultat."""
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    scores_finaux = executer_calcul_perso(config_user=config_user, filename=filename)

    for entry in data:
        # Cas 1 : C'est un item
        if "stats" in entry:
            entry["score"] = calculer_score_stats(entry["stats"], scores_finaux)
        
        # Cas 2 : C'est un bonus de panoplie
        elif "type" in entry and entry["type"] == "bonus_panoplie":
            for palier in entry.get("paliers", []):
                palier["score"] = calculer_score_stats(palier["bonus"], scores_finaux)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def extraire_top_3_par_type(input_file, lvl_max):
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 1. Liste des types à regrouper sous l'appellation "Armes"
    # Ajuste cette liste selon les noms exacts dans ta database
    TYPES_ARMES = [
        "Épée", "Arc", "Dagues", "Bâton", "Marteau", 
        "Pelle", "Hache", "Baguette", "Pioche", "Faux"
    ]
    
    TYPES_CAPES=[ "Cape", "Sac"]
    # 2. Filtrage
    items_valides = [
        entry for entry in data 
        if "stats" in entry and entry.get("niveau", 0) <= lvl_max
    ]
    
    # 3. Groupement avec logique de regroupement des armes
    classement_par_type = {}
    for item in items_valides:
        type_nom = item.get("type_objet", "Inconnu")
        
        # SI le type est une arme, on change son nom de groupe pour "Armes"
        if type_nom in TYPES_ARMES:
            type_nom = "Armes"
            
        if type_nom in TYPES_CAPES:
            type_nom = "Capes/Sacs"
            
        if type_nom not in classement_par_type:
            classement_par_type[type_nom] = []
        classement_par_type[type_nom].append(item)
    
    # 4. Tri et sélection du Top 3 (Strict)
    resultats_finaux = {}
    for type_nom, liste_items in classement_par_type.items():
        # Tri par score (du plus haut au plus bas)
        liste_triee = sorted(liste_items, key=lambda x: x.get("score", 0), reverse=True)
        
        # On ne garde que les 3 meilleurs
        resultats_finaux[type_nom] = liste_triee[:5]
        
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
