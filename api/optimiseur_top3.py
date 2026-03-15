import json
import pulp
import os


    
def extraire_top_n_solutions(json_file, lvl_max, n=3, items_exclus=None):
    # Chargement initial identique
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    blacklist = {nom.strip().lower() for nom in items_exclus} if items_exclus else set()    
    items = [it for it in data if "stats" in it and it.get("niveau", 0) <= lvl_max and it.get("nom", "").strip().lower() not in blacklist]
    sets_data = [s for s in data if s.get("type") == "bonus_panoplie"]
    TYPES_ARMES = ["Hache", "Pelle", "Marteau", "Épée", "Dagues", "Bâton", "Baguette", "Arc", "Faux", "Pioche"]
    TYPES_CAPE=[ "Cape", "Sac"]
    TYPES_MONTURE = ["Familier", "Dragodinde","Montilier"]

    # Création du problème de base
    prob = pulp.LpProblem("Optimisation_Top_N", pulp.LpMaximize)

    # Variables de décision
    item_vars = {f"item_{i}": pulp.LpVariable(f"item_{i}", cat=pulp.LpBinary) for i, it in enumerate(items)}
    for i, it in enumerate(items):
        it["_lp_var"] = f"item_{i}"

    set_vars = {}
    panoplie_scores = {}
    panoplie_repartitions = {}
    for s in sets_data:
        p_name = s["nom_panoplie"].strip()
        items_dispo = [it for it in items if it.get("panoplie") == p_name]
        if items_dispo:
            set_vars[p_name] = {}
            p_scores = {p["nombre_items"]: p.get("score", 0) for p in s["paliers"]}
            panoplie_scores[p_name] = p_scores
            p_reps = {p["nombre_items"]: p.get("repartition_stats", {}) for p in s["paliers"]}
            panoplie_repartitions[p_name] = p_reps
            for k in p_scores:
                v_name = f"pano_{p_name.replace(' ', '_')}_{k}"
                set_vars[p_name][k] = pulp.LpVariable(v_name, cat=pulp.LpBinary)

    # Contraintes de Slots
    slots = {}
    for it in items:
        if it.get("type_objet") in TYPES_ARMES:
            t_final = "Arme"
        elif it.get("type_objet") in TYPES_CAPE:
            t_final = "Cape"
        elif it.get("type_objet") in TYPES_MONTURE:
            t_final = "Monture"
        else:
            t_final = it.get("type_objet")
        if t_final not in slots: slots[t_final] = []
        slots[t_final].append(it)

    for t, list_items in slots.items():
        limite = 2 if "Anneau" in t else (6 if any(x in t for x in ["Dofus", "Trophée"]) else 1)
        prob += pulp.lpSum([item_vars[it["_lp_var"]] for it in list_items]) <= limite

    # Contraintes Panoplies
    for p_name, paliers in set_vars.items():
        items_in_set = [it for it in items if it.get("panoplie") == p_name]
        sum_x = pulp.lpSum([item_vars[it["_lp_var"]] for it in items_in_set])
        prob += pulp.lpSum([paliers[k] for k in paliers]) <= 1
        for k, y_var in paliers.items():
            prob += sum_x >= k * y_var

    # Objectif
    score_items = pulp.lpSum([it.get("score", 0) * item_vars[it["_lp_var"]] for it in items])
    score_paliers = pulp.lpSum([panoplie_scores[p_name][k] * set_vars[p_name][k] for p_name in set_vars for k in set_vars[p_name]])
    prob += score_items + score_paliers

    solutions_trouvees = []
    scores_vus = {}
    iteration = 0
    max_iterations = 50

    while len(solutions_trouvees) < 5 and iteration < max_iterations:
        iteration += 1
        prob.solve(pulp.PULP_CBC_CMD(msg=0))
        
        if pulp.LpStatus[prob.status] == 'Optimal':
            stuff_actuel = [it for it in items if pulp.value(item_vars[it["_lp_var"]]) == 1]
            
            # Somme des points réels par caractéristique
            points_par_stat = {}
            score_total_reel = 0 

            # A. Calcul pour les Items
            for it in stuff_actuel:
                sc = it.get("score", 0)
                rep = it.get("repartition_stats", {})
                score_total_reel += sc
                for stat, pct in rep.items():
                    # Points = Score_Item * (%_Stat / 100)
                    points = sc * (pct / 100)
                    points_par_stat[stat] = points_par_stat.get(stat, 0) + points

            # B. Calcul pour les Bonus de Panoplies
            for p_name in set_vars:
                for k in set_vars[p_name]:
                    if pulp.value(set_vars[p_name][k]) == 1:
                        sc = panoplie_scores[p_name][k]
                        rep = panoplie_repartitions[p_name][k]
                        score_total_reel += sc
                        for stat, pct in rep.items():
                            points = sc * (pct / 100)
                            points_par_stat[stat] = points_par_stat.get(stat, 0) + points
            
            score_arrondi = round(score_total_reel, 2)
            points_par_axe = mapper_points_vers_axes(points_par_stat)
            cle_unique = (score_arrondi, tuple(sorted(points_par_axe.items())))
            if cle_unique not in scores_vus:

                # D. Sauvegarde de la solution
                solutions_trouvees.append({
                    "stuff": stuff_actuel,
                    "score": round(score_total_reel, 2),
                    "repartition_axes": points_par_axe
                })
                scores_vus[cle_unique] = len(solutions_trouvees) - 1

            # Contrainte d'exclusion pour trouver la solution suivante
            current_vars = [item_vars[it["_lp_var"]] for it in stuff_actuel]
            prob += pulp.lpSum(current_vars) <= len(current_vars) - 1
        else:
            break 

    return solutions_trouvees


def mapper_points_vers_axes(points_par_stat):
    """
    Regroupe les points des caractéristiques précises vers les axes du radar
    en utilisant un dictionnaire de mapping.
    """
    mapping = {
        "Caractéristique(s) principale(s)": ["Force", "Intelligence", "Agilité", "Chance", "Dommages", "Dommages Terre", "Dommages Feu", "Dommages Eau", "Dommages Air", "Dommages Neutre", "Puissance"],
        "Initiative": ["Initiative"],
        "Dommages Poussée": ["Dommages Poussée"],
        "Soins": ["Soins"],
        "Critique": ["Critique"],
        "Retrait PA": ["Retrait PA"],
        "Retrait PM": ["Retrait PM"],
        "Résistances": ["% Rés.", "Rés. fixe"],
        "Vitalité": ["Vitalité"],
        "PA": ["PA", "Esquive PA"],
        "PM": ["PM", "Esquive PM"],
        "PO": ["PO"],
        "Invocations": ["Invocations"],
        "Tacle": ["Tacle"],
        "Fuite": ["Fuite"]
    }

    # Initialisation des points par axe à 0
    # On utilise les clés du mapping pour s'assurer que tous nos axes existent
    points_par_axe = {axe: 0 for axe in mapping.keys()}

    # Parcours des statistiques reçues
    for stat_nom, points in points_par_stat.items():
        # On cherche à quel axe appartient la statistique 'stat_nom'
        for axe, liste_stats_associees in mapping.items():
            if stat_nom in liste_stats_associees:
                points_par_axe[axe] += points
                break # On a trouvé l'axe, on passe à la stat suivante
    return points_par_axe