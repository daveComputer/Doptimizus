import json
import traceback

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from statistiques import enrichir_base_de_donnees
from statistiques import extraire_top_3_par_type
from optimiseur_top3 import extraire_top_n_solutions
app = Flask(__name__)
CORS(app)  # Autorise le frontend à parler au backend

# Chemin où le fichier sera enregistré
SAVE_PATH = "../scores_personnage.json"

@app.route('/save', methods=['POST'])
def save_data():
    try:
        data = request.json
        # 1. Sauvegarde des scores du radar
        os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
        with open(SAVE_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        
        # 2. APPEL DE LA FONCTION D'ENRICHISSEMENT
        # C'est ici que la magie opère quand on clique sur "Confirmer"
        enrichir_base_de_donnees('../database.json', '../database_scores.json', config_user=data)
        
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
        top_items = extraire_top_3_par_type('../database_scores.json', lvl)
        
        # 2. On récupère le top 3 des stuffs (via optimiseur_top_3.py)
        top_stuffs = extraire_top_n_solutions('../database_scores.json', lvl, n=5)
        
        return jsonify({
            "top_items": top_items,
            "top_stuffs": top_stuffs
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)