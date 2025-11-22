#!/usr/bin/env python3

import json
import re
from bs4 import BeautifulSoup
from utils import file_processor

def parse_traits_from_html(traits_html_file='./var/traits.html'):
    """Parse traits and their units from HTML file"""
    
    traits_data = {}
    
    try:
        print(f"Parsing traits from {traits_html_file}...")
        
        with open(traits_html_file, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')
        
        # Find all trait cards
        trait_cards = soup.find_all('div', class_=lambda x: x and 'p-4' in x and 'rounded' in x and 'text-white1' in x and 'bg-bg' in x)
        
        print(f"Found {len(trait_cards)} potential trait cards")
        
        for card in trait_cards:
            # Extract trait name
            trait_name = extract_trait_name(card)
            if not trait_name or trait_name == "Traits":  # Skip header
                continue
            
            # Extract units for this trait
            units = extract_units_from_card(card)
            
            # Extract activation levels and descriptions
            activations = extract_activations_from_card(card)
            
            if units:  # Only add if we found units
                traits_data[trait_name] = {
                    'units': units,
                    'activations': activations
                }
                print(f"Found trait: {trait_name} with {len(units)} units")
        
        print(f"Successfully parsed {len(traits_data)} traits")
        return traits_data
        
    except Exception as e:
        print(f"Error parsing {traits_html_file}: {e}")
        return {}

def extract_trait_name(card):
    """Extract trait name from a trait card"""
    
    # Try to find trait name in various ways
    # Method 1: Look for first significant text element
    name_elements = card.find_all(['div', 'span', 'h1', 'h2', 'h3'], limit=5)
    for elem in name_elements:
        text = elem.get_text(strip=True)
        # Skip if it's too long (likely description) or contains common words
        if text and len(text) < 30 and not any(word in text.lower() for word in ['after', 'each', 'combat', 'grants', 'your']):
            # Check if it looks like a trait name (starts with capital, no numbers)
            if text[0].isupper() and not text.replace(' ', '').replace('&', '').replace("'", '').isdigit():
                return text
    
    return None

def extract_units_from_card(card):
    """Extract unit names from a trait card"""
    
    units = []
    trait_name = extract_trait_name(card)
    
    # Look for unit images with alt text
    imgs = card.find_all('img')
    for img in imgs:
        alt_text = img.get('alt', '').strip()
        if alt_text and not any(skip_word in alt_text.lower() for skip_word in [
            'trait', 'ability', 'attack', 'damage', 'health', 'armor', 'magic', 'resistance'
        ]):
            # Clean up the alt text (remove numbers and special suffixes)
            clean_name = clean_unit_name(alt_text)
            # Skip if it's the same as trait name (trait icon)
            if clean_name and clean_name not in units and clean_name != trait_name:
                units.append(clean_name)
    
    return units

def clean_unit_name(name):
    """Clean unit name from alt text"""
    
    # Remove trailing numbers and common suffixes
    name = re.sub(r'\s*\d+$', '', name)  # Remove trailing numbers
    name = re.sub(r'\s*0$', '', name)    # Remove trailing 0
    
    # Skip if it's just a trait icon or generic term
    skip_names = {'0', '', 'trait', 'icon', 'ability', 'attack damage', 'ability power', 'health', 'armor', 'magic resistance'}
    if name.lower() in skip_names:
        return None
    
    # Skip if it's all numbers or too generic
    if name.replace(' ', '').isdigit() or len(name) < 2:
        return None
    
    return name

def extract_activations_from_card(card):
    """Extract activation levels and descriptions from a trait card"""
    
    activations = {}
    
    # Look for activation patterns in text
    all_text = card.get_text()
    
    # Pattern 1: Look for parenthesized numbers followed by descriptions
    # Handle cases where descriptions might be short or connect to next level
    activation_matches = re.finditer(r'\((\d+)\)\s*(.*?)(?=\(\d+\)|$)', all_text, re.DOTALL)
    
    for match in activation_matches:
        level = match.group(1)
        desc = match.group(2).strip()
        
        # Clean up description
        # Remove system variables like %i:scaleSerpents%
        desc = re.sub(r'%i:[^%]+%', '', desc)
        # Remove excessive whitespace and newlines
        desc = re.sub(r'\s+', ' ', desc).strip()
        
        # For very short descriptions, try to find meaningful content
        if len(desc) < 10:
            # Look for numbers or meaningful words
            if any(char.isdigit() for char in desc) or any(word in desc.lower() for word in ['armor', 'damage', 'health', 'mana', 'cost']):
                activations[level] = desc
        else:
            # Split long descriptions that might contain multiple levels
            # Look for pattern where next activation starts
            desc_parts = re.split(r'(?=\d+\s+[A-Z])', desc)
            if len(desc_parts) > 1:
                # Take only the first part
                desc = desc_parts[0].strip()
            
            if len(desc) > 2:
                activations[level] = desc
    
    # Pattern 2: Alternative pattern for slash-separated levels like "3/5/7"
    if not activations:
        # Look for patterns like "3/5/7: description"
        slash_pattern = re.search(r'(\d+(?:/\d+)+):\s*([^(\n]+)', all_text)
        if slash_pattern:
            levels = slash_pattern.group(1).split('/')
            desc = slash_pattern.group(2).strip()
            # Assign same description to all levels (might need manual refinement)
            for level in levels:
                activations[level] = desc
    
    # Pattern 3: Fallback - look for numbers followed by colon
    if not activations:
        activation_patterns = re.findall(r'(\d+):\s*([^0-9\n]+?)(?=\d+:|$)', all_text, re.MULTILINE)
        for level, desc in activation_patterns:
            desc = desc.strip()
            if len(desc) > 5:
                activations[level] = desc
    
    return activations

def main():
    # Parse traits from HTML
    traits_data = parse_traits_from_html()
    
    if traits_data:
        # Save to JSON file
        file_processor.write_json('./var/traits_units_activations.json', traits_data)
        print(f"Saved traits data to var/traits_units_activations.json")
        
        # Show summary
        print(f"\nSummary:")
        print(f"Total traits: {len(traits_data)}")
        
        # Show some examples
        print("\nSample traits:")
        for trait_name, data in list(traits_data.items())[:5]:
            print(f"  {trait_name}: {len(data['units'])} units, {len(data['activations'])} activations")
            if data['units']:
                print(f"    Units: {', '.join(data['units'][:3])}{'...' if len(data['units']) > 3 else ''}")

if __name__ == "__main__":
    main()
