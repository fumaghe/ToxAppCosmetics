import sqlite3

def count_echa_values():
    conn = sqlite3.connect('ingredients.db')
    cursor = conn.cursor()
    
    # Selezioniamo i primi 700 ingredienti
    cursor.execute("""
        SELECT echa_value, echa_dossier 
        FROM ingredients 
        LIMIT 700
    """)
    rows = cursor.fetchall()
    
    # Contiamo i valori non nulli per echa_value (escludendo '[]') e echa_dossier
    echa_value_count = sum(1 for row in rows if row[0] is not None and row[0] != '[]')
    echa_dossier_count = sum(1 for row in rows if row[1] is not None)
    
    conn.close()
    
    print(f"Numero di ingredienti con echa_value: {echa_value_count}")
    print(f"Numero di ingredienti con echa_dossier: {echa_dossier_count}")

count_echa_values()
