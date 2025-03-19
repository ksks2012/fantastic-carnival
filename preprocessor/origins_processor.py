from bs4 import BeautifulSoup

from utils import file_processor

def parse_tft_origins(html_file):
    # Read the HTML file
    with open(html_file, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')

    # Initialize the origins dictionary
    origins = {}

    # Find all table rows containing origin data
    table_rows = soup.select('.rt-tr-group .rt-tr')

    for row in table_rows:
        # Extract origin name
        origin_cell = row.select_one('.rt-td:nth-child(1) .characters-item.trait-table')
        if not origin_cell:
            continue
            
        origin_name = origin_cell.find('div', class_='d-none d-md-block')
        if origin_name:
            origin_name = ' '.join(origin_name.text.strip().split())
        else:
            # Fallback to image alt text if name div not found
            origin_img = origin_cell.find('img')
            origin_name = origin_img['alt'] if origin_img else None

        if not origin_name:
            continue

        # Extract units
        units_cell = row.select_one('.rt-td:nth-child(3) .table-images')
        if not units_cell:
            continue

        units = []
        for unit_link in units_cell.find_all('a', class_='characters-item'):
            unit_img = unit_link.find('img', class_='character-icon')
            if unit_img and 'alt' in unit_img.attrs:
                unit_name = unit_img['alt']
                print(unit_name)
                units.append(unit_name)

        # Add to origins dictionary
        origins[origin_name] = units

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