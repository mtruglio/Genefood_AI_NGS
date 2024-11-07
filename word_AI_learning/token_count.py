import json
import tiktoken
import sys
def count_tokens(data, encoding):
    """Recursively count tokens in JSON data using tiktoken."""
    token_count = 0

    if isinstance(data, dict):
        for key, value in data.items():
            token_count += count_tokens(key, encoding)
            token_count += count_tokens(value, encoding)
    elif isinstance(data, list):
        for item in data:
            token_count += count_tokens(item, encoding)
    elif isinstance(data, str):
        token_count += len(encoding.encode(data))
    return token_count

def main():
    input_file = sys.argv[1]
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Choose the encoding that matches the model you want to use, for example, 'gpt-3.5-turbo'
    encoding = tiktoken.get_encoding('cl100k_base')
    
    total_tokens = count_tokens(data, encoding)
    
    # Print the total token count
    print(f'Total tokens: {total_tokens}')

if __name__ == "__main__":
    main()
