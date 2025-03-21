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
    def __init__(self, root, combinations, unit_costs, traits_data):
        self.root = root
        self.root.title("Traits Combination Filter")
        self.combinations = combinations
        self.all_units, self.translated_units = get_all_units(combinations)
        self.selected_units = set()
        self.unit_costs = unit_costs
        self.traits_data = traits_data

        self.combinations = [
            {
                "units": set(combo["units"]),
                "total_cost": combo["total_cost"],
                "trait_count": combo["trait_count"],
                "activated_traits": combo["activated_traits"]
            }
            for combo in combinations
        ]

        # Main frame to split left and right sections
        self.main_frame = ttk.Frame(root)
        self.main_frame.pack(fill="both", expand=True)

        # Left section: Unit selection
        self.left_frame = ttk.Frame(self.main_frame)
        self.left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=5)

        self.unit_frame = ttk.LabelFrame(self.left_frame, text="Select Your Units", padding=10)
        self.unit_frame.pack(fill="both", expand=True)

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

        self.unit_notebook = ttk.Notebook(self.scrollable_frame)
        self.unit_notebook.pack(fill="both", expand=True)

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

        # Right section: Selected units display
        self.right_frame = ttk.Frame(self.main_frame)
        self.right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=5)

        # Right section: Currently Unit selection
        self.selected_frame = ttk.LabelFrame(self.right_frame, text="Selected Units", padding=10)
        self.selected_frame.pack(fill="both", expand=True)

        self.selected_listbox = tk.Listbox(self.selected_frame, height=20, width=30)
        self.selected_listbox.pack(fill="both", expand=True)

        # Button frame
        self.button_frame = ttk.Frame(root)
        self.button_frame.pack(pady=5)

        self.filter_button = ttk.Button(self.button_frame, text="Filter Combinations", command=self.show_results)
        self.filter_button.pack(side="left", padx=5)

        self.clear_button = ttk.Button(self.button_frame, text="Clear Selection", command=self.clear_selection)
        self.clear_button.pack(side="left", padx=5)

        # Copy button for results
        self.copy_button = ttk.Button(self.button_frame, text="Copy Selected", command=self.copy_selected_results)
        self.copy_button.pack(side="left", padx=5)

        # Result display area with Treeview
        self.result_frame = ttk.LabelFrame(root, text="Filter Results", padding=10)
        self.result_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Treeview for structured results
        self.result_tree = ttk.Treeview(self.result_frame, columns=("Units", "Total Cost", "Trait Count", "Traits"), show="headings", height=15)
        self.result_tree.pack(fill="both", expand=True)

        self.result_tree.heading("Units", text="Additional Units Needed")
        self.result_tree.heading("Total Cost", text="Total Cost")
        self.result_tree.heading("Trait Count", text="Trait Count")
        self.result_tree.heading("Traits", text="Activated Traits")

        self.result_tree.column("Units", width=300)
        self.result_tree.column("Total Cost", width=80, anchor="center")
        self.result_tree.column("Trait Count", width=80, anchor="center")
        self.result_tree.column("Traits", width=200)

        # Enable mouse wheel scrolling for unit selection
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def create_checkboxes(self, parent, units, block="none"):
        if block == "cost":
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
        elif block == "trait":
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
        else:
            for i, unit in enumerate(units):
                chk = ttk.Checkbutton(parent, text=unit, variable=self.check_vars[unit], command=self.update_selection)
                chk.grid(row=i // 5, column=i % 5, sticky="w", padx=5, pady=2)

    def update_selection(self):
        selected_translated = {unit for unit, var in self.check_vars.items() if var.get()}
        self.selected_units = {list(unit_translation.keys())[list(unit_translation.values()).index(unit)] 
                              for unit in selected_translated}
        print("Selected units (Chinese):", selected_translated)

        self.selected_listbox.delete(0, tk.END)
        for unit in sorted(selected_translated):
            self.selected_listbox.insert(tk.END, unit)

    def clear_selection(self):
        for var in self.check_vars.values():
            var.set(False)
        self.selected_units.clear()
        self.selected_listbox.delete(0, tk.END)
        print("All selections cleared.")

    def show_results(self):
        # Clear previous results
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)

        if not self.selected_units:
            self.result_tree.insert("", "end", values=("Please select at least one unit.", "", "", ""))
            return

        filtered = filter_combinations(self.combinations, self.selected_units)
        if not filtered:
            self.result_tree.insert("", "end", values=("No combinations found.", "", "", ""))
            return

        # Sort by total cost (ascending) and trait count (descending)
        filtered.sort(key=lambda x: (x["total_cost"], -x["trait_count"]))

        # Insert header with count
        self.result_tree.insert("", "end", values=(f"Found {len(filtered)} combinations", "", "", ""))

        # Insert top 10 results, showing only additional units needed
        for i, combo in enumerate(filtered[:10], 1):
            # Filter out already selected units (in English)
            additional_units = combo["units"] - self.selected_units
            # Translate additional units to Chinese
            translated_additional_units = [unit_translation.get(unit, unit) for unit in additional_units]
            units_str = ", ".join(translated_additional_units) if translated_additional_units else "None"
            traits_str = ", ".join(combo["activated_traits"])
            self.result_tree.insert("", "end", values=(units_str, combo["total_cost"], combo["trait_count"], traits_str))

    def copy_selected_results(self):
        # Copy selected rows from Treeview to clipboard
        selected_items = self.result_tree.selection()
        if not selected_items:
            return

        clipboard_text = ""
        for item in selected_items:
            values = self.result_tree.item(item, "values")
            clipboard_text += f"Additional Units Needed: {values[0]}\nTotal Cost: {values[1]}\nTrait Count: {values[2]}\nTraits: {values[3]}\n\n"

        self.root.clipboard_clear()
        self.root.clipboard_append(clipboard_text)
        print("Selected results copied to clipboard.")


# Main program
if __name__ == "__main__":
    combinations = file_processor.read_json("./var/traits_tracker_result_15000.json")
    unit_costs = file_processor.read_json("./var/units_cost.json")
    traits_data = file_processor.read_json("./var/traits_units_activations.json")
    root = tk.Tk()
    root.geometry("1000x800")
    app = TraitsFilterApp(root, combinations, unit_costs, traits_data)
    root.mainloop()
