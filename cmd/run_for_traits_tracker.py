import json

from preprocessor import traits_processor
from utils import file_processor

def main():
    json_file = "./var/traits_units.json"
    with open(json_file, 'r', encoding='utf-8') as f:
        traits_data = json.load(f)
    
    try:
        result = traits_processor.traits_tracker(traits_data)
        
        # Print the result in a formatted way
        print(json.dumps(result, indent=4))
        
    except FileNotFoundError:
        print(f"Error: File '{json_file}' not found")
    except Exception as e:
        print(f"Error occurred: {str(e)}")

    # Save the result to a JSON file
    file_processor.write_json("./var/traits_tracker_result.json", result)

if __name__ == "__main__":
    main()