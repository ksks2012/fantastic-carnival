import tkinter as tk
from tkinter import ttk
import json
from collections import defaultdict

from language.en_zh_tw import unit_translation
from utils import file_processor


# Extract all unique units from combinations
def get_all_units(combinations):
    units = set()
    for combo in combinations:
        units.update(combo["units"])
    all_units = sorted(units)
    # Translate unit names from English to Chinese
    translated_units = [unit_translation.get(unit, unit) for unit in all_units]
    print("All units:", translated_units)  # Debugging
    return all_units, translated_units  # Return English and Chinese lists

# Filter combinations
def filter_combinations(combinations, selected_units):
    selected_set = set(selected_units)
    print("Selected units for filtering:", selected_set)  # Debugging
    filtered = [combo for combo in combinations if selected_set.issubset(combo["units"])]
    print("Filtered combinations count:", len(filtered))  # Debugging
    return filtered

# Main window class
class TraitsFilterApp:
    def __init__(self, root, combinations, unit_costs):
        self.root = root
        self.root.title("Traits Combination Filter")
        self.combinations = combinations
        self.all_units, self.translated_units = get_all_units(combinations)  # English and Chinese units
        self.selected_units = set()
        self.unit_costs = unit_costs

        # Convert combinations to list of sets for faster filtering
        self.combinations = [
            {
            "units": set(combo["units"]),
            "total_cost": combo["total_cost"],
            "trait_count": combo["trait_count"],
            "activated_traits": combo["activated_traits"]
            }
            for combo in combinations
        ]

        # Unit selection area
        self.unit_frame = ttk.LabelFrame(root, text="Select Your Units", padding=10)
        self.unit_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.unit_notebook = ttk.Notebook(self.unit_frame)
        self.unit_notebook.pack(fill="both", expand=True)

        # Tab 1: Alphabetical Order
        self.tab_alpha = ttk.Frame(self.unit_notebook)
        self.unit_notebook.add(self.tab_alpha, text="Alphabetical Order")
        self.check_vars_alpha = self.create_checkboxes(self.tab_alpha, sorted(self.translated_units), block=False)

        # Tab 2: Cost Order (Grouped)
        self.tab_cost = ttk.Frame(self.unit_notebook)
        self.unit_notebook.add(self.tab_cost, text="Cost Order")
        sorted_by_cost = sorted(self.translated_units, key=lambda x: self.unit_costs[list(unit_translation.keys())[list(unit_translation.values()).index(x)]])
        self.check_vars_cost = self.create_checkboxes(self.tab_cost, sorted_by_cost, block=True)

        # Filter button
        self.filter_button = ttk.Button(root, text="Filter Combinations", command=self.show_results)
        self.filter_button.pack(pady=5)

        # Result display area
        self.result_frame = ttk.LabelFrame(root, text="Filter Results", padding=10)
        self.result_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.result_text = tk.Text(self.result_frame, height=15, width=80)
        self.result_text.pack(fill="both", expand=True)


    def create_checkboxes(self, parent, units, block=False):
        check_vars = {}
        if block:  # Display in blocks sorted by cost
            cost_groups = defaultdict(list)
            for unit in units:
                eng_unit = list(unit_translation.keys())[list(unit_translation.values()).index(unit)]
                cost = self.unit_costs[eng_unit]
                cost_groups[cost].append(unit)

            for cost in sorted(cost_groups.keys()):
                frame = ttk.LabelFrame(parent, text=f"{cost} Cost Units", padding=5)
                frame.pack(fill="x", padx=5, pady=5)
                for i, unit in enumerate(sorted(cost_groups[cost])):  # Sort alphabetically within each block
                    var = tk.BooleanVar()
                    chk = ttk.Checkbutton(frame, text=unit, variable=var, command=self.update_selection)
                    chk.grid(row=i // 5, column=i % 5, sticky="w", padx=5, pady=2)
                    check_vars[unit] = var
        else:  # No block display for alphabetical and trait sorting
            for i, unit in enumerate(units):
                var = tk.BooleanVar()
                chk = ttk.Checkbutton(parent, text=unit, variable=var, command=self.update_selection)
                chk.grid(row=i // 5, column=i % 5, sticky="w", padx=5, pady=2)
                check_vars[unit] = var
        return check_vars

    def update_selection(self):
        # Translate selected Chinese units back to English
        selected_translated = set()
        for tab_vars in [self.check_vars_alpha, self.check_vars_cost]:
            selected_translated.update({unit for unit, var in tab_vars.items() if var.get()})
        self.selected_units = {list(unit_translation.keys())[list(unit_translation.values()).index(unit)] 
                              for unit in selected_translated}
        print("Selected units (Chinese):", selected_translated)  # Debugging

    def show_results(self):
        self.result_text.delete(1.0, tk.END)  # Clear result area
        if not self.selected_units:
            self.result_text.insert(tk.END, "Please select at least one unit.")
            return

        filtered = filter_combinations(self.combinations, self.selected_units)
        if not filtered:
            self.result_text.insert(tk.END, "No matching combinations found.")
            return

        filtered.sort(key=lambda x: (x["total_cost"], -x["trait_count"]))
        
        self.result_text.insert(tk.END, f"Found {len(filtered)} combinations:\n\n")
        for i, combo in enumerate(filtered[:10], 1):
            # Translate unit names to Chinese for display
            translated_units = [unit_translation.get(unit, unit) for unit in combo["units"]]
            text = (f"Combination {i}:\n"
                   f"Units: {', '.join(translated_units)}\n"
                   f"Total Cost: {combo['total_cost']}\n"
                   f"Traits ({combo['trait_count']}): {', '.join(combo['activated_traits'])}\n\n")
            self.result_text.insert(tk.END, text)

# Main program
if __name__ == "__main__":
    combinations = file_processor.read_json("./var/traits_tracker_result_2000.json")
    unit_costs = file_processor.read_json("./var/units_cost.json")
    root = tk.Tk()
    app = TraitsFilterApp(root, combinations, unit_costs)
    root.mainloop()
