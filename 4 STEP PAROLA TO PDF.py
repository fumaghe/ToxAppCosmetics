import requests
from bs4 import BeautifulSoup

def extract_first_status_link(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad status codes
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the first link in the "Status" column of the table
        status_link = soup.find('table').find_all('tr')[1].find('a')['href']
        
        # Fix the URL by removing '../' and concatenating with base URL
        full_status_link = "https://cir-reports.cir-safety.org/" + status_link.replace("../", "")
        
        return full_status_link

    except requests.RequestException as e:
        print(f"Error accessing {url}: {e}")
    except (IndexError, TypeError) as e:
        print(f"Error parsing the page: {e}")

def find_ingredient_id_and_extract_link(ingredient_name, data_file_path):
    with open(data_file_path, 'r', encoding='utf-8') as file:
        ingredients = []  # List of tuples (ingredient_name, ingredient_id)
        for line in file:
            data = eval(line.strip())
            search_name = ingredient_name.lower()  # Convert search term to lowercase

            # Check for ingredient name substring in both fields
            if (search_name in data['pcpc_ingredientname'].lower() or
                search_name in data['pcpc_ciringredientname'].lower()):
                ingredients.append((data['pcpc_ingredientname'], data['pcpc_ingredientid']))

    if ingredients:
        # Extract link for each ingredient found
        for ingredient_name, ingredient_id in set(ingredients):  # Convert list to set for unique entries
            url = f"https://cir-reports.cir-safety.org/cir-ingredient-status-report/?id={ingredient_id}"
            status_link = extract_first_status_link(url)
            if status_link:
                print(f"Ingredient name: {ingredient_name}")
                print(f"First status link: {status_link}")
    else:
        print(f"Ingredient containing '{ingredient_name}' not found in the data file.")

# Example usage
ingredient_name = "Octyldodecyl Meadowfoamate"  # User input for ingredient
data_file_path = "C:\\Users\AndreaFumagalli\OneDrive - ITS Angelo Rizzoli\Documenti\GitHub\ProjectWork\DATASET.txt"  # Replace with your actual file path

find_ingredient_id_and_extract_link(ingredient_name, data_file_path)