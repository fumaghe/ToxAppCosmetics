import requests
from bs4 import BeautifulSoup

def get_pubchem_cid(ingredient_name):
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{ingredient_name}/cids/JSON"
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Errore nel recuperare CID per {ingredient_name}. Codice di risposta: {response.status_code}")
        return None
    
    try:
        data = response.json()
        cid = str(data['IdentifierList']['CID'][0])  # Convertire in stringa
        print(f"CID per {ingredient_name}: {cid}")
        return cid
    except (KeyError, IndexError, ValueError) as e:
        print(f"Errore nell'estrarre CID per {ingredient_name}: {e}")
        print(f"Risposta ricevuta: {response.text}")
        return None

def get_ld50_pubchem(cid):
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{cid}/JSON/"
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Errore nel recuperare i dati per il composto con CID {cid}. Codice di risposta: {response.status_code}")
        return None
    
    try:
        data = response.json()
        sections = data['Record']['Section']
        
        ld50_values = []
        
        def extract_ld50(sections):
            for section in sections:
                if 'Section' in section:
                    extract_ld50(section['Section'])
                if 'Information' in section:
                    for info in section['Information']:
                        if 'Value' in info and 'StringWithMarkup' in info['Value']:
                            for item in info['Value']['StringWithMarkup']:
                                if 'LD50' in item['String'] and 'mg/kg' in item['String']:
                                    ld50_values.append(item['String'])
        
        extract_ld50(sections)
        
        return ld50_values if ld50_values else None
    except Exception as e:
        print(f"Errore nell'estrarre i dati LD50: {e}")
        return None

def extract_first_status_link(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        status_links = soup.find('table').find_all('a')

        if not status_links:
            return None
        
        # Extract the first link
        first_link = "https://cir-reports.cir-safety.org/" + status_links[0]['href'].replace("../", "")
        
        # Try the first link
        try:
            response = requests.get(first_link)
            response.raise_for_status()
            return first_link
        except requests.RequestException:
            # If the first link fails, check if there's a second link
            if len(status_links) > 1:
                second_link = "https://cir-reports.cir-safety.org/" + status_links[1]['href'].replace("../", "")
                try:
                    response = requests.get(second_link)
                    response.raise_for_status()
                    return second_link
                except requests.RequestException as e:
                    return None
            else:
                return None

    except requests.RequestException as e:
        return None
