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
        return None
    count = Counter(values)
    most_common_count = count.most_common(1)[0][1]
    most_common_values = [value for value, freq in count.items() if freq == most_common_count]
    return most_common_values, most_common_count

def check_and_append_noael(ingredient_id, noael_value, noael_file_path):
    with open(noael_file_path, 'a', encoding='utf-8') as file:
        file.write(f"{ingredient_id}:{noael_value}\n")

def find_ingredient_id_and_extract_link(ingredient_name, data_file_path, noael_file_path):
    # Load NOAEL values from the NOAEL file into a dictionary
    noael_dict = {}
    with open(noael_file_path, 'r', encoding='utf-8') as file:
        for line in file:
            if ':' in line:
                id_value_pair = line.strip().split(':')
                if len(id_value_pair) == 2:
                    noael_dict[id_value_pair[0]] = id_value_pair[1]

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
                print(f"NOAEL value: {noael_dict[ingredient_id]} mg/kg (from file)")
            else:
                url = f"https://cir-reports.cir-safety.org/cir-ingredient-status-report/?id={ingredient_id}"
                status_link = extract_first_status_link(url)
                if status_link:
                    try:
                        response = requests.get(status_link)
                        response.raise_for_status()
                        
                        pdf_text = extract_text_from_pdf(response.content)
                        noael_values = find_noael_values(pdf_text)
                        most_common_noael, most_common_count = find_most_common_noael(noael_values)
                        
                        if noael_values:
                            for value in most_common_noael:
                                print(f"Ingredient name: {ingredient_name}")
                                print(f"NOAEL value: {value} mg/kg")
                                check_and_append_noael(ingredient_id, value, noael_file_path)
                        else:
                            print(f"Ingredient name: {ingredient_name}")
                            print("No NOAEL values found.")
                    except requests.RequestException as e:
                        print(f"Error accessing attachment {status_link}: {e}")
                    except Exception as e:
                        print(f"Error reading PDF {status_link}: {e}")
    else:
        print(f"Ingredient containing '{ingredient_name}' not found in the data file.")

# Example usage
ingredient_name = "Hydrolyzed Kluyveromyces Extract"
data_file_path = "C:/Users/AndreaFumagalli/OneDrive - ITS Angelo Rizzoli/Documenti/GitHub/ProjectWork/DATASET.txt"
noael_file_path = "C:/Users/AndreaFumagalli/OneDrive - ITS Angelo Rizzoli/Documenti/GitHub/ProjectWork/NOAELVALUES.txt"

find_ingredient_id_and_extract_link(ingredient_name, data_file_path, noael_file_path)
