import ast
import re

# Function to preserve newlines in specific fields like "Diagnosi" and clean elsewhere
def clean_and_convert_to_dict(data):
    # Step 1: Preserve newlines in the "Diagnosi" field
    # Use a regex to find the "Diagnosi" field and temporarily replace newlines with a placeholder
    data = re.sub(r'("Diagnosi"\s*:\s*")(.*?)(")', 
                  lambda m: m.group(1) + m.group(2).replace('\n', '<NEWLINE>') + m.group(3), 
                  data, 
                  flags=re.DOTALL)
    

    # Step 2: Remove all other newlines in the data
    data = data.replace('\n', '')
    print(data)
    
    # Correct JSON-style true/false/null to Python equivalents
    data = data.replace('true', 'True').replace('false', 'False').replace('null', 'None')

    try:
        # Use ast.literal_eval to safely evaluate the string to a Python dictionary
        python_dict = ast.literal_eval(data)
        return python_dict
    except (SyntaxError, ValueError) as e:
        print(f"Error during conversion: {e}")
        return None

# Read the file content
file_path = 'raw_response.txt'

with open(file_path, 'r', encoding='utf-8') as f:
    raw_data = f.read()

# Apply the cleaning and conversion
python_dict = clean_and_convert_to_dict(raw_data)

if python_dict:
    print("Conversion successful!")
    # Write the dictionary to a text file
    output_file_path = 'output.txt'

    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.write(str(python_dict))

    print(f"Dictionary written to {output_file_path}")
else:
    print("Conversion failed.")