import sqlite3

def count_echa_values():
    conn = sqlite3.connect('app\data\ingredients.db')
    cursor = conn.cursor()
    
    # Selezioniamo i primi 5577 ingredienti
    cursor.execute("""
        SELECT echa_value, LD50_CIR, NOAEL_CIR, LD50_pubchem 
        FROM ingredients 
        LIMIT 5877
    """)
    rows = cursor.fetchall()
    
    # Inizializziamo i contatori
    echa_value_count = 0
    no_echa_data_count = 0
    LD50_CIR_count = 0
    NOAEL_CIR_count = 0
    LD50_pubchem_count = 0
    last_echa_value_index = -1
    
    # Contatori per numero di dati presenti
    count_data_presence = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    
    # Iteriamo sui risultati per contare i valori
    for index, row in enumerate(rows):
        has_echa_value = row[0] is not None and row[0] != '[]'
        has_LD50_CIR = row[1] is not None and row[1] != '[]'
        has_NOAEL_CIR = row[2] is not None and row[2] != '[]'
        has_LD50_pubchem = row[3] is not None and row[3] != '[]'
        
        data_count = sum([has_echa_value, has_LD50_CIR, has_NOAEL_CIR, has_LD50_pubchem])
        count_data_presence[data_count] += 1
        
        if has_echa_value:
            echa_value_count += 1
            last_echa_value_index = index
        
        if has_LD50_CIR:
            LD50_CIR_count += 1
        
        if has_NOAEL_CIR:
            NOAEL_CIR_count += 1
        
        if has_LD50_pubchem:
            LD50_pubchem_count += 1
        
        if not has_echa_value and not has_LD50_CIR and not has_NOAEL_CIR and not has_LD50_pubchem:
            no_echa_data_count += 1
    
    conn.close()
    
    print(f"Numero di ingredienti con echa_value: {echa_value_count}")
    print(f"Numero di ingredienti con LD50_CIR: {LD50_CIR_count}")
    print(f"Numero di ingredienti con NOAEL_CIR: {NOAEL_CIR_count}")
    print(f"Numero di ingredienti con LD50_pubchem: {LD50_pubchem_count}")
    print(f"Numero di ingredienti senza nessuno dei dati: {no_echa_data_count}")
    if last_echa_value_index != -1:
        print(f"Indice dell'ultimo ingrediente con echa_value: {last_echa_value_index}")
    else:
        print("Nessun ingrediente con echa_value trovato")
    
    print("\nDistribuzione del numero di dati presenti tra echa_value, LD50_CIR, NOAEL_CIR e LD50_pubchem:")
    for count, num_ingredients in count_data_presence.items():
        print(f"{count} dati presenti: {num_ingredients} ingredienti")

count_echa_values()
