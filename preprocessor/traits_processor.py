import re

from bs4 import BeautifulSoup

from preprocessor import units_processor
from utils import file_processor

def parse_tft_origins(html_file) -> (dict, dict):
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

    units_traits_dict = units_processor.parse_traits(traits_dict)

    return traits_dict, units_traits_dict

def main():
    html_file = './var/tft_traits.html'
    
    try:
        traits_data, units_data = parse_tft_origins(html_file)
        
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

if __name__ == "__main__":
    main()