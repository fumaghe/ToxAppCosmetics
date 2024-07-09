import sqlite3

def add_columns_if_not_exist():
    conn = sqlite3.connect('ingredients.db')
    cursor = conn.cursor()

    # Controlla se la colonna echa_value esiste
    cursor.execute("PRAGMA table_info(ingredients)")
    columns = [info[1] for info in cursor.fetchall()]
    
    if 'echa_value' not in columns:
        cursor.execute("ALTER TABLE ingredients ADD COLUMN echa_value TEXT")
        print("Added column echa_value")

    if 'echa_dossier' not in columns:
        cursor.execute("ALTER TABLE ingredients ADD COLUMN echa_dossier TEXT")
        print("Added column echa_dossier")

    conn.commit()
    conn.close()

# Esegui la funzione per aggiungere le colonne
add_columns_if_not_exist()
