# Combo Checker

This directory contains tools for validating and analyzing trait combination results from the fantastic-carnival project.

## Files

- `combo_checker.py` - Main validation and analysis tool for combination results

## Combo Checker Tool

The combo checker validates the correctness of generated trait combinations and provides detailed analysis.

### Features

#### 🔍 Validation
- **File Structure Validation**: Checks JSON format and required fields
- **Combination Content Validation**: 
  - Required units verification (Xin Zhao, Poppy, Kennen)
  - Team size constraints (7-8 units)
  - Cost limits (≤50)
  - Cost calculation accuracy
  - Trait activation calculations
  - Target region requirements (≥5 regions)
  - Duplicate unit detection

#### 📊 Analysis
- **Summary Statistics**: Cost ranges, trait distributions, team size analysis
- **Best Combinations**: Lowest cost, most traits, most target regions
- **Detailed Inspection**: Individual combination analysis with unit costs and trait details

### Usage

```bash
# Activate virtual environment first
source ../rt-sandbox/bin/activate

# Full validation and statistics
python combo_checker.py

# Show summary statistics only
python combo_checker.py stats

# Show best combinations analysis
python combo_checker.py best

# Inspect specific combination (index starts from 0)
python combo_checker.py inspect 0

# Show help information
python combo_checker.py help
```

### Example Output

#### Full Validation
```
============================================================
COMBO FILE VALIDATION
============================================================
Search Parameters:
  start_units: 7
  max_units: 8
  max_cost: 50
  required_units: ['Xin Zhao', 'Poppy', 'Kennen']
Total combinations claimed: 450
Actual combinations in file: 450

Validation Results:
  Valid combinations: 450
  Invalid combinations: 0
  Success rate: 100.0%

✅ All combinations are VALID!
```

#### Best Combinations Analysis
```
Best Combinations Analysis:

Lowest Cost (Top 5):
  1. Cost: 16, Traits: 7, Regions: 5
     Units: ['Xin Zhao', 'Poppy', 'Kennen', 'Sona', 'Jhin', 'Orianna', 'Loris', 'Aphelios']
  2. Cost: 16, Traits: 7, Regions: 5
     Units: ['Xin Zhao', 'Poppy', 'Kennen', 'Sona', 'Shen', 'Orianna', 'Loris', 'Aphelios']
```

#### Detailed Inspection
```
Detailed Analysis of Combination #1:
Units: ['Xin Zhao', 'Poppy', 'Kennen', 'Sona', 'Jhin', 'Orianna', 'Loris', 'Aphelios']
Total Cost: 16
Team Size: 8
Trait Count: 7

Unit Costs:
  Xin Zhao: 2
  Poppy: 2
  Kennen: 3
  Sona: 1
  Jhin: 1
  Orianna: 2
  Loris: 3
  Aphelios: 2
  Total: 16

Activated Traits:
  Demacia: threshold 3 [TARGET REGION]
  Invoker: threshold 2
  Ionia: threshold 3 [TARGET REGION]
  Piltover: threshold 2 [TARGET REGION]
  Targon: threshold 1 [TARGET REGION]
  Warden: threshold 2
  Yordle: threshold 2 [TARGET REGION]

Target Regions Activated: 5/13

✅ This combination is VALID
```

### Dependencies

The checker requires the following data files:
- `var/traits_units_activations.json` - Trait definitions and activation thresholds
- `var/units_cost.json` - Unit cost information
- `var/all_valid_combos_optimized.json` - Generated combinations to validate

### Validation Rules

1. **Required Units**: Must include Xin Zhao, Poppy, and Kennen
2. **Team Size**: 7-8 units per combination
3. **Cost Limit**: Total cost must not exceed 50
4. **Target Regions**: Must activate at least 5 of the 13 target regions:
   - Bilgewater, Demacia, Freljord, Ionia, Ixtal
   - Noxus, Piltover, Shadow Isles, Shurima, Targon
   - Void, Yordle, Zaun
5. **Data Integrity**: All calculations must match between different fields

### Error Detection

The checker can detect various types of errors:
- Missing or extra required units
- Incorrect cost calculations
- Wrong trait activation thresholds
- Insufficient target region coverage
- Data inconsistencies between fields
- Duplicate units in combinations

## Development

To extend the checker functionality:

1. Add new validation rules in `validate_single_combo()` method
2. Implement additional analysis in summary or inspection functions
3. Add new command-line options in the `main()` function

## Output Files

The checker validates combinations from:
- `../var/all_valid_combos_optimized.json` - Default input file

Results are displayed to console with detailed validation reports and statistics.
