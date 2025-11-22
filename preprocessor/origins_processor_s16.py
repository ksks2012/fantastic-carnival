from bs4 import BeautifulSoup

from utils import file_processor

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
        origins_data = parse_tft_origins(html_file)
        
        # Print the result in a formatted way
        import json
        print(json.dumps(origins_data, indent=4))
        
    except FileNotFoundError:
        print(f"Error: File '{html_file}' not found")
    except Exception as e:
        print(f"Error occurred: {str(e)}")

    # Save the result to a JSON file
    file_processor.write_json("./var/origins_units.json", origins_data)

if __name__ == "__main__":
    main()