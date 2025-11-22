#!/usr/bin/env python3
import json
from pathlib import Path
from collections import Counter, defaultdict

class ComboChecker:
    def __init__(self):
        # Load reference data
        self.traits_data_path = Path('var/traits_units_activations.json')
        self.units_costs_path = Path('var/units_cost.json')
        self.combos_path = Path('var/all_valid_combos_optimized.json')
        
        with self.traits_data_path.open('r', encoding='utf-8') as f:
            self.traits_data = json.load(f)
        
        with self.units_costs_path.open('r', encoding='utf-8') as f:
            self.units_costs = json.load(f)
            
        # Target regions for validation
        self.target_regions = [
            'Bilgewater', 'Demacia', 'Freljord', 'Ionia', 'Ixtal', 
            'Noxus', 'Piltover', 'Shadow Isles', 'Shurima', 'Targon', 
            'Void', 'Yordle', 'Zaun'
        ]
        
        # Build unit -> traits mapping
        self.unit_traits = defaultdict(list)
        for trait_name, trait_data in self.traits_data.items():
            for unit in trait_data.get('units', []):
                self.unit_traits[unit].append(trait_name)
        
        # Parse trait thresholds
        self.trait_thresholds = {}
        for trait, info in self.traits_data.items():
            activations = info.get('activations', {}) or {}
            thresholds = []
            for k in activations.keys():
                try:
                    thresholds.append(int(k))
                except Exception:
                    continue
            thresholds.sort()
            if thresholds:
                self.trait_thresholds[trait] = thresholds
                
        print(f"Loaded {len(self.traits_data)} traits and {len(self.units_costs)} unit costs")
        print(f"Target regions: {len(self.target_regions)}")
        
    def validate_combo_file(self, combo_file_path=None):
        """Validate the entire combo file"""
        if combo_file_path is None:
            combo_file_path = self.combos_path
            
        if not combo_file_path.exists():
            print(f"ERROR: Combo file {combo_file_path} does not exist")
            return False
            
        try:
            with combo_file_path.open('r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in {combo_file_path}: {e}")
            return False
            
        # Validate file structure
        required_keys = ['search_parameters', 'total_combinations_found', 'combinations']
        for key in required_keys:
            if key not in data:
                print(f"ERROR: Missing required key '{key}' in combo file")
                return False
                
        search_params = data['search_parameters']
        total_found = data['total_combinations_found']
        combinations = data['combinations']
        
        print(f"Search Parameters:")
        for key, value in search_params.items():
            print(f"  {key}: {value}")
        print(f"Total combinations claimed: {total_found}")
        print(f"Actual combinations in file: {len(combinations)}")
        
        if total_found != len(combinations):
            print(f"WARNING: Claimed total ({total_found}) doesn't match actual count ({len(combinations)})")
            
        # Validate each combination
        valid_count = 0
        invalid_count = 0
        errors = []
        
        for i, combo in enumerate(combinations):
            is_valid, error_msgs = self.validate_single_combo(combo, search_params)
            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
                errors.extend([f"Combo {i+1}: {msg}" for msg in error_msgs])
                
        print(f"\nValidation Results:")
        print(f"  Valid combinations: {valid_count}")
        print(f"  Invalid combinations: {invalid_count}")
        print(f"  Success rate: {valid_count/(valid_count+invalid_count)*100:.1f}%")
        
        if invalid_count > 0:
            print(f"\nFirst 10 errors:")
            for error in errors[:10]:
                print(f"  {error}")
            if len(errors) > 10:
                print(f"  ... and {len(errors)-10} more errors")
                
        return invalid_count == 0
        
    def validate_single_combo(self, combo, search_params):
        """Validate a single combination"""
        errors = []
        
        # Check required fields
        required_fields = ['units', 'trait_count', 'activated_traits', 'total_cost', 'activated_details']
        for field in required_fields:
            if field not in combo:
                errors.append(f"Missing field '{field}'")
                
        if errors:
            return False, errors
            
        units = combo['units']
        trait_count = combo['trait_count']
        activated_traits = combo['activated_traits']
        total_cost = combo['total_cost']
        activated_details = combo['activated_details']
        
        # Check required units are present
        required_units = search_params.get('required_units', [])
        for req_unit in required_units:
            if req_unit not in units:
                errors.append(f"Missing required unit '{req_unit}'")
                
        # Check team size constraints
        team_size = len(units)
        min_units = search_params.get('start_units', 7)
        max_units = search_params.get('max_units', 8)
        if not (min_units <= team_size <= max_units):
            errors.append(f"Team size {team_size} not in range [{min_units}, {max_units}]")
            
        # Check cost constraint
        max_cost = search_params.get('max_cost', 50)
        if total_cost > max_cost:
            errors.append(f"Total cost {total_cost} exceeds maximum {max_cost}")
            
        # Validate cost calculation
        calculated_cost = 0
        for unit in units:
            if unit not in self.units_costs:
                errors.append(f"Unknown unit '{unit}'")
            else:
                calculated_cost += self.units_costs[unit]
                
        if calculated_cost != total_cost:
            errors.append(f"Cost mismatch: calculated {calculated_cost}, reported {total_cost}")
            
        # Validate trait calculations
        trait_counts = Counter()
        for unit in units:
            if unit in self.unit_traits:
                for trait in self.unit_traits[unit]:
                    trait_counts[trait] += 1
                    
        # Check activated traits
        expected_activated = {}
        for trait, count in trait_counts.items():
            if trait in self.trait_thresholds:
                thresholds = self.trait_thresholds[trait]
                valid_thresholds = [th for th in thresholds if th <= count]
                if valid_thresholds:
                    expected_activated[trait] = max(valid_thresholds)
                    
        # Validate activated_details matches calculation
        if set(expected_activated.keys()) != set(activated_details.keys()):
            missing = set(expected_activated.keys()) - set(activated_details.keys())
            extra = set(activated_details.keys()) - set(expected_activated.keys())
            if missing:
                errors.append(f"Missing activated traits: {missing}")
            if extra:
                errors.append(f"Extra activated traits: {extra}")
                
        for trait, expected_threshold in expected_activated.items():
            if trait in activated_details and activated_details[trait] != expected_threshold:
                errors.append(f"Trait {trait}: expected threshold {expected_threshold}, got {activated_details[trait]}")
                
        # Check activated_traits list matches activated_details keys
        if set(activated_traits) != set(activated_details.keys()):
            errors.append("activated_traits list doesn't match activated_details keys")
            
        # Check trait_count matches
        if trait_count != len(activated_details):
            errors.append(f"trait_count {trait_count} doesn't match activated traits count {len(activated_details)}")
            
        # Check target region requirement (at least 5)
        activated_regions = [trait for trait in activated_details.keys() if trait in self.target_regions]
        if len(activated_regions) < 5:
            errors.append(f"Only {len(activated_regions)} target regions activated, need at least 5: {activated_regions}")
            
        # Check for duplicate units
        if len(units) != len(set(units)):
            duplicates = [unit for unit in set(units) if units.count(unit) > 1]
            errors.append(f"Duplicate units found: {duplicates}")
            
        return len(errors) == 0, errors
        
    def inspect_combo(self, combo_index, combo_file_path=None):
        """Inspect a specific combination in detail"""
        if combo_file_path is None:
            combo_file_path = self.combos_path
            
        with combo_file_path.open('r', encoding='utf-8') as f:
            data = json.load(f)
            
        combinations = data['combinations']
        
        if combo_index < 0 or combo_index >= len(combinations):
            print(f"ERROR: Invalid combo index {combo_index}. Valid range: 0-{len(combinations)-1}")
            return
            
        combo = combinations[combo_index]
        
        print(f"\nDetailed Analysis of Combination #{combo_index + 1}:")
        print(f"Units: {combo['units']}")
        print(f"Total Cost: {combo['total_cost']}")
        print(f"Team Size: {len(combo['units'])}")
        print(f"Trait Count: {combo['trait_count']}")
        
        print(f"\nUnit Costs:")
        total_calc = 0
        for unit in combo['units']:
            cost = self.units_costs.get(unit, 0)
            total_calc += cost
            print(f"  {unit}: {cost}")
        print(f"  Total: {total_calc}")
        
        print(f"\nUnit Traits:")
        for unit in combo['units']:
            traits = self.unit_traits.get(unit, [])
            print(f"  {unit}: {traits}")
            
        print(f"\nActivated Traits:")
        target_region_count = 0
        for trait in sorted(combo['activated_traits']):
            threshold = combo['activated_details'].get(trait, 0)
            is_target = trait in self.target_regions
            if is_target:
                target_region_count += 1
            region_marker = " [TARGET REGION]" if is_target else ""
            print(f"  {trait}: threshold {threshold}{region_marker}")
            
        print(f"\nTarget Regions Activated: {target_region_count}/13")
        
        # Validate this specific combo
        is_valid, errors = self.validate_single_combo(combo, data['search_parameters'])
        if is_valid:
            print(f"\n✅ This combination is VALID")
        else:
            print(f"\n❌ This combination has ERRORS:")
            for error in errors:
                print(f"  - {error}")
    
    def summary_statistics(self, combo_file_path=None):
        """Generate summary statistics for the combo file"""
        if combo_file_path is None:
            combo_file_path = self.combos_path
            
        with combo_file_path.open('r', encoding='utf-8') as f:
            data = json.load(f)
            
        combinations = data['combinations']
        
        print(f"\nSummary Statistics:")
        print(f"Total combinations: {len(combinations)}")
        
        # Cost distribution
        costs = [combo['total_cost'] for combo in combinations]
        print(f"Cost range: {min(costs)} - {max(costs)}")
        print(f"Average cost: {sum(costs)/len(costs):.1f}")
        
        # Trait count distribution
        trait_counts = [combo['trait_count'] for combo in combinations]
        print(f"Trait count range: {min(trait_counts)} - {max(trait_counts)}")
        print(f"Average trait count: {sum(trait_counts)/len(trait_counts):.1f}")
        
        # Team size distribution
        team_sizes = [len(combo['units']) for combo in combinations]
        size_dist = Counter(team_sizes)
        print(f"Team size distribution:")
        for size in sorted(size_dist.keys()):
            print(f"  {size} units: {size_dist[size]} combinations")
            
        # Most common activated traits
        all_traits = []
        for combo in combinations:
            all_traits.extend(combo['activated_traits'])
        trait_frequency = Counter(all_traits)
        print(f"Most common activated traits:")
        for trait, count in trait_frequency.most_common(10):
            print(f"  {trait}: {count} times ({count/len(combinations)*100:.1f}%)")
            
        # Region coverage
        region_counts = Counter()
        for combo in combinations:
            for trait in combo['activated_traits']:
                if trait in self.target_regions:
                    region_counts[trait] += 1
        print(f"Target region activation rates:")
        for region in self.target_regions:
            count = region_counts.get(region, 0)
            print(f"  {region}: {count} times ({count/len(combinations)*100:.1f}%)")
            
    def find_best_combos(self, combo_file_path=None, top_n=5):
        """Find the best combinations by various criteria"""
        if combo_file_path is None:
            combo_file_path = self.combos_path
            
        with combo_file_path.open('r', encoding='utf-8') as f:
            data = json.load(f)
            
        combinations = data['combinations']
        
        print(f"\nBest Combinations Analysis:")
        
        # Lowest cost
        by_cost = sorted(combinations, key=lambda x: (x['total_cost'], -x['trait_count']))
        print(f"\nLowest Cost (Top {top_n}):")
        for i, combo in enumerate(by_cost[:top_n]):
            regions = sum(1 for t in combo['activated_traits'] if t in self.target_regions)
            print(f"  {i+1}. Cost: {combo['total_cost']}, Traits: {combo['trait_count']}, Regions: {regions}")
            print(f"     Units: {combo['units']}")
            
        # Most traits
        by_traits = sorted(combinations, key=lambda x: (-x['trait_count'], x['total_cost']))
        print(f"\nMost Traits (Top {top_n}):")
        for i, combo in enumerate(by_traits[:top_n]):
            regions = sum(1 for t in combo['activated_traits'] if t in self.target_regions)
            print(f"  {i+1}. Cost: {combo['total_cost']}, Traits: {combo['trait_count']}, Regions: {regions}")
            print(f"     Units: {combo['units']}")
            
        # Most regions
        by_regions = sorted(combinations, key=lambda x: (-sum(1 for t in x['activated_traits'] if t in self.target_regions), x['total_cost']))
        print(f"\nMost Target Regions (Top {top_n}):")
        for i, combo in enumerate(by_regions[:top_n]):
            regions = sum(1 for t in combo['activated_traits'] if t in self.target_regions)
            print(f"  {i+1}. Cost: {combo['total_cost']}, Traits: {combo['trait_count']}, Regions: {regions}")
            print(f"     Units: {combo['units']}")
            print(f"     Regions: {[t for t in combo['activated_traits'] if t in self.target_regions]}")

def main():
    import sys
    
    checker = ComboChecker()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "inspect" and len(sys.argv) > 2:
            try:
                combo_index = int(sys.argv[2])
                checker.inspect_combo(combo_index)
            except ValueError:
                print("ERROR: Please provide a valid combo index number")
            return
            
        elif command == "best":
            checker.find_best_combos()
            return
            
        elif command == "stats":
            checker.summary_statistics()
            return
            
        elif command == "help":
            print("Usage:")
            print("  python combo_checker.py              - Full validation and stats")
            print("  python combo_checker.py inspect N    - Inspect combo at index N")
            print("  python combo_checker.py best         - Show best combinations")
            print("  python combo_checker.py stats        - Show summary statistics only")
            print("  python combo_checker.py help         - Show this help")
            return
    
    # Default: full validation
    print("="*60)
    print("COMBO FILE VALIDATION")
    print("="*60)
    
    # Validate the combo file
    is_valid = checker.validate_combo_file()
    
    if is_valid:
        print("\n✅ All combinations are VALID!")
    else:
        print("\n❌ Some combinations are INVALID!")
        
    # Generate summary statistics
    checker.summary_statistics()
    
    # Show best combinations
    checker.find_best_combos()
    
    return is_valid

if __name__ == '__main__':
    main()
