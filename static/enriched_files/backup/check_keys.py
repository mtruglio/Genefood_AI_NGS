import os
import ast

# Define the expected structure
required_structure = {
    "Proteine": ["PESCE", "CARNE", "ALIMENTI DI ORIGINE VEGETALE", "LEGUMI", "UOVA"],
    "Carboidrati": ["CEREALI", "PSEUDO-CEREALI", "FRUTTA"],
    "Lipidi": ["GRASSI MONOINSATURI E POLINSATURI", "GRASSI SATURI"]
}

def check_structure(d):
    if not isinstance(d, dict):
        return False, "File does not contain a dictionary."

    # Check for main keys
    for main_key in ["Proteine", "Carboidrati", "Lipidi"]:
        if main_key not in d:
            return False, f"Key '{main_key}' is missing."

        for sub_key in ["Consigliati", "Tollerati", "Sconsigliati"]:
            if sub_key not in d[main_key]:
                return False, f"Sub-key '{sub_key}' is missing under '{main_key}'."

            # Check for specific categories within each main key
            expected_keys = required_structure[main_key]
            for cat in expected_keys:
                if cat not in d[main_key][sub_key]:
                    return False, f"Category '{cat}' is missing under '{main_key}' -> '{sub_key}'."

                elif d[main_key][sub_key][cat] and "items" not in d[main_key][sub_key][cat]:
                            return False, f"Missing 'items' in {cat} under {main_key} -> {sub_key}"

    return True, "Structure is correct."

def process_file(file_path):
    try:
        # Open the file and attempt to parse it as a Python dictionary
        with open(file_path, 'r') as f:
            content = f.read()
            try:
                data = ast.literal_eval(content)  # Safely evaluate the string as a Python literal (like a dict)
            except (SyntaxError, ValueError) as e:
                return False, f"Error parsing dictionary: {str(e)}"

            # Check structure
            valid, message = check_structure(data)
            return valid, message

    except Exception as e:
        return False, f"Failed to process file: {str(e)}"

# Directory containing the text files
directory = "./"

# Iterate through files in the directory
for filename in os.listdir(directory):
    if filename.endswith(".txt"):
        file_path = os.path.join(directory, filename)
        is_valid, message = process_file(file_path)
        print(f"File: {filename} -> {message}")
