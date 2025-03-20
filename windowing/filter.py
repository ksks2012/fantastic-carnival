import tkinter as tk
from tkinter import ttk
import json
from collections import defaultdict

from utils import file_processor


# Extract all unique units from combinations
def get_all_units(combinations):
    units = set()
    for combo in combinations:
        units.update(combo["units"])
    all_units = sorted(units)
    print("All units:", all_units)  # Debugging
    return all_units

# Filter combinations
def filter_combinations(combinations, selected_units):
    selected_set = set(selected_units)
    print("Selected units for filtering:", selected_set)  # Debugging
    filtered = [combo for combo in combinations if selected_set.issubset(set(combo["units"]))]
    print("Filtered combinations count:", len(filtered))  # Debugging
    return filtered

# Main window class
class TraitsFilterApp:
    def __init__(self, root, combinations):
        self.root = root
        self.root.title("Traits Combination Filter")
        self.combinations = combinations
        self.all_units = get_all_units(combinations)
        self.selected_units = set()

        # Unit selection area
        self.unit_frame = ttk.LabelFrame(root, text="Select Your Units", padding=10)
        self.unit_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.check_vars = {}
        for i, unit in enumerate(self.all_units):
            var = tk.BooleanVar()
            chk = ttk.Checkbutton(self.unit_frame, text=unit, variable=var,
                                command=self.update_selection)
            chk.grid(row=i // 5, column=i % 5, sticky="w", padx=5, pady=2)
            self.check_vars[unit] = var

        # Filter button
        self.filter_button = ttk.Button(root, text="Filter Combinations", command=self.show_results)
        self.filter_button.pack(pady=5)

        # Result display area
        self.result_frame = ttk.LabelFrame(root, text="Filtered Combinations", padding=10)
        self.result_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.result_text = tk.Text(self.result_frame, height=15, width=80)
        self.result_text.pack(fill="both", expand=True)

    def update_selection(self):
        self.selected_units = {unit for unit, var in self.check_vars.items() if var.get()}
        print("Selected units:", self.selected_units)  # Debugging

    def show_results(self):
        self.result_text.delete(1.0, tk.END)  # Clear result area
        if not self.selected_units:
            self.result_text.insert(tk.END, "Please select at least one unit.")
            return

        filtered = filter_combinations(self.combinations, self.selected_units)
        if not filtered:
            self.result_text.insert(tk.END, "No combinations found with selected units.")
            return

        filtered.sort(key=lambda x: (x["total_cost"], -x["trait_count"]))
        
        self.result_text.insert(tk.END, f"Found {len(filtered)} combinations:\n\n")
        for i, combo in enumerate(filtered[:10], 1):
            text = (f"Combination {i}:\n"
                   f"Units: {', '.join(combo['units'])}\n"
                   f"Total Cost: {combo['total_cost']}\n"
                   f"Traits ({combo['trait_count']}): {', '.join(combo['activated_traits'])}\n\n")
            self.result_text.insert(tk.END, text)

# Main program
if __name__ == "__main__":
    combinations = file_processor.load_json("./var/traits_tracker_result_2000.json")
    root = tk.Tk()
    app = TraitsFilterApp(root, combinations)
    root.mainloop()
