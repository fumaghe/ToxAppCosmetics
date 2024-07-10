import sqlite3

def count_echa_values():
    conn = sqlite3.connect('app/data/ingredients.db')
    cursor = conn.cursor()
    
    # Selezioniamo i primi 6056 ingredienti
    cursor.execute("""
        SELECT echa_value, LD50_CIR, NOAEL_CIR, LD50_pubchem, 
               cir_page, cir_pdf, pubchem_page, echa_dossier, pcpc_ingredientname
        FROM ingredients 
        LIMIT 6056
    """)
    rows = cursor.fetchall()
    
    # Inizializziamo i contatori
    echa_value_count = 0
    no_echa_data_count = 0
    LD50_CIR_count = 0
    NOAEL_CIR_count = 0
    LD50_pubchem_count = 0
    last_echa_value_index = -1
    
    cir_page_count = 0
    cir_pdf_count = 0
    pubchem_page_count = 0
    echa_dossier_count = 0
    
    # Contatori per numero di dati presenti
    count_data_presence = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    count_link_presence = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    
    # Lista per i nomi degli ingredienti senza valori
    no_value_ingredients = []
    
    # Iteriamo sui risultati per contare i valori
    for index, row in enumerate(rows):
        has_echa_value = row[0] is not None and row[0] != '[]'
        has_LD50_CIR = row[1] is not None and row[1] != '[]'
        has_NOAEL_CIR = row[2] is not None and row[2] != '[]'
        has_LD50_pubchem = row[3] is not None and row[3] != '[]'
        
        has_cir_page = row[4] is not None and row[4] != '[]'
        has_cir_pdf = row[5] is not None and row[5] != '[]'
        has_pubchem_page = row[6] is not None and row[6] != '[]'
        has_echa_dossier = row[7] is not None and row[7] != '[]'
        
        pcpc_ingredientname = row[8]
        
        data_count = sum([has_echa_value, has_LD50_CIR, has_NOAEL_CIR, has_LD50_pubchem])
        link_count = sum([has_cir_page, has_cir_pdf, has_pubchem_page, has_echa_dossier])
        
        count_data_presence[data_count] += 1
        count_link_presence[link_count] += 1
        
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
            no_value_ingredients.append(pcpc_ingredientname)
        
        if has_cir_page:
            cir_page_count += 1
            
        if has_cir_pdf:
            cir_pdf_count += 1
            
        if has_pubchem_page:
            pubchem_page_count += 1
            
        if has_echa_dossier:
            echa_dossier_count += 1
    
    conn.close()
    
    # Salviamo i nomi degli ingredienti senza valori in NOVALUE.txt
    with open('NOVALUE.txt', 'w') as file:
        for ingredient in no_value_ingredients:
            file.write(f"{ingredient}\n")
    
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

    print("--------------------------------------------------")
    
    print(f"Numero di ingredienti con cir_page: {cir_page_count}")
    print(f"Numero di ingredienti con cir_pdf: {cir_pdf_count}")
    print(f"Numero di ingredienti con pubchem_page: {pubchem_page_count}")
    print(f"Numero di ingredienti con echa_dossier: {echa_dossier_count}")
    
    print("\nDistribuzione del numero di link presenti tra cir_page, cir_pdf, pubchem_page e echa_dossier:")
    for count, num_ingredients in count_link_presence.items():
        print(f"{count} link presenti: {num_ingredients} ingredienti")

    print("--------------------------------------------------")

    print(f"Numero di ingredienti con almeno un valore: {sum(num for count, num in count_data_presence.items() if count > 0)}")
    print(f"Numero di ingredienti con zero valori: {count_data_presence[0]}")

    print("--------------------------------------------------")

    print(f"Numero di ingredienti con almeno un link: {sum(num for count, num in count_link_presence.items() if count > 0)}")
    print(f"Numero di ingredienti con zero link: {count_link_presence[0]}")
    
count_echa_values()
