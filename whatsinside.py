import sqlite3

def count_echa_values():
    conn = sqlite3.connect('ingredients.db')
    cursor = conn.cursor()
    
    # Selezioniamo i primi 700 ingredienti
    cursor.execute("""
        SELECT echa_value, echa_dossier 
        FROM ingredients 
        LIMIT 6000
    """)
    rows = cursor.fetchall()
    
    # Inizializziamo i contatori
    echa_value_count = 0
    echa_dossier_count = 0
    no_echa_data_count = 0
    last_echa_value_index = -1
    
    # Iteriamo sui risultati per contare i valori
    for index, row in enumerate(rows):
        has_echa_value = row[0] is not None and row[0] != '[]'
        has_echa_dossier = row[1] is not None
        
        if has_echa_value:
            echa_value_count += 1
            last_echa_value_index = index
            
        if has_echa_dossier:
            echa_dossier_count += 1
        
        if not has_echa_value and not has_echa_dossier:
            no_echa_data_count += 1
    
    conn.close()
    
    print(f"Numero di ingredienti con echa_value: {echa_value_count}")
    print(f"Numero di ingredienti con echa_dossier: {echa_dossier_count}")
    print(f"Numero di ingredienti senza né echa_value né echa_dossier: {no_echa_data_count}")
    if last_echa_value_index != -1:
        print(f"Indice dell'ultimo ingrediente con echa_value: {last_echa_value_index}")
    else:
        print("Nessun ingrediente con echa_value trovato")

count_echa_values()
