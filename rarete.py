import json
import numpy as np
from scipy.optimize import minimize
import re

# Liste des 25 catégories cibles
TARGET_CATEGORIES = [
    'vitalite', 'force', 'intelligence', 'agilite', 'chance', 'puissance', 
    'sagesse', 'pa', 'pm', 'po', 'invocation', 'dommages', 'dommages_eau','dommages_feu','dommages_terre','dommages_air','dommages_neutre',
    'fuite', 'tacle', 'ini', 'critique', 'dommages_critique', 'dommages_poussee','prospection', 'soin',
    'res_p_terre','res_p_feu','res_p_air','res_p_eau','res_p_neutre', 'res_f_terre', 'res_f_feu', 'res_f_air', 'res_f_eau', 'res_f_neutre','re_crit', 're_pou', 'esquive_pa','esquive_pm', 'retrait_pa','retrait_pm'
]

def extraire_valeur_max(valeur_str):
    if isinstance(valeur_str, (int, float)): return valeur_str
    nombres = re.findall(r'-?\d+', str(valeur_str))
    if not nombres: return 0
    vals = [int(n) for n in nombres]
    return sorted(vals, key=abs, reverse=True)[0]

def mapper_stats_item(stats_json):
    """Transforme les stats brutes du JSON vers les 25 catégories cibles."""
    item_mapped = {cat: 0 for cat in TARGET_CATEGORIES}
    
    mapping_direct = {
        'Vitalité': 'vitalite', 'Force': 'force', 'Intelligence': 'intelligence',
        'Agilité': 'agilite', 'Chance': 'chance', 'Puissance': 'puissance',
        'Sagesse': 'sagesse', 'PA': 'pa', 'PM': 'pm', 'PO': 'po',
        'Invocation': 'invocation', 'Dommages': 'dommages', 'Dommages Eau': 'dommages_eau','Dommages Feu': 'dommages_feu','Dommages Terre': 'dommages_terre','Dommages Air': 'dommages_air', 'Dommages Neutre': 'dommages_neutre',
        'Fuite': 'fuite', 'Tacle': 'tacle', 'Initiative': 'ini', 
        'Critique': 'critique', 'Dommages Critique': 'dommages_critique',
        'Dommages Poussée': 'dommages_poussee', 'Rés. Critique': 're_crit', 'Prospection': 'prospection', 'Soin': 'soin',
        'Rés. Poussée': 're_pou', 'Esquive PA': 'esquive_pa','Esquive PM': 'esquive_pm', 'Retrait PA': 'retrait_pa','Retrait PM': 'retrait_pm','Rés. Terre': 'res_p_terre','Rés. Feu': 'res_p_feu','Rés. Air': 'res_p_air','Rés. Eau': 'res_p_eau','Rés. Neutre': 'res_p_neutre',
        'Résistance Terre': 'res_f_terre','Résistance Feu': 'res_f_feu','Résistance Air': 'res_f_air','Résistance Eau': 'res_f_eau','Résistance Neutre': 'res_f_neutre'
    }

    for s in stats_json:
        nom = s['nom']
        val = extraire_valeur_max(s['valeur'])
        
        if nom in mapping_direct:
            item_mapped[mapping_direct[nom]] += val
            
    return item_mapped

def calculer_rarete_optimale(json_file, lvl_min, lvl_max):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Filtrage et groupement
    items_par_type = {}
    items_valides = [it for it in data if "stats" in it and lvl_min <= it.get("niveau", 0) <= lvl_max]
    
    for it in items_valides:
        t = it.get("type_objet", "Autre")
        if t not in items_par_type: items_par_type[t] = []
        items_par_type[t].append(mapper_stats_item(it["stats"]))

    # Création des matrices par type (uniquement si au moins 2 items)
    matrices_types = []
    for t, liste_it in items_par_type.items():
        if len(liste_it) >= 2:
            matrices_types.append(np.array([[it[cat] for cat in TARGET_CATEGORIES] for it in liste_it]))

    if not matrices_types:
        return "Pas assez de données pour l'analyse."

    # Fonction à minimiser : Somme des variances intra-type
    def objective(w):
        total_var = 0
        for X in matrices_types:
            scores = np.dot(X, w)
            total_var += np.var(scores)
        return total_var
    
    # Au lieu de mettre 1 partout, on donne des ordres de grandeur Dofus
    w_init = np.array([1.0 if c == 'vitalite' else 5.0 for c in TARGET_CATEGORIES])
    idx_pa, idx_pm, idx_po , idx_invoc, idx_crit,idx_soin= TARGET_CATEGORIES.index('pa'), TARGET_CATEGORIES.index('pm'), TARGET_CATEGORIES.index('po'), TARGET_CATEGORIES.index('invocation'), TARGET_CATEGORIES.index('critique'), TARGET_CATEGORIES.index('soin')
    w_init[idx_pa], w_init[idx_pm], w_init[idx_po], w_init[idx_invoc], w_init[idx_crit], w_init[idx_soin] = 500.0, 450.0, 250.0, 150.0, 50.0, 50.0

    # Contraintes : Vitalité (index 0) = 1, et tous les poids >= 0
    cons = ({'type': 'eq', 'fun': lambda w: w[0] - 1.0})
    bounds = [(0, None) for _ in range(len(TARGET_CATEGORIES))]
    w_init = np.ones(len(TARGET_CATEGORIES))

    res = minimize(objective, w_init, method='SLSQP', bounds=bounds, constraints=cons)

    if res.success:
        return {TARGET_CATEGORIES[i]: round(res.x[i], 2) for i in range(len(TARGET_CATEGORIES))}
    return "L'optimisation a échoué."

# --- EXECUTION ---
resultats = calculer_rarete_optimale('database_scores.json', 120,150)
print(json.dumps(resultats, indent=4))