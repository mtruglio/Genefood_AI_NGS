import os
import ast

# Function to find duplicates in food lists across subkeys
def find_duplicates_in_subkeys(data, key, filename):
    errors = []
    subkeys = ["Consigliati", "Tollerati", "Sconsigliati"]

    # To store foods for comparison across subkeys
    food_dict = {}

    # Loop through each subkey and collect the food items
    for subkey in subkeys:
        if subkey in data[key]:
            for category, items_dict in data[key][subkey].items():
                # Get the 'items' and split them by commas, cleaning the extra spaces
                if 'items' in items_dict and items_dict['items']:
                    food_list = [item.strip().lower() for item in items_dict['items'].split(',')]
                    # Check if the food is already in another subkey
                    for food in food_list:
                        if food in food_dict:
                            errors.append(f"Duplicate food '{food}' found in '{key}' under both '{food_dict[food]}' and '{subkey}'")
                        else:
                            food_dict[food] = subkey
    
    # Log errors for the current file
    if errors:
        print(f"Duplicate errors in {key} for file {filename}:")
        for error in errors:
            print(f" - {error}")
    else:
        print(f"No duplicates found in {key} for file {filename}.")

# Iterate through files in a directory and process each one
def process_directory(directory):
    for filename in os.listdir(directory):
        if filename.endswith(".txt"):
            filepath = os.path.join(directory, filename)
            try:
                # Read and evaluate the content of the file as a Python dictionary
                with open(filepath, 'r', encoding='utf-8') as file:
                    content = file.read()
                    # Try to safely evaluate the text as a Python dictionary
                    try:
                        data = ast.literal_eval(content)
                        
                        # Check for duplicates in each key
                        main_keys = ["Proteine", "Carboidrati", "Lipidi"]
                        for key in main_keys:
                            if key in data:
                                find_duplicates_in_subkeys(data, key, filename)
                            else:
                                print(f"Missing key {key} in file {filename}.")
                    except (ValueError, SyntaxError) as e:
                        print(f"Error evaluating {filename}: {str(e)}")
            except Exception as e:
                print(f"Error reading {filename}: {str(e)}")

# Replace 'your_directory' with the path to the directory containing your .txt files
process_directory('./')
