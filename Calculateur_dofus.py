import re

lvl=170
moyenne_sort=30
coeff_stat_principal = 4.5
coeff_sagesse = 0.4
coeff_res_pourcentage= 30
coeff_re_fixe=((coeff_res_pourcentage/12)/(lvl/100))*4
coeff_ini=1/2
coeff_stat_secondaire = coeff_ini
coeff_dommages=((coeff_stat_principal/2)/moyenne_sort)*25*10*4/5
coeff_po=200
coeff_invoc=250
coeff_pm=500
coeff_pa=1200
coeff_fuite=10
coeff_tacle=0
coeff_retrait=0
coeff_esquive=4
coeff_crit=10
coeff_do_crit=((coeff_crit/20)*(coeff_dommages/10))*10
print( coeff_do_crit)
coeff_do_pou=0

texte_item = """
151 à 200 Vitalité

31 à 40 Intelligence

31 à 40 Chance

31 à 40 Sagesse

2 à 3 Critique

1 PO

8 à 12 Dommages Feu

8 à 12 Dommages Eau

4 à 5 Soin

11 à 15 Prospection

3 à 4 Retrait PM

7 à 10 Rés. Critique

7 à 10 Rés. Neutre
"""

stats = {
    'vitalite': 0,
    'force': 0,
    'intelligence': 0,
    'agilite': 0,
    'chance': 0,
    'puissance': 0,
    'sagesse': 0,
    'pa': 0,
    'pm': 0,
    'po': 0,
    'invocation': 0,
    'prospection': 0,
    'dommages': 0,
    'dommages_neutre': 0,
    'dommages_terre': 0,
    'dommages_feu': 0,
    'dommages_eau': 0,
    'dommages_air': 0,
    'retrait_pa': 0,
    'retrait_pm': 0,
    'esquive_pa': 0,
    'esquive_pm': 0,
    'tacle': 0,
    'fuite': 0,
    'ini': 0,
    'critique': 0,
    'dommages_critique': 0,
    'res_pourcentage_neutre': 0,
    'res_pourcentage_terre': 0,
    'res_pourcentage_feu': 0,
    'res_pourcentage_eau': 0,
    'res_pourcentage_air': 0,
    'res_fixe_neutre': 0,
    'res_fixe_terre': 0,
    'res_fixe_feu': 0,
    'res_fixe_eau': 0,
    'res_fixe_air': 0,
    'dommages_poussee': 0,
    're_pou': 0,
    're_crit':0
}

