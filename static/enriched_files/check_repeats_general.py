import os
import ast

# Function to check for duplicate food items across the whole document
def check_for_global_duplicates(data, filename):
    all_foods = {}
    categories = ["Proteine", "Carboidrati", "Lipidi"]
    subkeys = ["Consigliati", "Tollerati", "Sconsigliati"]
    errors = []

    # Loop through each category and subkey
    for category in categories:
        if category in data:
            for subkey in subkeys:
                if subkey in data[category]:
                    for subcategory, items_dict in data[category][subkey].items():
                        if 'items' in items_dict and items_dict['items']:
                            food_list = [item.strip().lower() for item in items_dict['items'].split(',')]
                            
                            # Check for duplicates across all categories
                            for food in food_list:
                                if food in all_foods:
                                    # Log the duplication warning
                                    errors.append(f"Duplicate food '{food}' found in '{category}' -> '{subkey}' -> '{subcategory}' and '{all_foods[food]['category']}' -> '{all_foods[food]['subkey']}' -> '{all_foods[food]['subcategory']}'")
                                else:
                                    # Store where the food was first found
                                    all_foods[food] = {
                                        'category': category,
                                        'subkey': subkey,
                                        'subcategory': subcategory
                                    }
    
    # Log errors for the current file if any duplicates are found
    if errors:
        print(f"Duplicate errors in file {filename}:")
        for error in errors:
            print(f" - {error}")
    else:
        print(f"No duplicates found in {filename}.")

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

                        # Check for global duplicates across all categories
                        check_for_global_duplicates(data, filename)

                    except (ValueError, SyntaxError) as e:
                        print(f"Error evaluating {filename}: {str(e)}")
            except Exception as e:
                print(f"Error reading {filename}: {str(e)}")

# Replace 'your_directory' with the path to the directory containing your .txt files
process_directory('./')
