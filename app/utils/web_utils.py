import requests
from bs4 import BeautifulSoup

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
