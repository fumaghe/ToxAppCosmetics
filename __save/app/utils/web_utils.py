import requests
from bs4 import BeautifulSoup
import re

def get_pubchem_cid(ingredient_name):
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{ingredient_name}/cids/JSON"
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        data = response.json()
        cid = str(data['IdentifierList']['CID'][0])
        return cid
    except requests.RequestException as e:
        print(f"Errore nel recuperare CID per {ingredient_name}: {e}")
        return None
    except (KeyError, IndexError, ValueError) as e:
        print(f"Errore nell'estrarre CID per {ingredient_name}: {e}")
        return None

def find_missing_values(ingredient_name):
    value = search_pubmed(ingredient_name)
    if value:
        return value, "PubMed"
    value = search_echa(ingredient_name)
    if value:
        return value, "ECHA"
    value = search_pubchem(ingredient_name)
    if value:
        return value, "PubChem"
    return "Value not found in available sources.", "Unknown"

def extract_first_status_link(ingredient_id):
    url = f"https://cir-reports.cir-safety.org/cir-ingredient-status-report/?id={ingredient_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Cerca i link nella pagina
        status_links = soup.find_all('a', href=True)
        
        if not status_links:
            print("Nessun link trovato nella pagina CIR.")
            return None
        
        for link in status_links:
            href = link['href']
            if "status-report" in href or "report" in href:
                first_link = "https://cir-reports.cir-safety.org/" + href.replace("../", "")
                try:
                    response = requests.get(first_link)
                    response.raise_for_status()
                    return first_link
                except requests.RequestException as e:
                    print(f"Errore nell'accedere al link: {e}")
                    continue  # Prova il prossimo link

        print("Nessun link valido trovato nella pagina CIR.")
        return None

    except requests.RequestException as e:
        print(f"Errore nella richiesta HTTP per il link CIR: {e}")
        return None
    except (IndexError, TypeError) as e:
        print(f"Errore nel parsing della pagina CIR: {e}")
        return None


def search_pubmed(ingredient_name):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": ingredient_name,
        "retmode": "json",
        "retmax": 1
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        result = response.json()
        if result['esearchresult']['idlist']:
            article_id = result['esearchresult']['idlist'][0]
            return fetch_pubmed_article(article_id)
    return None

def fetch_pubmed_article(article_id):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "pubmed",
        "id": article_id,
        "retmode": "xml"
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'xml')
        abstract = soup.find('AbstractText')
        if abstract:
            return extract_toxicity_value(abstract.text)
    return None

def extract_toxicity_value(text):
    match = re.search(r'(\d+(\.\d+)?)\s*(mg/kg|mg\/kg)', text)
    if match:
        return match.group(1) + " " + match.group(3)
    return "Value not found in PubMed."

def search_echa(ingredient_name):
    search_url = f"https://echa.europa.eu/search-for-chemicals/-/dislist/details/0b0236e182de8d93?q={ingredient_name}"
    response = requests.get(search_url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table')
        if table:
            for row in table.find_all('tr'):
                if 'LD50' in row.text or 'NOAEL' in row.text:
                    cells = row.find_all('td')
                    for cell in cells:
                        match = re.search(r'(\d+(\.\d+)?)\s*(mg/kg|mg\/kg)', cell.text)
                        if match:
                            return match.group(1) + " " + match.group(3)
    return None

def search_pubchem(ingredient_name):
    base_url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{ingredient_name}/property/LD50,NOAEL/JSON"
    response = requests.get(base_url)
    if response.status_code == 200:
        data = response.json()
        if 'PropertyTable' in data:
            properties = data['PropertyTable']['Properties'][0]
            if 'LD50' in properties:
                return f"{properties['LD50']} mg/kg", "PubChem"
            if 'NOAEL' in properties:
                return f"{properties['NOAEL']} mg/kg", "PubChem"
    return None
