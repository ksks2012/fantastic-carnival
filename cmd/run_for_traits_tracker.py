import json

from preprocessor import traits_processor
from utils import file_processor

def main():
    traits_file = "./var/traits_units.json"
    costs_file = "./var/costs_units.json"
    
    try:
        traits_data = file_processor.read_json(traits_file)
        costs_data = file_processor.read_json(costs_file)

        result = traits_processor.traits_tracker(traits_data, costs_data)
        
        # Print the result in a formatted way
        print(json.dumps(result, indent=4))
        
    except FileNotFoundError:
        print(f"Error: File '{traits_file}' or '{costs_file}' not found")
    except Exception as e:
        print(f"Error occurred: {str(e)}")

    # Save the result to a JSON file
    file_processor.write_json("./var/traits_tracker_result.json", result)

if __name__ == "__main__":
    main()