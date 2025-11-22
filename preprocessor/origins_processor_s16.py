from bs4 import BeautifulSoup

from utils import file_processor

def extract_units_cost(html_file):
    # Read the HTML file
    with open(html_file, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')

    # Dictionary to store character name and cost mapping
    units_cost = {}
    
    # Look for character cards
    character_cards = soup.find_all('div', class_='rounded text-white1 w-[291px] flex flex-col bg-bg')
    
    for card in character_cards:
        # Extract character name and cost from the card
        name_cost_div = card.select_one('.font-montserrat.font-semibold')
        if not name_cost_div:
            continue
        
        # Get the full text which contains both name and cost
        full_text = name_cost_div.get_text()
        
        # Extract cost from the cost display element
        cost_div = card.select_one('.flex.items-end')
        if not cost_div:
            continue
            
        # Get cost number (usually the first text node in cost div)
        cost_text = cost_div.get_text().strip()
        try:
            # Extract the number from cost text (format like "4" or "4 gold")
            cost = int(''.join(filter(str.isdigit, cost_text)))
        except (ValueError, TypeError):
            continue
        
        # Clean character name by removing cost and extra whitespace
        character_name = full_text.split('\n')[0].strip()
        
        # Remove cost number from the character name (e.g., "Anivia1" -> "Anivia")
        import re
        character_name_clean = re.sub(r'\d+$', '', character_name).strip()
        
        if character_name_clean and cost:
            units_cost[character_name_clean] = cost
            print(f"Found character: {character_name_clean} with cost: {cost}")
    
    return units_cost

def parse_tft_origins(html_file):
    # Read the HTML file
    with open(html_file, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')

    # Initialize the origins dictionary
    origins = {}
    
    # This appears to be a modern React app, so we need to extract data differently
    # Look for character cards and their traits
    character_cards = soup.find_all('div', class_='rounded text-white1 w-[291px] flex flex-col bg-bg')
    
    # Dictionary to store character to traits mapping
    character_traits = {}
    
    for card in character_cards:
        # Extract character name from the card
        name_div = card.select_one('.font-montserrat.font-semibold')
        if not name_div:
            continue
        
        character_name = name_div.text.strip()
        # Remove cost number if it exists
        character_name = character_name.split('\n')[0].strip()
        
        # Extract traits from the card
        trait_imgs = card.select('img[alt*=" 0"]')  # Trait images have " 0" in alt text
        traits = []
        
        for trait_img in trait_imgs:
            alt_text = trait_img.get('alt', '')
            if ' 0' in alt_text:
                trait_name = alt_text.replace(' 0', '').strip()
                traits.append(trait_name)
        
        if character_name and traits:
            character_traits[character_name] = traits
            print(f"Found character: {character_name} with traits: {traits}")
    
    # Now group characters by their origins/traits
    for character, traits in character_traits.items():
        for trait in traits:
            if trait not in origins:
                origins[trait] = []
            origins[trait].append(character)
    
    return origins

def main():
    html_file = './var/tft_origins.html'
    
    try:
        # Extract units cost data
        units_cost_data = extract_units_cost(html_file)
        
        # Print the units cost result
        import json
        print("Units Cost Data:")
        print(json.dumps(units_cost_data, indent=4, ensure_ascii=False))
        
        # Save units cost to JSON file
        file_processor.write_json("./var/units_cost.json", units_cost_data)
        
        # Also extract origins data as before
        origins_data = parse_tft_origins(html_file)
        
        # Save the origins result to a JSON file
        file_processor.write_json("./var/origins_units.json", origins_data)
        
    except FileNotFoundError:
        print(f"Error: File '{html_file}' not found")
    except Exception as e:
        print(f"Error occurred: {str(e)}")

if __name__ == "__main__":
    main()