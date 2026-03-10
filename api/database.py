import sqlite3
import os

DB_PATH = "doptimizus.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Permet d'accéder aux colonnes par nom
    return conn

def init_db():
    conn = get_db_connection()
    # Création de la table blacklist si elle n'existe pas
    conn.execute('''
        CREATE TABLE IF NOT EXISTS blacklist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_nom TEXT UNIQUE NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            config_json TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Initialisation au lancement
if __name__ == "__main__":
    init_db()