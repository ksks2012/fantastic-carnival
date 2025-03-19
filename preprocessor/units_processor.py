import json

def parse_traits(original_data: dict) -> dict:
    # Create a new dictionary to map units to their traits
    units_traits_dict = {}

    # Iterate over each trait
    for trait_name, trait_data in original_data.items():
        units = trait_data.get("units", [])
        for unit in units:
            # If the unit is not already in the dictionary, initialize an empty list
            if unit not in units_traits_dict:
                units_traits_dict[unit] = []
            # Add the trait to the unit's list
            units_traits_dict[unit].append(trait_name)

    return units_traits_dict


