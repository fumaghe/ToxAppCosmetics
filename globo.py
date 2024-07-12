import requests
from bs4 import BeautifulSoup
import sqlite3
from tqdm import tqdm

# Funzione per trovare il link di un ingrediente
def trova_link(ingrediente):
    base_url = "https://cosmileeurope.eu/wp-content/plugins/inci-db-search/search.php?s="
    parametri = "&l=it-IT&n=10&p=https%3A%2F%2Fcosmileeurope.eu%2Fit%2Finci%2Fingrediente"
    
    def fetch_link(query):
        url = f"{base_url}{query.replace(' ', '%20')}{parametri}"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        link = soup.find('a', class_='inci_box_link-link')
        if link:
            return link['href']
        return None
    
    link = fetch_link(ingrediente)
    if not link:
        words = ingrediente.split()
        while words:
            words.pop()
            partial_ingrediente = ' '.join(words)
            link = fetch_link(partial_ingrediente)
            if link:
                break
    return link

# Funzione per estrarre informazioni dalla pagina dell'ingrediente
def estrai_informazioni(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    info = {}
    
    # Estrazione delle sezioni principali
    main_content = soup.find('div', class_='inci_db')
    if main_content:
        h1 = main_content.find('h1', {'id': 'inci'})
        if h1:
            info['Nome Ingrediente'] = h1.get_text(strip=True)
        
        sections = main_content.find_all(['h2', 'h3', 'p'])
        current_section = None
        
        for tag in sections:
            if tag.name == 'h2':
                current_section = tag.get_text(strip=True)
                info[current_section] = []
            elif current_section:
                info[current_section].append(tag.get_text(strip=True))
    
    return info

# Funzione principale per aggiornare il database
def aggiorna_database(db_path, start_index=0, num_ingredienti=None):
    # Connessione al database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Aggiungi la colonna 'cosmile_page' se non è già presente
    cursor.execute('PRAGMA table_info(ingredients)')
    columns = [column[1] for column in cursor.fetchall()]
    if 'cosmile_page' not in columns:
        cursor.execute('ALTER TABLE ingredients ADD COLUMN cosmile_page TEXT')
        conn.commit()

    # Recupera tutti gli ingredienti
    cursor.execute('SELECT pcpc_ingredientid, pcpc_ingredientname FROM ingredients')
    ingredienti = cursor.fetchall()

    # Se num_ingredienti è specificato, limitare il numero di ingredienti
    if num_ingredienti:
        ingredienti = ingredienti[start_index:start_index + num_ingredienti]
    else:
        ingredienti = ingredienti[start_index:]

    # Inizializza contatori
    total = len(ingredienti)
    found = 0
    found_links = []

    # Aggiorna la colonna 'cosmile_page' con i link trovati
    for pcpc_ingredientid, pcpc_ingredientname in tqdm(ingredienti, desc="Updating database"):
        link = trova_link(pcpc_ingredientname)
        if link:
            found += 1
            found_links.append(link)
            informazioni = estrai_informazioni(link)
            # Stampa le informazioni estratte
            print(f"Informazioni per {pcpc_ingredientname}:")
            for key, value in informazioni.items():
                print(f"\n{key}:")
                if isinstance(value, list):
                    for item in value:
                        print(f"  - {item}")
                else:
                    print(f"  {value}")
            print("\n" + "="*50 + "\n")
        cursor.execute('UPDATE ingredients SET cosmile_page = ? WHERE pcpc_ingredientid = ?', (link, pcpc_ingredientid))
        conn.commit()

    # Chiude la connessione al database
    conn.close()

    # Stampa il riepilogo
    print(f"Found {found} links out of {total} ingredients.")
    for link in found_links:
        print(link)

# Esempio di utilizzo
db_path = 'ingredients.db'
start_index = 0  # Cambia questo valore per l'indice di partenza
num_ingredienti = 2  # Cambia questo valore per il numero di ingredienti da cercare, oppure imposta su None per cercare tutti gli ingredienti

aggiorna_database(db_path, start_index, num_ingredienti)
