import json
import traceback
import uuid

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from statistiques import enrichir_base_de_donnees
from statistiques import extraire_top_3_par_type
from optimiseur_top3 import extraire_top_n_solutions
app = Flask(__name__,static_folder='web')
CORS(app)  # Autorise le frontend à parler au backend
items_exclus = []

# Chemin où le fichier sera enregistré

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route('/save', methods=['POST'])
def save_data():
    try:
        data = request.json
        unique_id = str(uuid.uuid4())
        filename = f"config_{unique_id}.json"
        with open(filename, 'w') as f:
            json.dump(request.json, f, indent=4)
        
        # 2. APPEL DE LA FONCTION D'ENRICHISSEMENT
        # C'est ici que la magie opère quand on clique sur "Confirmer"
        enrichir_base_de_donnees('database.json', 'database_scores.json',filename, config_user=data)
        
        return jsonify({
            "status": "success", 
            "message": "Scores enregistrés et base de données mise à jour !"
        })
    except Exception as e:
        # Ceci va écrire l'erreur exacte dans tes logs Docker !
        print("!!! ERREUR SERVEUR !!!")
        traceback.print_exc() 
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get-results', methods=['GET'])
def get_results():
    try:
        lvl = request.args.get('lvl', default=200, type=int)
        
        # 1. Récupère le Top 5 par type (avec les répartitions d'items déjà incluses)
        top_items = extraire_top_3_par_type('database_scores.json', lvl)
        
        # 2. Récupère le top des stuffs (l'optimiseur calcule maintenant les % globaux)
        # Note : On suppose que ta fonction extraire_top_n_solutions 
        # a été mise à jour avec la logique de cumul des points.
        top_stuffs = extraire_top_n_solutions('database_scores.json', lvl, n=5)
        
        # 3. On renvoie tout au JS
        return jsonify({
            "status": "success",
            "top_items": top_items,
            "top_stuffs": top_stuffs  # Contiendra "stuff", "score" et "repartition"
        })
        
    except Exception as e:
        # Debug : affiche l'erreur exacte dans tes logs Render
        print(f"Erreur optimisation : {e}")
        traceback.print_exc()  # Affiche la trace complète de l'erreur
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route('/exclude-item', methods=['POST'])
def exclude_item():
    data = request.json
    nom = data.get('item_nom')
    if nom and nom not in items_exclus:
        items_exclus.append(nom)
        # Optionnel : sauvegarder dans un fichier pour que ça reste après un reboot
        with open("blacklist.txt", "a") as f:
            f.write(f"{nom}\n")
    return jsonify({"status": "success"})

@app.route('/get-blacklist', methods=['GET'])
def get_blacklist():
    # On renvoie la liste triée par ordre alphabétique
    return jsonify(sorted(list(items_exclus)))

@app.route('/rehabilitate-item', methods=['POST'])
def rehabilitate_item():
    data = request.json
    nom = data.get('item_nom')
    
    if nom in items_exclus:
        items_exclus.remove(nom)
        # On met à jour le fichier physique pour que ce soit permanent
        try:
            with open("blacklist.txt", "w", encoding="utf-8") as f:
                for item in items_exclus:
                    f.write(f"{item}\n")
        except Exception as e:
            print(f"Erreur lors de la mise à jour du fichier : {e}")
            
    return jsonify({"status": "success"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port,debug=True)