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
# Main window class
class TraitsFilterApp:
    def __init__(self, root, combinations, unit_costs, traits_data):
        self.root = root
        self.root.title("Traits Combination Filter")
        self.combinations = combinations
        self.all_units, self.translated_units = get_all_units(combinations)
        self.selected_units = set()
        self.unit_costs = unit_costs
        self.traits_data = traits_data

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

        # Unit selection area with scrollbar
        self.unit_frame = ttk.LabelFrame(root, text="Select Your Units", padding=10)
        self.unit_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Create a canvas and scrollbar
        self.canvas = tk.Canvas(self.unit_frame)
        self.scrollbar = ttk.Scrollbar(self.unit_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Notebook inside scrollable frame
        self.unit_notebook = ttk.Notebook(self.scrollable_frame)
        self.unit_notebook.pack(fill="both", expand=True)

        # Shared variable dictionary for all tabs
        self.check_vars = {unit: tk.BooleanVar() for unit in self.translated_units}

        # Tab 1: Alphabetical Order
        self.tab_alpha = ttk.Frame(self.unit_notebook)
        self.unit_notebook.add(self.tab_alpha, text="Alphabetical Order")
        self.create_checkboxes(self.tab_alpha, sorted(self.translated_units), block="none")

        # Tab 2: Cost Order (Grouped)
        self.tab_cost = ttk.Frame(self.unit_notebook)
        self.unit_notebook.add(self.tab_cost, text="Cost Order")
        sorted_by_cost = sorted(self.translated_units, key=lambda x: self.unit_costs[list(unit_translation.keys())[list(unit_translation.values()).index(x)]])
        self.create_checkboxes(self.tab_cost, sorted_by_cost, block="cost")

        # Tab 3: Trait Order (Grouped)
        self.tab_traits = ttk.Frame(self.unit_notebook)
        self.unit_notebook.add(self.tab_traits, text="Trait Order")
        self.create_checkboxes(self.tab_traits, self.translated_units, block="trait")

        # Filter button
        self.filter_button = ttk.Button(root, text="Filter Combinations", command=self.show_results)
        self.filter_button.pack(pady=5)

        # Result display area
        self.result_frame = ttk.LabelFrame(root, text="Filter Results", padding=10)
        self.result_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.result_text = tk.Text(self.result_frame, height=15, width=80)
        self.result_text.pack(fill="both", expand=True)

        # Enable mouse wheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def create_checkboxes(self, parent, units, block="none"):
        if block == "cost":  # Display in blocks sorted by cost
            cost_groups = defaultdict(list)
            for unit in units:
                eng_unit = list(unit_translation.keys())[list(unit_translation.values()).index(unit)]
                cost = self.unit_costs[eng_unit]
                cost_groups[cost].append(unit)

            for cost in sorted(cost_groups.keys()):
                frame = ttk.LabelFrame(parent, text=f"{cost} Cost Units", padding=5)
                frame.pack(fill="x", padx=5, pady=5)
                for i, unit in enumerate(sorted(cost_groups[cost])):
                    chk = ttk.Checkbutton(frame, text=unit, variable=self.check_vars[unit], command=self.update_selection)
                    chk.grid(row=i // 5, column=i % 5, sticky="w", padx=5, pady=2)
        elif block == "trait":  # Display in blocks sorted by traits
            trait_groups = defaultdict(list)
            for trait, info in self.traits_data.items():
                for eng_unit in info["units"]:
                    unit = unit_translation.get(eng_unit, eng_unit)
                    if unit in units:
                        trait_groups[trait].append(unit)

            for trait in sorted(trait_groups.keys()):
                frame = ttk.LabelFrame(parent, text=trait, padding=5)
                frame.pack(fill="x", padx=5, pady=5)
                for i, unit in enumerate(sorted(trait_groups[trait])):
                    chk = ttk.Checkbutton(frame, text=unit, variable=self.check_vars[unit], command=self.update_selection)
                    chk.grid(row=i // 5, column=i % 5, sticky="w", padx=5, pady=2)
        else:  # No block display (alphabetical order)
            for i, unit in enumerate(units):
                chk = ttk.Checkbutton(parent, text=unit, variable=self.check_vars[unit], command=self.update_selection)
                chk.grid(row=i // 5, column=i % 5, sticky="w", padx=5, pady=2)

    def update_selection(self):
        selected_translated = {unit for unit, var in self.check_vars.items() if var.get()}
        self.selected_units = {list(unit_translation.keys())[list(unit_translation.values()).index(unit)] 
                              for unit in selected_translated}
        print("Selected units (Chinese):", selected_translated)  # Debugging

    def show_results(self):
        self.result_text.delete(1.0, tk.END)
        if not self.selected_units:
            self.result_text.insert(tk.END, "Please select at least one unit.")
            return

        filtered = filter_combinations(self.combinations, self.selected_units)
        if not filtered:
            self.result_text.insert(tk.END, "No combinations found.")
            return

        filtered.sort(key=lambda x: (x["total_cost"], -x["trait_count"]))
        
        self.result_text.insert(tk.END, f"Found {len(filtered)} combinations:\n\n")
        for i, combo in enumerate(filtered[:10], 1):
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
    traits_data = file_processor.read_json("./var/traits_units_activations.json")
    root = tk.Tk()
    root.geometry("800x800")
    app = TraitsFilterApp(root, combinations, unit_costs, traits_data)
    root.mainloop()
