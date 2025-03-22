import json
import os
import sys
import tkinter as tk
import yaml
from tkinter import ttk
from collections import defaultdict
from functools import lru_cache

# Dynamically add the packaged module path
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
    sys.path.append(os.path.join(base_path, 'language'))
    sys.path.append(os.path.join(base_path, 'utils'))
else:
    base_path = os.path.dirname(__file__)

from language.en_zh_tw import unit_translation, ui_translations
from utils import file_processor

class TraitsFilterApp:
    def __init__(self, root, combinations, unit_costs, traits_data):
        self.root = root
        self.root.title("Traits Combination Filter")
        self.unit_costs = unit_costs
        self.traits_data = traits_data
        self.selected_units = set()
        self.language = "English"
        self.translation = unit_translation
        self.reverse_translation = {v: k for k, v in unit_translation.items()}
        self.filtered_results = []
        
        # Preprocess combinations (more efficiently)
        self.combinations = [
            {
                "units": frozenset(combo["units"]),  # Using frozenset for better performance
                "total_cost": combo["total_cost"],
                "trait_count": combo["trait_count"],
                "activated_traits": tuple(combo["activated_traits"])  # Using tuple for immutability
            }
            for combo in combinations
        ]
        self.all_units = sorted(set().union(*(combo["units"] for combo in self.combinations)))
        self.translated_units = self._translate_units(self.all_units)
        self.check_vars = {unit: tk.BooleanVar() for unit in self.translated_units}

        # Setup UI
        self._setup_ui()
        
        # Bind keys for better user experience
        self.root.bind("<Control-f>", lambda e: self.show_results())
        self.root.bind("<Control-c>", lambda e: self.copy_selected_results())
        
    def _translate_units(self, units):
        """Translate unit names based on current language."""
        if self.language == "English":
            return list(units)
        else:  # Chinese
            return [self.translation.get(unit, unit) for unit in units]

    def _translate_text(self, text):
        """Translate UI text based on current language."""
        return ui_translations[self.language].get(text, text)

    def _setup_ui(self):
        """Initialize the main UI components."""
        self._create_language_selector()
        
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True)

        self._create_unit_selection_area()
        self._create_selected_units_area()
        self._create_button_area()
        self._create_result_area()
        
        # Add status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _create_language_selector(self):
        """Create language selection UI component."""
        lang_frame = ttk.Frame(self.root)
        lang_frame.pack(fill="x", pady=5)
        ttk.Label(lang_frame, text="Language:").pack(side="left", padx=5)
        self.lang_combo = ttk.Combobox(lang_frame, values=["English", "Chinese"], state="readonly")
        self.lang_combo.set("English")
        self.lang_combo.pack(side="left")
        self.lang_combo.bind("<<ComboboxSelected>>", self._change_language)

    def _change_language(self, event):
        """Handle language change and refresh UI."""
        new_language = self.lang_combo.get()
        
        # Save the old selection state (based on current language)
        old_check_states = {}
        for unit, var in self.check_vars.items():
            if self.language == "Chinese":
                eng_unit = self.reverse_translation.get(unit, unit)
            else:
                eng_unit = unit
            old_check_states[eng_unit] = var.get()
        
        # Update language and units
        self.language = new_language
        self.translated_units = self._translate_units(self.all_units)
        
        # Rebuild check_vars based on the new language
        self.check_vars = {}
        for unit in self.translated_units:
            if self.language == "Chinese":
                eng_unit = self.reverse_translation.get(unit, unit)
            else:
                eng_unit = unit
            self.check_vars[unit] = tk.BooleanVar(value=old_check_states.get(eng_unit, False))
        
        self._refresh_ui()

    def _refresh_ui(self):
        """Refresh all UI elements with the current language."""
        self.root.title(self._translate_text("Traits Combination Filter"))
        
        # Update frame titles
        self.unit_frame.config(text=self._translate_text("Select Your Units"))
        self.selected_frame.config(text=self._translate_text("Selected Units"))
        self.result_frame.config(text=self._translate_text("Filter Results"))

        # Rebuild the tabs
        self._rebuild_tabs()
        
        # Update buttons
        for widget in self.button_frame.winfo_children():
            widget.destroy()
        ttk.Button(self.button_frame, text=self._translate_text("Filter Combinations"), 
                  command=self.show_results).pack(side="left", padx=5)
        ttk.Button(self.button_frame, text=self._translate_text("Clear Selection"), 
                  command=self.clear_selection).pack(side="left", padx=5)
        ttk.Button(self.button_frame, text=self._translate_text("Copy Selected"), 
                  command=self.copy_selected_results).pack(side="left", padx=5)

        # Update Treeview headings
        self._update_treeview_headings()
        
        # Refresh selected units and results
        self.update_selection()
        self.show_results()

    def _rebuild_tabs(self):
        """Rebuild the unit tabs with current language."""
        for tab_id in self.unit_notebook.tabs():
            self.unit_notebook.forget(tab_id)
        self.tab_contents.clear()

        self._add_tab(self._translate_text("Alphabetical Order"), sorted(self.translated_units), "none")
        
        # Sort by cost
        sorted_by_cost = sorted(self.translated_units, 
                               key=lambda x: self.unit_costs[self.reverse_translation.get(x, x) 
                                                           if self.language == "Chinese" else x])
        self._add_tab(self._translate_text("Cost Order"), sorted_by_cost, "cost")
        
        # Sort by trait
        self._add_tab(self._translate_text("Trait Order"), self.translated_units, "trait")
        self._show_tab_content(self._translate_text("Alphabetical Order"))
    
    def _update_treeview_headings(self):
        """Update treeview headings to current language."""
        self.result_tree.heading("Units", text=self._translate_text("Additional Units Needed"))
        self.result_tree.heading("Total Cost", text=self._translate_text("Total Cost"))
        self.result_tree.heading("Trait Count", text=self._translate_text("Trait Count"))
        self.result_tree.heading("Traits", text=self._translate_text("Activated Traits"))

    def _create_unit_selection_area(self):
        """Create the unit selection area with fixed tabs and scrollable content."""
        self.left_frame = ttk.Frame(self.main_frame)
        self.left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=5)

        self.unit_frame = ttk.LabelFrame(self.left_frame, text=self._translate_text("Select Your Units"), padding=10)
        self.unit_frame.pack(fill="both", expand=True)

        # Notebook for tabs
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
                     sorted(self.translated_units, 
                            key=lambda x: self.unit_costs[self.reverse_translation.get(x, x) 
                                                        if self.language == "Chinese" else x]), 
                     "cost")
        self._add_tab(self._translate_text("Trait Order"), self.translated_units, "trait")

        self.unit_notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self._show_tab_content(self._translate_text("Alphabetical Order"))

        # Bind mouse wheel - only to the canvas
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_linux_scroll)
        self.canvas.bind("<Button-5>", self._on_linux_scroll)

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
            # Organize by cost
            cost_groups = defaultdict(list)
            for unit in units:
                eng_unit = self.reverse_translation.get(unit, unit) if self.language == "Chinese" else unit
                cost_groups[self.unit_costs[eng_unit]].append(unit)
            
            for cost in sorted(cost_groups.keys()):
                frame = ttk.LabelFrame(parent, text=f"{cost} Cost Units", padding=5)
                frame.pack(fill="x", padx=5, pady=5)
                self._add_checkboxes_to_frame(frame, sorted(cost_groups[cost]))
        
        elif block_type == "trait":
            # Organize by trait
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
            # Simple alphabetical listing
            self._add_checkboxes_to_frame(parent, units)

    def _add_checkboxes_to_frame(self, frame, units):
        """Add individual checkboxes to a frame."""
        for i, unit in enumerate(units):
            chk = ttk.Checkbutton(frame, text=unit, variable=self.check_vars[unit], 
                                 command=self.update_selection)
            chk.grid(row=i // 5, column=i % 5, sticky="w", padx=5, pady=2)

    def _show_tab_content(self, tab_name):
        """Show the content of the selected tab in the scrollable frame."""
        for child in self.scrollable_frame.winfo_children():
            child.pack_forget()
        if tab_name in self.tab_contents:
            self.tab_contents[tab_name].pack(fill="both", expand=True)
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        # Reset scroll position to top
        self.canvas.yview_moveto(0)

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
        self.selected_scrollbar = ttk.Scrollbar(self.selected_frame, orient="vertical", 
                                              command=self.selected_listbox.yview)
        self.selected_listbox.config(yscrollcommand=self.selected_scrollbar.set)
        self.selected_listbox.pack(side="left", fill="both", expand=True)
        self.selected_scrollbar.pack(side="right", fill="y")

    def _create_button_area(self):
        """Create the button area."""
        self.button_frame = ttk.Frame(self.root)
        self.button_frame.pack(pady=5)

        ttk.Button(self.button_frame, text=self._translate_text("Filter Combinations"), 
                  command=self.show_results).pack(side="left", padx=5)
        ttk.Button(self.button_frame, text=self._translate_text("Clear Selection"), 
                  command=self.clear_selection).pack(side="left", padx=5)
        ttk.Button(self.button_frame, text=self._translate_text("Copy Selected"), 
                  command=self.copy_selected_results).pack(side="left", padx=5)

    def _create_result_area(self):
        """Create the result display area with Treeview."""
        self.result_frame = ttk.LabelFrame(self.root, text=self._translate_text("Filter Results"), padding=10)
        self.result_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Create a frame for the Treeview and scrollbar
        tree_frame = ttk.Frame(self.result_frame)
        tree_frame.pack(fill="both", expand=True)
        
        # Create the Treeview with scrollbars
        self.result_tree = ttk.Treeview(tree_frame, columns=("Units", "Total Cost", "Trait Count", "Traits"), 
                                      show="headings", height=15)
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.result_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.result_tree.xview)
        self.result_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout for Treeview and scrollbars
        self.result_tree.grid(column=0, row=0, sticky='nsew')
        vsb.grid(column=1, row=0, sticky='ns')
        hsb.grid(column=0, row=1, sticky='ew')
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        # Configure column headings and widths
        self.result_tree.heading("Units", text=self._translate_text("Additional Units Needed"))
        self.result_tree.heading("Total Cost", text=self._translate_text("Total Cost"))
        self.result_tree.heading("Trait Count", text=self._translate_text("Trait Count"))
        self.result_tree.heading("Traits", text=self._translate_text("Activated Traits"))

        self.result_tree.column("Units", width=300, minwidth=150)
        self.result_tree.column("Total Cost", width=80, minwidth=50, anchor="center")
        self.result_tree.column("Trait Count", width=80, minwidth=50, anchor="center")
        self.result_tree.column("Traits", width=200, minwidth=100)

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling for the unit selection canvas."""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def _on_linux_scroll(self, event):
        """Handle mouse wheel scrolling on Linux."""
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")

    def update_selection(self):
        """Update the selected units and refresh the listbox."""
        selected_translated = {unit for unit, var in self.check_vars.items() if var.get()}
        self.selected_units = {self.reverse_translation.get(unit, unit) if self.language == "Chinese" else unit 
                              for unit in selected_translated}

        self.selected_listbox.delete(0, tk.END)
        for unit in sorted(selected_translated):
            self.selected_listbox.insert(tk.END, unit)
        
        self.status_var.set(f"{len(self.selected_units)} units selected")

    def clear_selection(self):
        """Clear all selections and refresh the listbox."""
        for var in self.check_vars.values():
            var.set(False)
        self.selected_units.clear()
        self.selected_listbox.delete(0, tk.END)
        self.status_var.set("All selections cleared")
        self.result_tree.delete(*self.result_tree.get_children())

    @lru_cache(maxsize=128)
    def _filter_combinations_cached(self, selected_units_tuple):
        """Cached version of filter combinations for better performance."""
        selected_set = set(selected_units_tuple)
        return [combo for combo in self.combinations if selected_set.issubset(combo["units"])]

    def show_results(self):
        """Display filtered results in the Treeview, showing only additional units needed."""
        self.result_tree.delete(*self.result_tree.get_children())
        self.status_var.set("Filtering combinations...")
        self.root.update()  # Update UI to show status change

        if not self.selected_units:
            self.result_tree.insert("", "end", values=(self._translate_text("Please select at least one unit."), "", "", ""))
            self.status_var.set("Ready")
            return

        # Use the cached filter function with an immutable key
        selected_units_tuple = tuple(sorted(self.selected_units))
        self.filtered_results = self._filter_combinations_cached(selected_units_tuple)
        
        if not self.filtered_results:
            self.result_tree.insert("", "end", values=(self._translate_text("No combinations found."), "", "", ""))
            self.status_var.set("No combinations found")
            return

        # Sort results efficiently
        self.filtered_results.sort(key=lambda x: (x["total_cost"], -x["trait_count"]))
        
        # Show the results count
        result_count = len(self.filtered_results)
        self.result_tree.insert("", "end", 
                               values=(f"{self._translate_text('Found')} {result_count} {self._translate_text('combinations')}", "", "", ""))

        # Show the top results (pagination could be added for large datasets)
        max_display = min(100, len(self.filtered_results))
        for i, combo in enumerate(self.filtered_results[:max_display], 1):
            additional_units = set(combo["units"]) - self.selected_units
            translated_additional = [self.translation.get(unit, unit) if self.language == "Chinese" else unit 
                                    for unit in additional_units]
            units_str = ", ".join(sorted(translated_additional)) if translated_additional else self._translate_text("None")
            traits_str = ", ".join(combo["activated_traits"])
            self.result_tree.insert("", "end", values=(units_str, combo["total_cost"], combo["trait_count"], traits_str))

        self.status_var.set(f"Found {result_count} combinations, displaying {max_display}")

    def copy_selected_results(self):
        """Copy selected results from Treeview to clipboard."""
        selected_items = self.result_tree.selection()
        if not selected_items:
            self.status_var.set("No items selected to copy")
            return

        clipboard_text = ""
        for item in selected_items:
            values = self.result_tree.item(item, "values")
            if values[0] and not values[0].startswith(self._translate_text("Found")) and not values[0].startswith(self._translate_text("No combinations")):
                clipboard_text += (f"{self._translate_text('Additional Units Needed')}: {values[0]}\n"
                                  f"{self._translate_text('Total Cost')}: {values[1]}\n"
                                  f"{self._translate_text('Trait Count')}: {values[2]}\n"
                                  f"{self._translate_text('Activated Traits')}: {values[3]}\n\n")

        if clipboard_text:
            self.root.clipboard_clear()
            self.root.clipboard_append(clipboard_text)
            self.status_var.set("Selected results copied to clipboard")
        else:
            self.status_var.set("No valid items to copy")

def resource_path(relative_path):
    """Get the file path for both packaged and development environments"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    else:
        root_dir = os.path.dirname(os.path.dirname(__file__))
        return os.path.join(root_dir, relative_path)
        
# Main Program
if __name__ == "__main__":
    combinations = file_processor.read_json(resource_path("./etc/traits_tracker_result_30000.json"))
    unit_costs = file_processor.read_json(resource_path("./etc/units_cost.json"))
    traits_data = file_processor.read_json(resource_path("./etc/traits_units_activations.json"))
    
    root = tk.Tk()
    root.geometry("1000x800")
    app = TraitsFilterApp(root, combinations, unit_costs, traits_data)
    root.mainloop()