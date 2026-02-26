import json
import pulp

def extraire_top_n_solutions(json_file, lvl_max, n=3, items_exclus=None):
    if items_exclus is None:
        items_exclus = []
    
    # Chargement initial identique
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    blacklist = [nom.strip().lower() for nom in items_exclus]
    items = [it for it in data if "stats" in it and it.get("niveau", 0) <= lvl_max and it.get("nom", "").strip().lower() not in blacklist]
    sets_data = [s for s in data if s.get("type") == "bonus_panoplie"]
    TYPES_ARMES = ["Hache", "Pelle", "Marteau", "Épée", "Dagues", "Bâton", "Baguette", "Arc", "Faux", "Pioche"]
    TYPES_CAPE=[ "Cape", "Sac"]

    # Création du problème de base
    prob = pulp.LpProblem("Optimisation_Top_N", pulp.LpMaximize)

    # Variables de décision
    item_vars = {f"item_{i}": pulp.LpVariable(f"item_{i}", cat=pulp.LpBinary) for i, it in enumerate(items)}
    for i, it in enumerate(items):
        it["_lp_var"] = f"item_{i}"

    set_vars = {}
    panoplie_scores = {}
    for s in sets_data:
        p_name = s["nom_panoplie"].strip()
        items_dispo = [it for it in items if it.get("panoplie") == p_name]
        if items_dispo:
            set_vars[p_name] = {}
            p_scores = {p["nombre_items"]: p.get("score", 0) for p in s["paliers"]}
            panoplie_scores[p_name] = p_scores
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

    for iteration in range(n):
        prob.solve(pulp.PULP_CBC_CMD(msg=0))
        
        if pulp.LpStatus[prob.status] == 'Optimal':
            # 1. On récupère les items de cette solution
            stuff_actuel = [it for it in items if pulp.value(item_vars[it["_lp_var"]]) == 1]
            score_actuel = pulp.value(prob.objective)
            solutions_trouvees.append((stuff_actuel, score_actuel))
            
            # 2. CONTRAINTE D'EXCLUSION : On interdit de reprendre exactement TOUS ces items
            # La somme des variables de la solution actuelle doit être inférieure au nombre d'items choisis
            current_vars = [item_vars[it["_lp_var"]] for it in stuff_actuel]
            prob += pulp.lpSum(current_vars) <= len(current_vars) - 1
        else:
            break # Plus de solution possible
    print(f"Solutions trouvées : {len(solutions_trouvees)}")
    return solutions_trouvees
