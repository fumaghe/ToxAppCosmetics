import time
import sqlite3

def get_db_connection():
    conn = sqlite3.connect('app/data/ingredients.db')
    conn.row_factory = sqlite3.Row
    return conn

def search_ingredient(ingredient_name_or_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    SELECT 
        pcpc_ingredientid AS id, 
        pcpc_ingredientname AS name, 
        NOAEL_CIR, 
        LD50_CIR, 
        LD50_PubChem, 
        echa_value,
        echa_dossier,
        value_updated, 
        cir_page, 
        cir_pdf, 
        pubchem_page
    FROM ingredients
    WHERE pcpc_ingredientid = ? OR pcpc_ingredientname = ?
    """
    cursor.execute(query, (ingredient_name_or_id, ingredient_name_or_id))
    result = cursor.fetchone()
    conn.close()
    return result

def measure_search_time(ingredient_ids_or_names):
    times = []
    
    for ingredient in ingredient_ids_or_names:
        start_time = time.time()
        search_ingredient(ingredient)
        end_time = time.time()
        
        search_time = end_time - start_time
        times.append(search_time)
    
    average_time = sum(times) / len(times)
    print(f"Average search time: {average_time:.4f} seconds")
    
ingredienti = ['Acetic Acid', '1,2-Butanediol', '1,5-Pentanediol', '2,4-Diaminophenol Dihydrochloride', '2,3-Naphthalenediol',
               '2,3-Butanediol', '2-Amino-4-Hydroxyethylaminoanisole', '2-Methyl-5-Hydroxyethylaminophenol', '2-Methoxyethanol', '2-Oleamido-1,3-Octadecanediol',
               'Batyl Isostearate', 'Bassia Butyracea Seed Butter', 'Babassu Oil Polyglyceryl-6 Esters', 'Basic Brown 17', 'Basic Violet 3',
               'Euterpe Oleracea Fruit Oil', 'Euterpe Oleracea Sterols', 'Eucalyptus Globulus Leaf Powder', 'Eucalyptus Globulus Leaf Water', 'Beeswax Acid']

measure_search_time(ingredienti)

