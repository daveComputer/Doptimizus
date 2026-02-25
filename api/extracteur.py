import re
import json

def parse_item(lines):
    """Analyse un item en utilisant la répétition du nom comme balise."""
    nom_reference = lines[0]
    item_data = {
        "nom": nom_reference,
        "type_objet": "",
        "niveau": 0,
        "panoplie": None,
        "stats": []
    }

    # Ligne 1 : Type & Niveau (Format: "Anneau - Niveau 200")
    type_niv_match = re.search(r"(.+) - Niveau (\d+)", lines[1])
    if type_niv_match:
        item_data["type_objet"] = type_niv_match.group(1).strip()
        item_data["niveau"] = int(type_niv_match.group(2))

    # On cherche à quel index le nom se répète
    repetition_index = -1
    for i in range(1, len(lines)):
        if lines[i].lower() == nom_reference.lower():
            repetition_index = i
            break

    # Si le nom se répète, la ligne entre le niveau (index 1) et la répétition est la panoplie
    if repetition_index > 2:
        # La panoplie est à l'index 2 (entre index 1 et index répétition)
        item_data["panoplie"] = lines[2]
        stats_start_index = repetition_index + 1
    else:
        # Sécurité au cas où la structure varierait
        stats_start_index = 3

    # Extraction des stats
    stat_pattern = r"(-?\d+(?:\sà\s-?\d+)?)\s*(.*)"
    for i in range(stats_start_index, len(lines)):
        match = re.search(stat_pattern, lines[i])
        if match:
            item_data["stats"].append({
                "nom": match.group(2).strip(),
                "valeur": match.group(1).replace('\xa0', ' ')
            })
    return item_data

def parse_set_bonus(lines):
    """Analyse un bloc de bonus de panoplie (pas de répétition du nom)."""
    set_data = {
        "nom_panoplie": lines[0],
        "type": "bonus_panoplie",
        "paliers": []
    }
    current_palier = None
    
    for i in range(1, len(lines)):
        line = lines[i]
        # Si la ligne est un chiffre seul (2, 3...)
        if re.match(r"^\d+$", line):
            if current_palier:
                set_data["paliers"].append(current_palier)
            current_palier = {"nombre_items": int(line), "bonus": []}
        elif current_palier is not None:
            match = re.search(r"(-?\d+(?:\sà\s-?\d+)?)\s*(.*)", line)
            if match:
                current_palier["bonus"].append({
                    "nom": match.group(2).strip(),
                    "valeur": match.group(1).replace('\xa0', ' ')
                })
    if current_palier:
        set_data["paliers"].append(current_palier)
    return set_data

def process_file(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    blocks = content.split('//')
    final_database = []

    for block in blocks:
        lines = [line.strip() for line in block.strip().split('\n') if line.strip()]
        if not lines: continue
            
        nom_principal = lines[0].lower()
        # On vérifie s'il y a répétition du nom dans les lignes suivantes
        is_item = any(l.lower() == nom_principal for l in lines[1:])

        if is_item:
            final_database.append(parse_item(lines))
        else:
            final_database.append(parse_set_bonus(lines))

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_database, f, indent=4, ensure_ascii=False)
    
    print(f"Fait ! {len(final_database)} entrées traitées.")

process_file('items_bruts.txt', 'database.json')