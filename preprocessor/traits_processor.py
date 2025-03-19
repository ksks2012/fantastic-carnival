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

def traits_tracker(traits_data, cost_data, max_combinations=10, combo_size=8):
    # Filter out traits with only one unit
    valid_traits = {trait: info for trait, info in traits_data.items() if len(info["units"]) > 1}

    # Get all unique units and their costs
    unit_costs = {}
    for cost, units in cost_data.items():
        for unit in units:
            unit_costs[unit] = int(cost)

    all_units = set()
    for trait in valid_traits.values():
        all_units.update(trait["units"])

    # Sort units by cost (ascending) to prioritize lower-cost units
    sorted_units = sorted(all_units, key=lambda x: unit_costs[x])

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

    # Calculate total cost of a combination
    def calculate_total_cost(combo):
        return sum(unit_costs[unit] for unit in combo)

    # Find combinations, prioritizing lower costs
    def find_combinations(max_combinations):
        valid_combinations = []
        seen_combinations = set()  # To avoid duplicates
        
        # Generate combinations from sorted units (lower costs first)
        for combo in combinations(sorted_units, combo_size):
            combo_tuple = tuple(sorted(combo))  # Sort for consistent comparison
            if combo_tuple in seen_combinations:
                continue
            seen_combinations.add(combo_tuple)
            
            count, activated_traits = count_activated_traits(combo)
            if count >= 8:  # Minimum 8 traits activated
                total_cost = calculate_total_cost(combo)
                valid_combinations.append({
                    "units": list(combo),
                    "trait_count": count,
                    "activated_traits": list(activated_traits),
                    "total_cost": total_cost
                })
                if len(valid_combinations) >= max_combinations:
                    break
        
        # Sort by total cost (ascending) and then by trait count (descending)
        valid_combinations.sort(key=lambda x: (x["total_cost"], -x["trait_count"]))
        return valid_combinations

    max_results = min(max_combinations, 5)  # Limit to top 5 or max_combinations
    results = find_combinations(max_combinations=max_combinations)

    # Print results
    print(f"Found {len(results)} combinations with {combo_size} units activating 8 or more traits")
    print(f"\nTop {max_results} combinations (sorted by total cost, then trait count):")
    for i, combo in enumerate(results[:max_results], 1):
        print(f"\nCombination {i}:")
        print(f"Units: {', '.join(combo['units'])}")
        print(f"Total Cost: {combo['total_cost']}")
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
    file_processor.write_json("./var/costs_units.json", costs_data)

if __name__ == "__main__":
    main()