def parse_stats(texte):
    # Dictionnaire de correspondance entre les noms dans le texte et les clés du dictionnaire de stats
    correspondances = {
        'Vitalité': 'vitalite',
        'Force': 'force',
        'Chance': 'chance',
        'Intelligence': 'intelligence',
        'Agilité': 'agilite',
        'Puissance': 'puissance',
        'Sagesse': 'sagesse',
        'PA': 'pa',
        'PM': 'pm',
        'PO': 'po',
        'Invocation': 'invocation',
        'Prospection': 'prospection',
        'Dommages': 'dommages',
        'Dommages Neutre': 'dommages_neutre',
        'Dommages Terre': 'dommages_terre',
        'Dommages Feu': 'dommages_feu',
        'Dommages Eau': 'dommages_eau',
        'Dommages Air': 'dommages_air',
        'Retrait PA': 'retrait_pa',
        'Retrait PM': 'retrait_pm',
        'Esquive PA': 'esquive_pa',
        'Esquive PM': 'esquive_pm',
        'Tacle': 'tacle',
        'Fuite': 'fuite',
        'Initiative': 'ini',
        'Critique': 'critique',
        'Dommages Critique': 'dommages_critique',
        '% Rés. Neutre': 'res_pourcentage_neutre',
        '% Rés. Terre': 'res_pourcentage_terre',
        '% Rés. Feu': 'res_pourcentage_feu',
        '% Rés. Eau': 'res_pourcentage_eau',
        '% Rés. Air': 'res_pourcentage_air',
        'Rés. Neutre': 'res_fixe_neutre',
        'Rés. Terre': 'res_fixe_terre',
        'Rés. Feu': 'res_fixe_feu',
        'Rés. Eau': 'res_fixe_eau',
        'Rés. Air': 'res_fixe_air',
        'Dommages Poussée': 'dommages_poussee',
        'Rés. Critique': 're_crit',
        'Rés. Poussée': 're_pou'
    }
    
    lignes = texte.strip().split('\n')
    stats_extraites = stats.copy()
    
    for ligne in lignes:
        # Regex pour les jets de valeurs (positifs ou négatifs)
        match_range = re.match(r'(-?\d+)\s*à\s*(-?\d+)\s*(.+)', ligne)
        if match_range:
            valeur1 = int(match_range.group(1))
            valeur2 = int(match_range.group(2))
            
            # On prend la valeur qui a la plus grande magnitude (le plus grand "valeur absolue")
            # C'est la valeur la plus extrême (ex: -10 au lieu de -7)
            valeur = max(valeur1,valeur2)
            
            nom_stat = match_range.group(3).strip()
            
            if nom_stat in correspondances:
                key = correspondances[nom_stat]
                stats_extraites[key] += valeur
                
            continue

        # Regex pour les valeurs simples (positives ou négatives)
        match_single = re.match(r'(-?\d+)\s*(.+)', ligne)
        if match_single:
            valeur = int(match_single.group(1))
            nom_stat = match_single.group(2).strip()
            
            if nom_stat in correspondances:
                key = correspondances[nom_stat]
                stats_extraites[key] += valeur
    return stats_extraites


stats_de_l_item = parse_stats(texte_item)
print(stats_de_l_item)
valeur = (
    stats_de_l_item['vitalite'] * 1 +
    (stats_de_l_item['chance']+ stats_de_l_item['puissance']) * coeff_stat_principal + 
    (stats_de_l_item['force'] + stats_de_l_item['intelligence'] + stats_de_l_item['agilite'])*coeff_stat_secondaire+
    stats_de_l_item['sagesse'] * coeff_sagesse +
    (stats_de_l_item['res_pourcentage_neutre'] + stats_de_l_item['res_pourcentage_terre'] + stats_de_l_item['res_pourcentage_feu'] + stats_de_l_item['res_pourcentage_eau'] + stats_de_l_item['res_pourcentage_air']) * coeff_res_pourcentage +
    (stats_de_l_item['res_fixe_neutre'] + stats_de_l_item['res_fixe_terre'] + stats_de_l_item['res_fixe_feu'] + stats_de_l_item['res_fixe_eau'] + stats_de_l_item['res_fixe_air']+ 2*stats_de_l_item['re_crit']+ 2*stats_de_l_item['re_pou']) * coeff_re_fixe +
    stats_de_l_item['invocation'] * coeff_invoc +
    stats_de_l_item['po'] * coeff_po +
    stats_de_l_item['pm'] * coeff_pm +
    stats_de_l_item['pa'] * coeff_pa +
    stats_de_l_item['ini'] * coeff_ini +
    (stats_de_l_item['dommages']+ stats_de_l_item['dommages_eau']) * coeff_dommages +
    stats_de_l_item['fuite'] * coeff_fuite +
    stats_de_l_item['tacle'] * coeff_tacle +
    (stats_de_l_item['esquive_pa'] + stats_de_l_item['esquive_pm']) * coeff_esquive +
    (stats_de_l_item['retrait_pa'] + stats_de_l_item['retrait_pm']) * coeff_retrait +
    stats_de_l_item['critique'] * coeff_crit +
    stats_de_l_item['dommages_critique'] * coeff_do_crit +
    stats_de_l_item['dommages_poussee'] * coeff_do_pou
)
print(f"\nLa valeur totale de l'item est : {valeur}")

nb_elements=2.8
valeur_pano=valeur/nb_elements
print(valeur_pano)