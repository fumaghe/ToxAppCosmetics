import requests
from bs4 import BeautifulSoup
import re
from collections import Counter
import PyPDF2
import io

def extract_first_status_link(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        status_link = soup.find('table').find_all('tr')[1].find('a')['href']
        full_status_link = "https://cir-reports.cir-safety.org/" + status_link.replace("../", "")
       
        return full_status_link

    except requests.RequestException as e:
        print(f"Error accessing {url}: {e}")
    except (IndexError, TypeError) as e:
        print(f"Error parsing the page: {e}")

def extract_text_from_pdf(pdf_content):
    reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
    text = ""
    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        text += page.extract_text() or ""
    return text

def find_noael_values(text):
    pattern = r'NOAEL\s*[:/]?'
    matches = re.finditer(pattern, text, re.IGNORECASE)
    values = []
    for match in matches:
        start_index = match.end()
        words = text[start_index:start_index+100].split()[:20]  # Extracting next 20 words
        for word in words:
            if re.match(r'\d+(\.\d+)?', word):  # Checking if the word is a number
                values.append(word)
                break
    return values

def find_most_common_noael(values):
    if not values:
        return None, 0
    count = Counter(values)
    most_common_value, most_common_count = count.most_common(1)[0]
    return most_common_value, most_common_count

def check_and_append_noael(ingredient_id, most_common_noael, other_noael_values, noael_file_path):
    with open(noael_file_path, 'a', encoding='utf-8') as file:
        file.write(f"{ingredient_id}:most_common:{most_common_noael}\n")
        if other_noael_values:
            file.write(f"{ingredient_id}:other:{','.join(map(str, other_noael_values))}\n")

def find_ingredient_id_and_extract_link(ingredient_name, data_file_path, noael_file_path):
    # Load NOAEL values from the NOAEL file into a dictionary
    noael_dict = {}
    with open(noael_file_path, 'r', encoding='utf-8') as file:
        for line in file:
            if ':' in line:
                id_value_pair = line.strip().split(':')
                if len(id_value_pair) == 3:
                    id_key = id_value_pair[0]
                    if id_key not in noael_dict:
                        noael_dict[id_key] = {}
                    noael_dict[id_key][id_value_pair[1]] = id_value_pair[2].split(',')

    with open(data_file_path, 'r', encoding='utf-8') as file:
        ingredients = []
        for line in file:
            data = eval(line.strip())
            search_name = ingredient_name.lower()
            if (search_name in data['pcpc_ingredientname'].lower() or
                search_name in data['pcpc_ciringredientname'].lower()):
                ingredients.append((data['pcpc_ingredientname'], data['pcpc_ingredientid']))

    if ingredients:
        for ingredient_name, ingredient_id in set(ingredients):
            if ingredient_id in noael_dict:
                print(f"Ingredient name: {ingredient_name}")
                most_common_noael = noael_dict[ingredient_id].get('most_common', 'N/A')[0]
                other_values = noael_dict[ingredient_id].get('other', [])
                print(f"Most common NOAEL: {most_common_noael} mg/kg")
                for value in other_values:
                    print(f"Other NOAEL value: {value}")
            else:
                url = f"https://cir-reports.cir-safety.org/cir-ingredient-status-report/?id={ingredient_id}"
                status_link = extract_first_status_link(url)
                if status_link:
                    try:
                        response = requests.get(status_link)
                        response.raise_for_status()
                        
                        pdf_text = extract_text_from_pdf(response.content)
                        noael_values = find_noael_values(pdf_text)
                        most_common_noael, _ = find_most_common_noael(noael_values)
                        
                        if noael_values:
                            other_noael_values = set(noael_values)
                            other_noael_values.discard(most_common_noael)
                            
                            print(f"Ingredient name: {ingredient_name}")
                            print(f"Most common NOAEL: {most_common_noael} mg/kg")
                            for value in other_noael_values:
                                print(f"Other NOAEL value: {value}")

                            check_and_append_noael(ingredient_id, most_common_noael, list(other_noael_values), noael_file_path)
                        else:
                            print(f"Ingredient name: {ingredient_name}")
                            print("Errore nel trovare il valore richiesto")
                            print(f"Link al pdf: {status_link}")
                    except requests.RequestException as e:
                        print(f"Error accessing attachment {status_link}: {e}")
                    except Exception as e:
                        print(f"Errore nell'apertura del pdf")
                        print(f"Link al pdf: {status_link}")
    else:
        print(f"Ingredient containing '{ingredient_name}' not found in the data file.")

# Example usage
ingredient_name = "Lactic Acid"
data_file_path = "C:/Users/AndreaFumagalli/OneDrive - ITS Angelo Rizzoli/Documenti/GitHub/ProjectWork/DATASET.txt"
noael_file_path = "C:/Users/AndreaFumagalli/OneDrive - ITS Angelo Rizzoli/Documenti/GitHub/ProjectWork/NOAELVALUES.txt"

find_ingredient_id_and_extract_link(ingredient_name, data_file_path, noael_file_path)