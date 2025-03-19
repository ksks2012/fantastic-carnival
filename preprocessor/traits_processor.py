import json
import re

from bs4 import BeautifulSoup
from itertools import combinations

from preprocessor import units_processor
from utils import file_processor

def parse_tft_origins(html_file) -> (dict, dict, dict):
    # Read the HTML file
    with open(html_file, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')

    # Dictionary to store traits with units and activation requirements
    traits_dict = {}

    # Find all trait sections
    trait_sections = soup.find_all('div', class_='set-trait')

    for trait_section in trait_sections:
        # Extract trait name
        trait_name_elem = trait_section.find('h4', class_='trait-name')
        if trait_name_elem:
            trait_name = trait_name_elem.text.strip()
        else:
            continue  # Skip if no trait name found
        
        # Find all champion items within this trait
        champion_items = trait_section.find_all('a', class_='characters-item')
        units = []
        for item in champion_items:
            champion_wrapper = item.find('div', class_='character-wrapper')
            if champion_wrapper:
                img_elem = champion_wrapper.find('img')
                if img_elem and 'alt' in img_elem.attrs:
                    unit_name = img_elem['alt'].strip()
                    units.append(unit_name)
        
        # Extract activation requirements and bonuses
        bonus_list = trait_section.find('ul', class_='trait-bonus-list')
        activations = {}
        if bonus_list:
            bonus_items = bonus_list.find_all('li', class_='trait-bonus-item')
            for item in bonus_items:
                count_elem = item.find('span', class_='trait-bonus-count')
                if count_elem:
                    count = count_elem.text.strip()
                    bonus_text = item.text.strip().replace(count, '').strip()  # Remove the count from the bonus text
                    bonus_text = re.sub(r'\s+', ' ', bonus_text.replace('\n', ' '))
                    activations[count] = bonus_text
        
        # Structure the trait data
        traits_dict[trait_name] = {
            "units": units,
            "activations": activations
        }

    cost_units_dict = {}
    # Find all champion sections
    champions = soup.find_all('div', class_='set-champion')

    for champion in champions:
        # Extract cost
        cost_elem = champion.find('div', class_='champion-cost-value')
        if cost_elem:
            cost = cost_elem.text.strip()
            
            # Extract unit name
            name_elem = champion.find('h4', class_='champion-name')
            if name_elem:
                unit_name = name_elem.text.strip()
                
                # Add to dictionary, creating list if cost doesn't exist yet
                if cost not in cost_units_dict:
                    cost_units_dict[cost] = []
                cost_units_dict[cost].append(unit_name)

    units_traits_dict = units_processor.parse_traits(traits_dict)

    return traits_dict, units_traits_dict, cost_units_dict

def traits_tracker(traits_data):
    # Filter out traits with only one unit
    valid_traits = {trait: info for trait, info in traits_data.items() if len(info["units"]) > 1}

    # Get all unique units
    all_units = set()
    for trait in valid_traits.values():
        all_units.update(trait["units"])

    # Function to get minimum activation requirement for a trait
    def get_min_activation(trait_data):
        activations = trait_data["activations"]
        return min(int(level) for level in activations.keys())

    # Function to count activated traits for a given combination
    def count_activated_traits(combo):
        combo_set = set(combo)
        activated = set()
        
        for trait_name, trait_data in valid_traits.items():
            trait_units = set(trait_data["units"])
            units_in_combo = len(trait_units & combo_set)
            min_activation = get_min_activation(trait_data)
            
            if units_in_combo >= min_activation:
                activated.add(trait_name)
        
        return len(activated), activated

    # Find combinations and limit the number
    def find_combinations(max_combinations=10):
        valid_combinations = []
        for combo in combinations(all_units, 8):
            count, activated_traits = count_activated_traits(combo)
            if count >= 8:
                valid_combinations.append({
                    "units": list(combo),
                    "trait_count": count,
                    "activated_traits": list(activated_traits)
                })
                # Stop when the maximum number is reached
                if len(valid_combinations) >= max_combinations:
                    break
        
        # Sort by the number of activated traits (descending)
        valid_combinations.sort(key=lambda x: x["trait_count"], reverse=True)
        return valid_combinations

    max_results = 5  # Set the desired maximum number of combinations
    results = find_combinations(max_combinations=max_results)

    # Print results
    print(f"Found {len(results)} combinations with 8 units activating 8 or more traits")
    print("\nTop 5 combinations:")
    for i, combo in enumerate(results[:5], 1):
        print(f"\nCombination {i}:")
        print(f"Units: {', '.join(combo['units'])}")
        print(f"Activated Traits ({combo['trait_count']}): {', '.join(combo['activated_traits'])}")

    return results

def main():
    html_file = './var/tft_traits.html'
    
    try:
        traits_data, units_data, costs_data = parse_tft_origins(html_file)
        
        # Print the result in a formatted way
        import json
        print(json.dumps(traits_data, indent=4))
        print(json.dumps(units_data, indent=4))
        
    except FileNotFoundError:
        print(f"Error: File '{html_file}' not found")
    except Exception as e:
        print(f"Error occurred: {str(e)}")

    # Save the result to a JSON file
    file_processor.write_json("./var/traits_units.json", traits_data)
    file_processor.write_json("./var/units_traits.json", units_data)
    file_processor.write_json("./var/cost_units.json", costs_data)

if __name__ == "__main__":
    main()