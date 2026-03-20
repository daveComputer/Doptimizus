import sqlite3
import os
import requests

API_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(API_DIR, "database.db")

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Permet d'accéder aux colonnes par nom
    return conn

def init_db():
    conn = get_db_connection()
    # Création de la table blacklist si elle n'existe pas
    conn.execute('''
        CREATE TABLE IF NOT EXISTS blacklist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT, 
            item_nom TEXT,
            UNIQUE(user_id, item_nom)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS user_stats (
            user_id TEXT PRIMARY KEY,
            poids_json TEXT,
            date_maj DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            config_json TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS commentaires (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            auteur TEXT,
            message TEXT NOT NULL,
            date DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


DISCORD_WEBHOOK_URL = "https://discordapp.com/api/webhooks/1483181860463841442/XinhHUqh7y2f9U3VCryZx9z4iUM_04J61cnDkNbseNIISCs6Uvu7gLd0SnYuAx3KIZ3Y"

def send_discord_notification(message):
    data = {
        "content": f"🚀 **Nouveau commentaire reçu !**",
        "embeds": [{
            "description": message,
            "color": 5814783, # Une couleur sympa (bleu-ish)
            "footer": {"text": "Mon Site Web"}
        }]
    }
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=data)
    except Exception as e:
        print(f"Erreur Discord : {e}")

# Initialisation au lancement
if __name__ == "__main__":
    init_db()