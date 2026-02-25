import json
import pulp

def optimiser_stuff_complet(json_file, lvl_max, items_exclus=None):
    if items_exclus is None:
        items_exclus = ["Amulette Ementaire Deluxe", "Ruskauffe","La Racine Hagogue"]
    
    # Normalisation de la liste d'exclusion pour éviter les problèmes de casse/espaces
    blacklist = [nom.strip().lower() for nom in items_exclus]

    # 1. Chargement des données
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Filtrage initial
    items = [
        it for it in data 
        if "stats" in it 
        and it.get("niveau", 0) <= lvl_max
        and it.get("nom", "").strip().lower() not in blacklist
    ]
    sets_data = [s for s in data if s.get("type") == "bonus_panoplie"]

    TYPES_ARMES = [
        "Hache", "Pelle", "Marteau", "Épée", "Dagues", "Bâton", 
        "Baguette", "Arc", "Faux", "Pioche"
    ]

    TYPES_CAPE=[ "Cape", "Sac"]

    # 2. Création du modèle
    prob = pulp.LpProblem("Optimisation_Dofus", pulp.LpMaximize)

    # 3. Variables de décision (Items)
    item_vars = {}
    for i, it in enumerate(items):
        var_id = f"item_{i}"
        item_vars[var_id] = pulp.LpVariable(var_id, cat=pulp.LpBinary)
        it["_lp_var"] = var_id

    # 4. Variables de décision (Bonus Panoplies)
    # On ne crée des variables que pour les panoplies dont on possède au moins un item
    set_vars = {}
    panoplie_scores = {}
    for s in sets_data:
        p_name = s["nom_panoplie"].strip()
        items_dispo = [it for it in items if it.get("panoplie") == p_name]
        
        if items_dispo:
            set_vars[p_name] = {}
            panoplie_scores[p_name] = {p["nombre_items"]: p.get("score", 0) for p in s["paliers"]}
            for k in panoplie_scores[p_name]:
                v_name = f"pano_{p_name.replace(' ', '_')}_{k}"
                set_vars[p_name][k] = pulp.LpVariable(v_name, cat=pulp.LpBinary)

    # 5. CONTRAINTES DE SLOTS
    slots = {}
    for it in items:
        t_brut= it.get("type_objet", "Autre")
        if t_brut in TYPES_ARMES:
            t_final = "Arme"
        elif t_brut in TYPES_CAPE:
            t_final = "Cape"
        else:
            t_final = t_brut
        if t_final not in slots: slots[t_final] = []
        slots[t_final].append(it)

    for t, list_items in slots.items():
        # Limite : 1 par slot, sauf Anneaux (2)
        limite = 2 if "Anneau" in t else 1
        prob += pulp.lpSum([item_vars[it["_lp_var"]] for it in list_items]) <= limite

    # 6. CONTRAINTES D'ACTIVATION DES PANOPLIES
    for p_name, paliers in set_vars.items():
        items_in_set = [it for it in items if it.get("panoplie") == p_name]
        sum_x = pulp.lpSum([item_vars[it["_lp_var"]] for it in items_in_set])
        
        # On ne peut activer qu'un seul palier à la fois pour une panoplie
        prob += pulp.lpSum([paliers[k] for k in paliers]) <= 1
        
        # Le palier k ne peut être vrai que si on a au moins k items
        for k, y_var in paliers.items():
            prob += sum_x >= k * y_var

    # 7. FONCTION OBJECTIF
    score_items = pulp.lpSum([it.get("score", 0) * item_vars[it["_lp_var"]] for it in items])
    score_paliers = pulp.lpSum([
        panoplie_scores[p_name][k] * set_vars[p_name][k]
        for p_name in set_vars for k in set_vars[p_name]
    ])
    
    prob += score_items + score_paliers

    # 8. RÉSOLUTION
    # Utilise le solveur par défaut (CBC)
    prob.solve(pulp.PULP_CBC_CMD(msg=0))

    # 9. RÉCUPÉRATION DU STUFF IDÉAL
    if pulp.LpStatus[prob.status] == 'Optimal':
        stuff_final = [it for it in items if pulp.value(item_vars[it["_lp_var"]]) == 1]
        score_total = pulp.value(prob.objective)
        return stuff_final, score_total
    else:
        return None, 0

# --- EXECUTION ---
resultat, score = optimiser_stuff_complet('database_scores.json', 160)

if resultat:
    print(f"Meilleur score trouvé : {score:.2f}")
    for it in resultat:
        print(f"- {it['type_objet']}: {it['nom']} ({it['score']} pts)")