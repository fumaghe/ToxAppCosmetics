import sqlite3

def add_column_to_db():
    conn = sqlite3.connect('app\data\ingredients.db')  # Assicurati di avere il percorso corretto
    cursor = conn.cursor()

    # Aggiungi la colonna value_updated se non esiste già
    cursor.execute("ALTER TABLE ingredients ADD COLUMN value_updated TEXT")

    conn.commit()
    conn.close()

# Chiamata alla funzione per aggiungere la colonna
add_column_to_db()
