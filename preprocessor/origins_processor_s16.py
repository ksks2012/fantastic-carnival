from bs4 import BeautifulSoup
import re

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
    # Look for character cards and their traits - use more flexible selector
    character_cards = soup.find_all('div', class_=lambda x: x and 'rounded text-white1' in x and 'flex flex-col' in x)
    
    # Dictionary to store character to traits mapping
    character_traits = {}
    
    for card in character_cards:
        # Extract character name from the card
        name_div = card.select_one('div[class*="font-montserrat"][class*="font-semibold"]')
        if not name_div:
            continue
        
        character_name = name_div.text.strip()
        # Remove cost number if it exists
        character_name = character_name.split('\n')[0].strip()
        # Clean name by removing cost digits at the end
        import re
        character_name = re.sub(r'\d+$', '', character_name).strip()
        
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

def extract_unlock_heroes(unlock_html_file='./var/tft_origins_unlock.html', origins_html_file='./var/tft_origins.html'):
    """Extract heroes that need to be unlocked and their unlock conditions from both HTML files"""
    
    unlock_heroes = {}
    
    # Check both HTML files for unlock heroes
    html_files = [unlock_html_file, origins_html_file]
    
    for html_file in html_files:
        try:
            print(f"Checking {html_file} for unlock heroes...")
            
            # Read HTML file
            with open(html_file, 'r', encoding='utf-8') as file:
                html_content = file.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find all hero cards - use flexible selector
            hero_cards = soup.find_all('div', class_=lambda x: x and 'rounded text-white1' in x and 'flex flex-col' in x)
            
            file_unlock_count = 0
            
            for card in hero_cards:
                # Get hero name - try multiple selectors
                hero_name_element = card.find('div', class_='relative flex justify-between p-[9px] bg-bg text-[18px] font-montserrat font-semibold rounded-[3px] css-kuoeib')
                if not hero_name_element:
                    hero_name_element = card.select_one('div[class*="font-montserrat"][class*="font-semibold"]')
                
                if not hero_name_element:
                    continue
                    
                hero_name = hero_name_element.get_text().strip()
                # Remove cost digits
                hero_name = re.sub(r'\d+$', '', hero_name).strip()
                
                # Look for unlock section
                unlock_section = card.find('h4', class_='h4 mb-1', string='Unlock:')
                if unlock_section:
                    unlock_condition = unlock_section.find_next_sibling('div')
                    if unlock_condition:
                        condition_text = unlock_condition.get_text().strip()
                        if hero_name not in unlock_heroes:  # Avoid duplicates
                            unlock_heroes[hero_name] = condition_text
                            file_unlock_count += 1
            
            print(f"Found {file_unlock_count} unlock heroes in {html_file}")
            
        except FileNotFoundError:
            print(f"File {html_file} not found, skipping...")
        except Exception as e:
            print(f"Error processing {html_file}: {e}")
    
    print(f"Total found: {len(unlock_heroes)} unique unlock heroes")
    
    # Display all unlock heroes and conditions
    for hero, condition in sorted(unlock_heroes.items()):
        print(f"{hero}: {condition}")
    
    return unlock_heroes


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
        
        # Extract unlock heroes data from unlock-specific HTML file
        unlock_heroes_data = extract_unlock_heroes()
        
        # Save unlock heroes to JSON file
        file_processor.write_json("./var/unlock_heroes.json", unlock_heroes_data)
        
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