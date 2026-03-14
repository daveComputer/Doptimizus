import json
import traceback
import uuid
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from api.statistiques import enrichir_base_de_donnees
from api.statistiques import extraire_top_3_par_type
from api.optimiseur_top3 import extraire_top_n_solutions
from api.database import get_db_connection, init_db
app = Flask(__name__,template_folder='web', 
            static_folder='static')
CORS(app)  # Autorise le frontend à parler au backend
items_exclus = []
init_db()

# Chemin où le fichier sera enregistré

@app.route('/')
def serve_index():
    return render_template('index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)


@app.route('/save', methods=['POST'])
def save_data():
    try:
        data = request.json
        
        # 1. SAUVEGARDE DANS SQLITE (Pour l'historique)
        conn = get_db_connection()
        conn.execute('INSERT INTO history (config_json) VALUES (?)', (json.dumps(data),))
        conn.commit()
        conn.close()

        # 2. APPEL DE LA FONCTION D'ENRICHISSEMENT
        # On ne passe plus 'filename', mais directement 'data'
        # Assure-toi que enrichir_base_de_donnees peut traiter le dict directement !
        enrichir_base_de_donnees(
            'database.json', 
            'database_scores.json', 
            config_user=data  # On utilise le dictionnaire en mémoire
        )
        
        return jsonify({
            "status": "success", 
            "message": "Configuration enregistrée en base et scores mis à jour !"
        })

    except Exception as e:
        print("!!! ERREUR LORS DE LA SAUVEGARDE !!!")
        traceback.print_exc() 
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get-results', methods=['GET'])
def get_results():
    try:
        lvl = request.args.get('lvl', default=200, type=int)
        
        # 1. RÉCUPÉRATION DE LA BLACKLIST DEPUIS SQLITE
        # On interroge la base de données au lieu de lire un fichier .txt
        conn = get_db_connection()
        rows = conn.execute('SELECT item_nom FROM blacklist').fetchall()
        conn.close()
        
        # On transforme le résultat en une liste simple de noms
        items_bannis = [row['item_nom'] for row in rows]
        
        # 2. Passage de la liste aux fonctions de calcul
        # IMPORTANT : Tu dois modifier la signature de ces deux fonctions 
        # pour qu'elles acceptent l'argument 'items_bannis'.
        top_items = extraire_top_3_par_type(
            'database_scores.json', 
            lvl, 
            exclus=items_bannis
        )
        
        top_stuffs = extraire_top_n_solutions(
            'database_scores.json', 
            lvl, 
            n=5, 
            items_exclus=items_bannis
        )
        
        # 3. On renvoie tout au JS
        return jsonify({
            "status": "success",
            "top_items": top_items,
            "top_stuffs": top_stuffs
        })
        
    except Exception as e:
        print(f"Erreur lors de la récupération des résultats : {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
        
    except Exception as e:
        # Debug : affiche l'erreur exacte dans tes logs Render
        print(f"Erreur optimisation : {e}")
        traceback.print_exc()  # Affiche la trace complète de l'erreur
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route('/exclude-item', methods=['POST'])
def exclude_item():
    item_nom = request.json.get('item_nom')
    items_exclus.append(item_nom)
    if not item_nom:
        return "Nom manquant", 400
    
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO blacklist (item_nom) VALUES (?)', (item_nom,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass # L'item est déjà dans la liste, pas grave
    finally:
        conn.close()
    return "OK", 200

@app.route('/get-blacklist', methods=['GET'])
def get_blacklist():
    conn = get_db_connection()
    items = conn.execute('SELECT item_nom FROM blacklist').fetchall()
    conn.close()
    # On transforme les lignes en liste de strings
    return jsonify([row['item_nom'] for row in items])

@app.route('/rehabilitate-item', methods=['POST'])
def rehabilitate_item():
    item_nom = request.json.get('item_nom')
    conn = get_db_connection()
    conn.execute('DELETE FROM blacklist WHERE item_nom = ?', (item_nom,))
    conn.commit()
    conn.close()
    return "OK", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port,debug=True)