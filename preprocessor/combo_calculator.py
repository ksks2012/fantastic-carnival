#!/usr/bin/env python3
import json
import itertools
from collections import defaultdict, Counter
from pathlib import Path
from utils import file_processor

DATA_TRAITS = Path('var/traits_units_activations.json')
DATA_COSTS = Path('var/units_cost.json')

class TraitComboCalculatorOptimized:
    def __init__(self):
        with DATA_TRAITS.open('r', encoding='utf-8') as f:
            self.traits_data = json.load(f)
        with DATA_COSTS.open('r', encoding='utf-8') as f:
            self.units_costs = json.load(f)
        
        # the 13 origin regions to consider
        self.target_regions = [
            'Bilgewater', 'Demacia', 'Freljord', 'Ionia', 'Ixtal', 
            'Noxus', 'Piltover', 'Shadow Isles', 'Shurima', 'Targon', 
            'Void', 'Yordle', 'Zaun'
        ]
        
        # build mappings: unit -> traits, trait -> units
        self.unit_traits = defaultdict(list)
        self.trait_units = defaultdict(list)
        for trait_name, trait_data in self.traits_data.items():
            for unit in trait_data.get('units', []):
                self.unit_traits[unit].append(trait_name)
                self.trait_units[trait_name].append(unit)
        
        # parse integer thresholds from activations (keys that can be int)
        self.trait_thresholds = {}
        for trait, info in self.traits_data.items():
            activ = info.get('activations', {}) or {}
            thresholds = []
            for k in activ.keys():
                try:
                    thresholds.append(int(k))
                except Exception:
                    continue
            thresholds.sort()
            if thresholds:
                self.trait_thresholds[trait] = thresholds
        
        # unit heuristics for sorting candidates
        self.unit_region_coverage = {}
        self.unit_total_traits = {}
        for unit, traits in self.unit_traits.items():
            self.unit_region_coverage[unit] = sum(1 for t in traits if t in self.target_regions)
            self.unit_total_traits[unit] = len(traits)
        
        # candidate pool: only units from target regions that have cost
        candidates = []
        for unit in self.unit_traits.keys():
            if unit not in self.units_costs:
                continue
            # only include units that belong to target regions
            contributes_region = any(t in self.target_regions for t in self.unit_traits[unit])
            if contributes_region:
                candidates.append(unit)
        # sort heuristically: more region coverage, more traits, lower cost
        candidates.sort(key=lambda u: (-self.unit_region_coverage.get(u,0), -self.unit_total_traits.get(u,0), self.units_costs.get(u,999)))
        self.candidates = candidates
        
        print(f"Loaded {len(self.traits_data)} traits and {len(self.units_costs)} unit costs")
        print(f"Candidate units after filtering: {len(self.candidates)}")
    
    def calculate_total_cost(self, units):
        total_cost = 0
        for u in units:
            total_cost += int(self.units_costs.get(u, 0))
        return total_cost
    
    def get_activation_state(self, selected_units):
        # returns activated dict (trait -> chosen threshold) and counts Counter
        counts = Counter()
        for u in selected_units:
            for t in self.unit_traits.get(u, []):
                counts[t] += 1
        activated = {}
        for trait, thresholds in self.trait_thresholds.items():
            cnt = counts.get(trait, 0)
            valid = [th for th in thresholds if th <= cnt]
            if valid:
                activated[trait] = max(valid)
        return activated, counts
    
    def count_activated_target_regions(self, activated_dict):
        # number of target regions that are in activated_dict
        return sum(1 for r in self.target_regions if r in activated_dict)
    
    def can_reach_more_regions(self, current_counts, start_idx, remaining_slots, candidates):
        # optimistic bound for how many distinct regions could be activated
        possible_regions = set()
        # include already possibly satisfied regions if current_counts meets smallest threshold
        for trait in self.target_regions:
            if trait in self.trait_thresholds:
                thresholds = self.trait_thresholds[trait]
                if current_counts.get(trait,0) >= thresholds[0]:
                    possible_regions.add(trait)
        idx = start_idx
        slots = remaining_slots
        while idx < len(candidates) and slots > 0:
            u = candidates[idx]
            for t in self.unit_traits.get(u, []):
                if t in self.target_regions:
                    possible_regions.add(t)
            idx += 1
            slots -= 1
        return len(possible_regions)
    
    def find_all_valid_combos(self, max_units=8, max_cost=50, start_units=7, required_units=None):
        print(f"Optimized search: start {start_units}, max {max_units}, max_cost {max_cost}")
        if required_units:
            print(f"Required starting units: {required_units}")
        
        viable_candidates = [u for u in self.candidates if int(self.units_costs.get(u, 999)) <= max_cost]
        all_results = []
        
        for team_size in range(start_units, max_units + 1):
            print(f"Searching team size = {team_size} ...")
            results = self._dfs_search_all_for_size(team_size, viable_candidates, max_cost, required_units)
            all_results.extend(results)
            
        return all_results
    
    def _dfs_search_all_for_size(self, team_size, candidates, max_cost, required_units=None):
        n = len(candidates)
        chosen = []
        chosen_set = set()
        backtrack_state = {'cost': 0, 'counts': {}}
        all_combos = []
        
        # Initialize with required units if specified
        if required_units:
            for unit in required_units:
                if unit in candidates and unit not in chosen_set:
                    chosen.append(unit)
                    chosen_set.add(unit)
                    backtrack_state['cost'] += int(self.units_costs.get(unit, 0))
                    for t in self.unit_traits.get(unit, []):
                        backtrack_state['counts'][t] = backtrack_state['counts'].get(t, 0) + 1
        
        def get_activated_from_state():
            activated_local = {}
            for trait, thresholds in self.trait_thresholds.items():
                cnt = backtrack_state['counts'].get(trait, 0)
                valids = [th for th in thresholds if th <= cnt]
                if valids:
                    activated_local[trait] = max(valids)
            return activated_local
        
        def backtrack(start_idx, depth):
            if depth == team_size:
                activated_local = get_activated_from_state()
                if not activated_local:
                    return
                region_count = self.count_activated_target_regions(activated_local)
                if region_count >= 5 and backtrack_state['cost'] <= max_cost:
                    combo = {
                        'units': chosen.copy(),
                        'trait_count': len(activated_local),
                        'activated_traits': sorted(list(activated_local.keys())),
                        'total_cost': backtrack_state['cost'],
                        'activated_details': activated_local
                    }
                    all_combos.append(combo)
                return
            
            if start_idx >= n:
                return
            if (n - start_idx) < (team_size - depth):
                return
                
            slots_needed = team_size - depth
            # optimistic min cost using next 200 candidates
            next_costs = []
            for j in range(start_idx, min(n, start_idx + 200)):
                next_costs.append(int(self.units_costs.get(candidates[j], 999)))
            next_costs.sort()
            if len(next_costs) < slots_needed:
                return
            optimistic_min_cost = sum(next_costs[:slots_needed])
            if backtrack_state['cost'] + optimistic_min_cost > max_cost:
                return
                
            possible_region_count = self.can_reach_more_regions(backtrack_state['counts'], start_idx, slots_needed, candidates)
            already_activated_regions = sum(1 for r in self.target_regions if backtrack_state['counts'].get(r, 0) >= 1 and r in self.trait_thresholds and any(th <= backtrack_state['counts'].get(r,0) for th in self.trait_thresholds.get(r,[])))
            if possible_region_count < 5 and already_activated_regions < 5:
                return
                
            for i in range(start_idx, n):
                u = candidates[i]
                if u in chosen_set:
                    continue
                chosen.append(u)
                chosen_set.add(u)
                prev_cost = backtrack_state['cost']
                backtrack_state['cost'] = prev_cost + int(self.units_costs.get(u, 0))
                for t in self.unit_traits.get(u, []):
                    backtrack_state['counts'][t] = backtrack_state['counts'].get(t, 0) + 1
                    
                if backtrack_state['cost'] <= max_cost:
                    backtrack(i+1, depth+1)
                    
                backtrack_state['cost'] = prev_cost
                for t in self.unit_traits.get(u, []):
                    backtrack_state['counts'][t] -= 1
                    if backtrack_state['counts'][t] == 0:
                        del backtrack_state['counts'][t]
                chosen.pop()
                chosen_set.remove(u)
        
        initial_depth = len(required_units) if required_units else 0
        backtrack(0, initial_depth)
        return all_combos
    
    def run_and_save_all(self, start_units=7, max_units=8, max_cost=50, required_units=None, outpath='var/all_valid_combos_optimized.json'):
        results = self.find_all_valid_combos(max_units=max_units, max_cost=max_cost, start_units=start_units, required_units=required_units)
        if results:
            # Sort results by total cost, then by trait count
            results.sort(key=lambda x: (x['total_cost'], -x['trait_count']))
            
            output_data = {
                'search_parameters': {
                    'start_units': start_units,
                    'max_units': max_units,
                    'max_cost': max_cost,
                    'required_units': required_units
                },
                'total_combinations_found': len(results),
                'combinations': results
            }
            
            file_processor.write_json(outpath, output_data)
            print(f"Found {len(results)} valid combinations and saved to {outpath}")
        else:
            print("No valid combos found with the optimized search within given limits.")
        return results

def main():
    calc = TraitComboCalculatorOptimized()
    # Define the required starting units
    required_units = ['Xin Zhao', 'Poppy', 'Kennen']
    
    results = calc.run_and_save_all(
        start_units=7, 
        max_units=8, 
        max_cost=50, 
        required_units=required_units
    )
    
    if results:
        print(f"Found {len(results)} valid combinations starting with {required_units}")
        print("\nTop 5 combinations by cost:")
        for i, combo in enumerate(results[:5]):
            print(f"\n{i+1}. Cost: {combo['total_cost']}, Traits: {combo['trait_count']}")
            print(f"   Units: {combo['units']}")
            print(f"   Activated Traits: {combo['activated_traits']}")
    else:
        print("No solutions found. Consider increasing max_units or max_cost.")

if __name__ == '__main__':
    main()
