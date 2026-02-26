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
        filename = f"api/config_{unique_id}.json"
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
        top_items = extraire_top_3_par_type('database_scores.json', lvl)
        
        # 2. On récupère le top 3 des stuffs (via optimiseur_top_3.py)
        top_stuffs = extraire_top_n_solutions('database_scores.json', lvl, n=5)
        
        return jsonify({
            "top_items": top_items,
            "top_stuffs": top_stuffs
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port,debug=True)