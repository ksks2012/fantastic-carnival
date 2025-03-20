import json
import time

from preprocessor import traits_processor
from utils import file_processor

def main():
    traits_tracker_file = "./var/traits_tracker_result.json"
    
    try:
        traits_tracker_data = file_processor.read_json(traits_tracker_file)

        result = traits_processor.freq_analysis(traits_tracker_data)
        
    except FileNotFoundError:
        print(f"Error: File '{traits_tracker_file}' not found")
    except Exception as e:
        print(f"Error occurred: {str(e)}")

    # Save the result to a JSON file
    file_processor.write_json("./var/freq_analysis_result.json", result)

if __name__ == "__main__":
    main()