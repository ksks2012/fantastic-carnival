import json
from collections import defaultdict

def check_duplicates_generator(combinations_file, output_file):
    seen_units = set()
    with open(output_file, "w", encoding="utf-8") as out_f:
        with open(combinations_file, "r", encoding="utf-8") as in_f:
            combinations = json.load(in_f)
            for i, combo in enumerate(combinations):
                units_set = frozenset(combo["units"])
                if units_set in seen_units:
                    out_f.write(f"Duplicate at index {i}: {json.dumps(combo)}\n")
                else:
                    seen_units.add(units_set)

def main():
    input_file = "./var/traits_tracker_result.json"
    output_file = "duplicates.txt"
    
    # Check for duplicates and write to file
    check_duplicates_generator(input_file, output_file)
    
    # Check if there are duplicates
    with open(output_file, "r", encoding="utf-8") as f:
        duplicates = f.readlines()
        if duplicates:
            print(f"Found {len(duplicates)} duplicate combinations, see {output_file} for details")
            for line in duplicates[:3]:  # Show the first 3
                print(line.strip())
        else:
            print("No duplicate combinations found.")

if __name__ == "__main__":
    main()