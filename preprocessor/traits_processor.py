import json
import re

from bs4 import BeautifulSoup
from collections import defaultdict, Counter
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
    valid_traits = {trait: info for trait, info in traits_data.items() if len(info["units"]) > 1}
    unit_costs = {unit: int(cost) for cost, units in cost_data.items() for unit in units}
    
    unit_to_traits = defaultdict(set)
    min_activations = {}
    for trait, data in valid_traits.items():
        min_activations[trait] = min(int(level) for level in data["activations"].keys())
        for unit in data["units"]:
            unit_to_traits[unit].add(trait)
    
    all_units = sorted(unit_costs.keys(), key=unit_costs.get)

    def count_traits(units):
        trait_counts = defaultdict(int)
        for unit in units:
            for trait in unit_to_traits[unit]:
                trait_counts[trait] += 1
        activated = {trait for trait, count in trait_counts.items() if count >= min_activations[trait]}
        return len(activated), activated

    def greedy_start():
        selected = []
        covered_traits = set()
        available_units = all_units.copy()
        
        while len(selected) < combo_size and available_units:
            best_unit = max(available_units, 
                          key=lambda u: len(unit_to_traits[u] - covered_traits), 
                          default=None)
            if not best_unit or len(unit_to_traits[best_unit] - covered_traits) == 0:
                break
            selected.append(best_unit)
            covered_traits.update(unit_to_traits[best_unit])
            available_units.remove(best_unit)
        
        return selected[:combo_size] if len(selected) >= combo_size else None

    def build_combinations():
        results = []
        initial_combo = greedy_start()
        if not initial_combo:
            return results

        # Use generator to produce combinations one by one
        def generate_combinations(index, current_combo, current_traits):
            if len(current_combo) == combo_size:
                trait_count, activated_traits = count_traits(current_combo)
                if trait_count >= 8:
                    total_cost = sum(unit_costs[u] for u in current_combo)
                    yield {
                        "units": current_combo[:],
                        "trait_count": trait_count,
                        "activated_traits": sorted(activated_traits),
                        "total_cost": total_cost
                    }
                return
            
            # Pruning: if the current number of traits + the maximum number of traits that can be contributed by the remaining selectable units < 8, stop
            remaining_slots = combo_size - len(current_combo)
            potential_traits = len(set().union(*(unit_to_traits[all_units[i]] for i in range(index, len(all_units)))) - current_traits)
            if len(current_traits) + potential_traits < 8:
                return

            for i in range(index, len(all_units)):
                unit = all_units[i]
                new_traits = unit_to_traits[unit]
                current_combo.append(unit)
                yield from generate_combinations(i + 1, current_combo, current_traits | new_traits)
                current_combo.pop()
                if len(results) >= max_combinations:
                    break

        # Collect results
        for combo in generate_combinations(0, [], set()):
            results.append(combo)
            if len(results) >= max_combinations:
                break
        
        return sorted(results, key=lambda x: (x["total_cost"], -x["trait_count"]))

    results = build_combinations()

    print(f"Found {len(results)} combinations with {combo_size} units activating 8 or more traits")
    if results:
        print(f"\nTop {min(max_combinations, 3)} combinations (sorted by total cost, then trait count):")
        for i, combo in enumerate(results[:3], 1):
            print(f"\nCombination {i}:")
            print(f"Units: {', '.join(combo['units'])}")
            print(f"Total Cost: {combo['total_cost']}")
            print(f"Activated Traits ({combo['trait_count']}): {', '.join(combo['activated_traits'])}")
    else:
        print("No combinations found.")

    return results

def freq_analysis(traits_tracker_result: dict) -> dict:
    unit_frequency = Counter()
    for combo in traits_tracker_result:
        unit_frequency.update(combo["units"])
    
    return dict(sorted(unit_frequency.items(), key=lambda x: x[1], reverse=True))

def main():
    html_file = './var/tft_traits.html'
    
    try:
        traits_data, units_data, costs_data = parse_tft_origins(html_file)        
    except FileNotFoundError:
        print(f"Error: File '{html_file}' not found")
    except Exception as e:
        print(f"Error occurred: {str(e)}")

    # Save the result to a JSON file
    file_processor.write_json("./var/traits_units_activations.json", traits_data)
    file_processor.write_json("./var/units_traits.json", units_data)
    file_processor.write_json("./var/costs_units.json", costs_data)

if __name__ == "__main__":
    main()