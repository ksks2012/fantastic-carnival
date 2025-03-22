import os
import sys
import tkinter as tk

from tkinter import ttk
from collections import defaultdict

from language.en_zh_tw import unit_translation, ui_translations
from utils import file_processor

# Utility Functions
def get_all_units(combinations):
    """Extract all unique units from combinations."""
    units = set().union(*(combo["units"] for combo in combinations))
    return sorted(units)

def filter_combinations(combinations, selected_units):
    """Filter combinations containing all selected units."""
    selected_set = set(selected_units)
    print("Selected units for filtering:", selected_set)
    filtered = [combo for combo in combinations if selected_set.issubset(combo["units"])]
    print("Filtered combinations count:", len(filtered))
    return filtered

# Main Application Class
class TraitsFilterApp:
    def __init__(self, root, combinations, unit_costs, traits_data):
        self.root = root
        self.root.title("Traits Combination Filter")
        self.unit_costs = unit_costs
        self.traits_data = traits_data
        self.selected_units = set()
        self.language = "English"  # Default language
        self.translation = unit_translation  # English to Chinese
        self.reverse_translation = {v: k for k, v in unit_translation.items()}  # Chinese to English

        # Preprocess combinations
        self.combinations = [
            {
                "units": set(combo["units"]),
                "total_cost": combo["total_cost"],
                "trait_count": combo["trait_count"],
                "activated_traits": combo["activated_traits"]
            }
            for combo in combinations
        ]
        self.all_units = get_all_units(combinations)
        self.translated_units = self._translate_units(self.all_units)
        self.check_vars = {unit: tk.BooleanVar() for unit in self.translated_units}

        # Setup UI
        self._setup_ui()

    def _translate_units(self, units):
        """Translate unit names based on current language."""
        if self.language == "English":
            return [unit for unit in units]
        else:  # Chinese
            return [self.translation.get(unit, unit) for unit in units]

    def _translate_text(self, text):
        """Translate UI text based on current language."""
        return ui_translations[self.language].get(text, text)

    def _setup_ui(self):
        """Initialize the main UI components."""
        # Language selection
        self.lang_frame = ttk.Frame(self.root)
        self.lang_frame.pack(fill="x", pady=5)
        ttk.Label(self.lang_frame, text="Language:").pack(side="left", padx=5)
        self.lang_combo = ttk.Combobox(self.lang_frame, values=["English", "Chinese"], state="readonly")
        self.lang_combo.set("English")
        self.lang_combo.pack(side="left")
        self.lang_combo.bind("<<ComboboxSelected>>", self._change_language)

        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)

        self._create_unit_selection_area()
        self._create_selected_units_area()
        self._create_button_area()
        self._create_result_area()

    def _change_language(self, event):
        """Handle language change and refresh UI."""
        self.language = self.lang_combo.get()
        self.translated_units = self._translate_units(self.all_units)
        self.check_vars = {unit: tk.BooleanVar(value=self.check_vars.get(unit, tk.BooleanVar()).get()) 
                           for unit in self.translated_units}
        self._refresh_ui()

    def _refresh_ui(self):
        """Refresh all UI elements with the current language."""
        self.root.title(self._translate_text("Traits Combination Filter"))
        self.unit_frame.config(text=self._translate_text("Select Your Units"))
        self.selected_frame.config(text=self._translate_text("Selected Units"))
        self.result_frame.config(text=self._translate_text("Filter Results"))

        # Clear existing tabs
        for tab_id in self.unit_notebook.tabs():
            self.unit_notebook.forget(tab_id)
        self.tab_contents.clear()

        # Recreate tabs with new language
        self._add_tab(self._translate_text("Alphabetical Order"), sorted(self.translated_units), "none")
        self._add_tab(self._translate_text("Cost Order"), 
                      sorted(self.translated_units, key=lambda x: self.unit_costs[self.reverse_translation.get(x, x) if self.language == "Chinese" else x]), 
                      "cost")
        self._add_tab(self._translate_text("Trait Order"), self.translated_units, "trait")
        self._show_tab_content(self._translate_text("Alphabetical Order"))

        # Update buttons
        for widget in self.button_frame.winfo_children():
            widget.destroy()
        ttk.Button(self.button_frame, text=self._translate_text("Filter Combinations"), command=self.show_results).pack(side="left", padx=5)
        ttk.Button(self.button_frame, text=self._translate_text("Clear Selection"), command=self.clear_selection).pack(side="left", padx=5)
        ttk.Button(self.button_frame, text=self._translate_text("Copy Selected"), command=self.copy_selected_results).pack(side="left", padx=5)

        # Update Treeview headings
        self.result_tree.heading("Units", text=self._translate_text("Additional Units Needed"))
        self.result_tree.heading("Total Cost", text=self._translate_text("Total Cost"))
        self.result_tree.heading("Trait Count", text=self._translate_text("Trait Count"))
        self.result_tree.heading("Traits", text=self._translate_text("Activated Traits"))

        # Refresh selected units and results
        self.update_selection()
        self.show_results()

    def _create_unit_selection_area(self):
        """Create the unit selection area with fixed tabs and scrollable content."""
        self.left_frame = ttk.Frame(self.main_frame)
        self.left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=5)

        self.unit_frame = ttk.LabelFrame(self.left_frame, text=self._translate_text("Select Your Units"), padding=10)
        self.unit_frame.pack(fill="both", expand=True)

        # Notebook for tabs (fixed at the top)
        self.unit_notebook = ttk.Notebook(self.unit_frame)
        self.unit_notebook.pack(fill="x", pady=(0, 5))

        # Content frame with scrollbar
        self.content_frame = ttk.Frame(self.unit_frame)
        self.content_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(self.content_frame)
        self.scrollbar = ttk.Scrollbar(self.content_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Dictionary to hold tab content frames
        self.tab_contents = {}
        self._add_tab(self._translate_text("Alphabetical Order"), sorted(self.translated_units), "none")
        self._add_tab(self._translate_text("Cost Order"), 
                      sorted(self.translated_units, key=lambda x: self.unit_costs[self.reverse_translation.get(x, x) if self.language == "Chinese" else x]), 
                      "cost")
        self._add_tab(self._translate_text("Trait Order"), self.translated_units, "trait")

        self.unit_notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self._show_tab_content(self._translate_text("Alphabetical Order"))

        # Bind mouse wheel
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _add_tab(self, tab_name, units, block_type):
        """Add a tab to the notebook and create its scrollable content."""
        tab = ttk.Frame(self.unit_notebook)
        self.unit_notebook.add(tab, text=tab_name)
        content_frame = ttk.Frame(self.scrollable_frame)
        self.tab_contents[tab_name] = content_frame
        self._create_checkboxes(content_frame, units, block_type)

    def _create_checkboxes(self, parent, units, block_type):
        """Create checkboxes based on block type (none, cost, trait)."""
        if block_type == "cost":
            cost_groups = defaultdict(list)
            for unit in units:
                eng_unit = self.reverse_translation.get(unit, unit) if self.language == "Chinese" else unit
                cost_groups[self.unit_costs[eng_unit]].append(unit)
            for cost in sorted(cost_groups.keys()):
                frame = ttk.LabelFrame(parent, text=f"{cost} Cost Units", padding=5)
                frame.pack(fill="x", padx=5, pady=5)
                self._add_checkboxes_to_frame(frame, sorted(cost_groups[cost]))
        elif block_type == "trait":
            trait_groups = defaultdict(list)
            for trait, info in self.traits_data.items():
                for eng_unit in info["units"]:
                    unit = self.translation.get(eng_unit, eng_unit) if self.language == "Chinese" else eng_unit
                    if unit in units:
                        trait_groups[trait].append(unit)
            for trait in sorted(trait_groups.keys()):
                frame = ttk.LabelFrame(parent, text=trait, padding=5)
                frame.pack(fill="x", padx=5, pady=5)
                self._add_checkboxes_to_frame(frame, sorted(trait_groups[trait]))
        else:
            self._add_checkboxes_to_frame(parent, units)

    def _add_checkboxes_to_frame(self, frame, units):
        """Add individual checkboxes to a frame."""
        for i, unit in enumerate(units):
            chk = ttk.Checkbutton(frame, text=unit, variable=self.check_vars[unit], command=self.update_selection)
            chk.grid(row=i // 5, column=i % 5, sticky="w", padx=5, pady=2)

    def _show_tab_content(self, tab_name):
        """Show the content of the selected tab in the scrollable frame."""
        for child in self.scrollable_frame.winfo_children():
            child.pack_forget()
        self.tab_contents[tab_name].pack(fill="both", expand=True)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_tab_changed(self, event):
        """Handle tab change event to update displayed content."""
        selected_tab = self.unit_notebook.tab(self.unit_notebook.select(), "text")
        self._show_tab_content(selected_tab)

    def _create_selected_units_area(self):
        """Create the area to display selected units."""
        self.right_frame = ttk.Frame(self.main_frame)
        self.right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=5)

        self.selected_frame = ttk.LabelFrame(self.right_frame, text=self._translate_text("Selected Units"), padding=10)
        self.selected_frame.pack(fill="both", expand=True)

        self.selected_listbox = tk.Listbox(self.selected_frame, height=20, width=30)
        self.selected_listbox.pack(fill="both", expand=True)

    def _create_button_area(self):
        """Create the button area."""
        self.button_frame = ttk.Frame(self.root)
        self.button_frame.pack(pady=5)

        ttk.Button(self.button_frame, text=self._translate_text("Filter Combinations"), command=self.show_results).pack(side="left", padx=5)
        ttk.Button(self.button_frame, text=self._translate_text("Clear Selection"), command=self.clear_selection).pack(side="left", padx=5)
        ttk.Button(self.button_frame, text=self._translate_text("Copy Selected"), command=self.copy_selected_results).pack(side="left", padx=5)

    def _create_result_area(self):
        """Create the result display area with Treeview."""
        self.result_frame = ttk.LabelFrame(self.root, text=self._translate_text("Filter Results"), padding=10)
        self.result_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.result_tree = ttk.Treeview(self.result_frame, columns=("Units", "Total Cost", "Trait Count", "Traits"), 
                                        show="headings", height=15)
        self.result_tree.pack(fill="both", expand=True)

        self.result_tree.heading("Units", text=self._translate_text("Additional Units Needed"))
        self.result_tree.heading("Total Cost", text=self._translate_text("Total Cost"))
        self.result_tree.heading("Trait Count", text=self._translate_text("Trait Count"))
        self.result_tree.heading("Traits", text=self._translate_text("Activated Traits"))

        self.result_tree.column("Units", width=300)
        self.result_tree.column("Total Cost", width=80, anchor="center")
        self.result_tree.column("Trait Count", width=80, anchor="center")
        self.result_tree.column("Traits", width=200)

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling for the unit selection canvas."""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def update_selection(self):
        """Update the selected units and refresh the listbox."""
        selected_translated = {unit for unit, var in self.check_vars.items() if var.get()}
        self.selected_units = {self.reverse_translation.get(unit, unit) if self.language == "Chinese" else unit 
                              for unit in selected_translated}
        print("Selected units (English):", self.selected_units)

        self.selected_listbox.delete(0, tk.END)
        for unit in sorted(selected_translated):
            self.selected_listbox.insert(tk.END, unit)

    def clear_selection(self):
        """Clear all selections and refresh the listbox."""
        for var in self.check_vars.values():
            var.set(False)
        self.selected_units.clear()
        self.selected_listbox.delete(0, tk.END)
        print("All selections cleared.")

    def show_results(self):
        """Display filtered results in the Treeview, showing only additional units needed."""
        self.result_tree.delete(*self.result_tree.get_children())

        if not self.selected_units:
            self.result_tree.insert("", "end", values=(self._translate_text("Please select at least one unit."), "", "", ""))
            return

        filtered = filter_combinations(self.combinations, self.selected_units)
        if not filtered:
            self.result_tree.insert("", "end", values=(self._translate_text("No combinations found."), "", "", ""))
            return

        filtered.sort(key=lambda x: (x["total_cost"], -x["trait_count"]))
        self.result_tree.insert("", "end", values=(f"{self._translate_text('Found')} {len(filtered)} {self._translate_text('combinations')}", "", "", ""))

        for i, combo in enumerate(filtered[:10], 1):
            additional_units = combo["units"] - self.selected_units
            translated_additional_units = [self.translation.get(unit, unit) if self.language == "Chinese" else unit for unit in additional_units]
            units_str = ", ".join(translated_additional_units) if translated_additional_units else self._translate_text("None")
            traits_str = ", ".join(combo["activated_traits"])
            self.result_tree.insert("", "end", values=(units_str, combo["total_cost"], combo["trait_count"], traits_str))

    def copy_selected_results(self):
        """Copy selected results from Treeview to clipboard."""
        selected_items = self.result_tree.selection()
        if not selected_items:
            return

        clipboard_text = ""
        for item in selected_items:
            values = self.result_tree.item(item, "values")
            clipboard_text += f"{self._translate_text('Additional Units Needed')}: {values[0]}\n{self._translate_text('Total Cost')}: {values[1]}\n{self._translate_text('Trait Count')}: {values[2]}\n{self._translate_text('Activated Traits')}: {values[3]}\n\n"

        self.root.clipboard_clear()
        self.root.clipboard_append(clipboard_text)
        print("Selected results copied to clipboard.")

# Function to dynamically get the file path
def resource_path(relative_path):
    """Get the file path for both packaged and development environments"""
    if hasattr(sys, '_MEIPASS'):
        # Packaged environment, files are in the temporary extraction directory
        return os.path.join(sys._MEIPASS, relative_path)
    else:
        # Development environment, use relative path
        return os.path.join(os.path.dirname(__file__), relative_path)
    
# Main Program
if __name__ == "__main__":
    combinations = file_processor.read_json(resource_path("./etc/traits_tracker_result_30000.json"))
    unit_costs = file_processor.read_json(resource_path("./etc/units_cost.json"))
    traits_data = file_processor.read_json(resource_path("./etc/traits_units_activations.json"))
    root = tk.Tk()
    root.geometry("1000x800")
    app = TraitsFilterApp(root, combinations, unit_costs, traits_data)
    root.mainloop()