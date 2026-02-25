import json

with open('equipements_touch.json', 'r', encoding='utf-8') as f:
    items = json.load(f)

# On cherche des items qui n'existent QUE sur PC (ex: niveau > 200 ou noms spécifiques)
pc_only_keywords = ["Servitude", "Guerre", "Misère", "Corruption"]
items_suspects = []

for item in items:
    nom = item.get('name', {}).get('fr', '')
    if any(key in nom for key in pc_only_keywords):
        items_suspects.append(nom)

if items_suspects:
    print(f"⚠️ Alerte : {len(items_suspects)} items PC détectés !")
    print("Exemples :", items_suspects[:5])
else:
    print("✅ Le fichier semble propre ou ne contient pas les items PC récents.")