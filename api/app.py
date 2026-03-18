import json
import traceback
import uuid
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from flask import Flask, request, jsonify, send_from_directory, render_template, session
from flask_cors import CORS
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from api.statistiques import enrichir_base_de_donnees
from api.statistiques import extraire_top_3_par_type
from api.optimiseur_top3 import extraire_top_n_solutions
from api.database import get_db_connection, init_db, send_discord_notification
API_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(API_DIR, "database.db")
app = Flask(__name__,template_folder='web', 
            static_folder='static')
CORS(app)  # Autorise le frontend à parler au backend


app.secret_key = 'clementine'

def get_db_connection():
    # On force l'ouverture du fichier au bon endroit
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


init_db()
db_path = os.path.join(API_DIR, 'database.json')
scores_path = os.path.join(API_DIR, 'database_scores.json')
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
            db_path, 
            scores_path, 
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
        user_id = session.get('user_id')
        
        # 1. RÉCUPÉRATION DE LA BLACKLIST DEPUIS SQLITE
        # On interroge la base de données au lieu de lire un fichier .txt
        conn = get_db_connection()
        rows = conn.execute('SELECT item_nom FROM blacklist WHERE user_id = ?', (user_id,)).fetchall()
        conn.close()
        
        # On transforme le résultat en une liste simple de noms
        items_bannis = [row['item_nom'] for row in rows]
        
        # 2. Passage de la liste aux fonctions de calcul
        # IMPORTANT : Tu dois modifier la signature de ces deux fonctions 
        # pour qu'elles acceptent l'argument 'items_bannis'.
        top_items = extraire_top_3_par_type(
            scores_path, 
            lvl, 
            exclus=items_bannis
        )
        
        top_stuffs = extraire_top_n_solutions(
            scores_path, 
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
    user_id = session.get('user_id')
    
    # 1. Vérification initiale
    if not item_nom:
        return "Nom manquant", 400

    # 2. Séparation des noms par '/' et nettoyage des espaces inutiles
    # On utilise une compréhension de liste pour ignorer les entrées vides
    noms_a_traiter = [n.strip() for n in item_nom.split('/') if n.strip()]

    conn = get_db_connection()
    try:
        for nom in noms_a_traiter:
            # 4. Insertion en base de données
            try:
                conn.execute(
                    'INSERT INTO blacklist (user_id, item_nom) VALUES (?, ?)', 
                    (user_id, nom)
                )
            except sqlite3.IntegrityError:
                # L'item est déjà en DB, on passe au suivant
                continue
        
        conn.commit()
    except Exception as e:
        return f"Erreur lors de l'insertion : {str(e)}", 500
    finally:
        conn.close()

    return "OK", 200

@app.route('/get-blacklist', methods=['GET'])
def get_blacklist():
    user_id = session.get('user_id')
    conn = get_db_connection()
    rows = conn.execute('SELECT item_nom FROM blacklist WHERE user_id = ?', (user_id,)).fetchall()
    conn.close()
    return [row['item_nom'] for row in rows]

@app.route('/rehabilitate-item', methods=['POST'])
def rehabilitate_item():
    item_nom = request.json.get('item_nom')
    conn = get_db_connection()
    conn.execute('DELETE FROM blacklist WHERE item_nom = ?', (item_nom,))
    conn.commit()
    conn.close()
    return "OK", 200

@app.route('/add_comment', methods=['POST'])
def add_comment():
    data = request.json
    message = data.get('message')

    if not message:
        return "Message vide", 400

    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO commentaires (message) VALUES (?)', (message,))
        conn.commit()
        
        # --- APPEL À DISCORD ICI ---
        send_discord_notification( message)
        
    finally:
        conn.close()
        
    return "Merci pour votre retour !", 200

@app.before_request
def ensure_user_id():
    # On vérifie si l'ID existe
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
        # On force Flask à envoyer le cookie de session immédiatement
        session.permanent = True 


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port,debug=True)