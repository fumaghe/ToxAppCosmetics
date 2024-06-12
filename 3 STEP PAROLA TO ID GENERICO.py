# -*- coding: utf-8 -*-
"""
Created on Tue Jun 11 19:02:31 2024

@author: AndreaFumagalli
"""

import webbrowser

def find_ingredient_id(ingredient_name, data_file_path):

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
    # Print ingredient name and ID for all found ingredients (no duplicates)
    for ingredient_name, ingredient_id in set(ingredients):  # Convert list to set for unique entries
      print(f"Ingredient name: {ingredient_name} - Ingredient ID: {ingredient_id}")
  else:
    print(f"Ingredient containing '{ingredient_name}' not found in the data file.")

# Example usage
ingredient_name = "DeCeth-5"  # User input for ingredient
data_file_path = "C:\Users\AndreaFumagalli\OneDrive - ITS Angelo Rizzoli\Documenti\GitHub\ProjectWork\DATASET.txt"  # Replace with your actual file path

find_ingredient_id(ingredient_name, data_file_path)