import json
import pulp
import os
from api.statistiques import  mapper_points_vers_axes

CONTRAINTES={
    "PA": 5,
    "PM": 3,
    "PO": 6,
    "Invocations": 5,
    "% Rés. Neutre": 35,
    "% Rés. Terre": 35,
    "% Rés. Feu": 35,
    "% Rés. Eau": 35,
    "% Rés. Air": 35
}


    
def extraire_top_n_solutions(json_file, lvl_max, poids,n=3, items_exclus=None):
    # Chargement initial identique
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    blacklist = {nom.strip().lower() for nom in items_exclus} if items_exclus else set()    
    items = [it for it in data if "stats" in it and it.get("niveau", 0) <= lvl_max and it.get("nom", "").strip().lower() not in blacklist]
    sets_data = [s for s in data if s.get("type") == "bonus_panoplie"]
    TYPES_ARMES = ["Hache", "Pelle", "Marteau", "Épée", "Dagues", "Bâton", "Baguette", "Arc", "Faux", "Pioche"]
    TYPES_CAPE=[ "Cape", "Sac"]
    TYPES_MONTURE = ["Familier", "Dragodinde","Montilier"]
    TYPES_TROPHEES = ["Trophée","Dofus"]

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
            p_scores = {p["nombre_items"]: {"score":p.get("score", 0), "bonus": p.get("bonus", {})} for p in s["paliers"]}
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
        elif it.get("type_objet") in TYPES_TROPHEES:
            t_final = "Trophée/Dofus"
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
    excess_vars = {
        stat: pulp.LpVariable(f"excess_{stat}", lowBound=0, cat=pulp.LpContinuous)
        for stat in CONTRAINTES.keys()
    }
    # 3. Calcul de la somme brute des stats (Items + Paliers)
    penalites = []

    for stat, limite in CONTRAINTES.items():
        # Somme sur les items
        somme_items = pulp.lpSum([
            it.get("stats", {}).get(stat, 0) * item_vars[it["_lp_var"]] 
            for it in items
        ])
        
        # Somme sur les paliers de panoplie
        somme_paliers = pulp.lpSum([
            panoplie_scores[p_name][k].get("stats", {}).get(stat, 0) * set_vars[p_name][k]
            for p_name in set_vars for k in set_vars[p_name]
        ])

        # Ajustement de la limite pour les BL
        limite_eff = limite + 1 if (stat == "PA" and lvl_max < 100) else limite

        # CONTRAINTE D'EXCÈS : excess_stat >= (Total - Limite)
        # Si Total < Limite, excess_stat vaudra 0 (grâce au lowBound=0 et à la maximisation)
        prob += excess_vars[stat] >= (somme_items + somme_paliers) - limite_eff

        # On calcule la pénalité : Excès * Poids de la stat
        if "Rés" not in stat:
            poid = poids.get(stat, 1) # Par défaut 1 si non trouvé
        else:
            poid=poids.get("% Rés.")
        penalites.append(excess_vars[stat] * poid)

    # 4. DÉFINITION DE L'OBJECTIF FINAL
    score_items = pulp.lpSum([it.get("score", 0) * item_vars[it["_lp_var"]] for it in items])
    score_paliers = pulp.lpSum([panoplie_scores[p_name][k]["score"] * set_vars[p_name][k] for p_name in set_vars for k in set_vars[p_name]])

    # Objectif = Gain brut - Pénalités d'excès
    prob.setObjective(score_items + score_paliers - pulp.lpSum(penalites))

    solutions_trouvees = []
    scores_vus = {}
    iteration = 0
    max_iterations = 50
    items_vus=[]
    prob += pulp.lpSum(item_vars.values()) >= 10, "Min_Items"

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
                        sc = panoplie_scores[p_name][k]["score"]
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
    
    for solution in solutions_trouvees:
        for it in solution["stuff"]:
                    sc = it.get("score", 0)
                    rep = it.get("repartition_stats", {})
                    if it["nom"] not in items_vus:
                        points_par_stat_it = {stat: sc * (pct / 100) for stat, pct in rep.items()}
                        points_par_axe_it = mapper_points_vers_axes(points_par_stat_it)
                        it["repartition_stats"]= points_par_axe_it
                        items_vus.append(it["nom"])
    return solutions_trouvees


