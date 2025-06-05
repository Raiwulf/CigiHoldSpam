import customtkinter as ctk
from PIL import ImageTk
import os
import sys
from tkinter import messagebox
from core.config_manager import ConfigManager
from core.spam_controller import SpamController

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("CigiHoldSpam")
        self.geometry("350x400")

        self.config_manager = ConfigManager()
        self.entry_string_vars = {} # To hold our StringVars
        self.setup_name_var = ctk.StringVar()
        self.selected_setup_var = ctk.StringVar()

        self.spam_controller = SpamController(
            config_manager=self.config_manager,
            root_tk_window=self, 
            on_trigger_met_callback=self._handle_trigger_met,
            on_trigger_not_met_callback=self._handle_trigger_not_met
        )

        self.tab_view = ctk.CTkTabview(self)
        self.tab_view.pack(expand=True, fill="both", padx=5, pady=5)

        self.features_tab = self.tab_view.add("Features")
        self.setup_tab = self.tab_view.add("Setup")

        self._create_features_tab_widgets()
        self._create_setup_tab_widgets()
        
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Helper function to get resource path
        def resource_path(relative_path):
            """ Get absolute path to resource, works for dev and for PyInstaller """
            try:
                # PyInstaller creates a temp folder and stores path in _MEIPASS
                base_path = sys._MEIPASS
            except Exception:
                base_path = os.path.abspath(".")

            return os.path.join(base_path, relative_path)

        icon_actual_path = resource_path(os.path.join("res", "app.png"))
        self.iconpath = ImageTk.PhotoImage(file=icon_actual_path)
        self.wm_iconbitmap()
        self.iconphoto(False, self.iconpath)

    def _create_features_tab_widgets(self):
        features_tab = self.tab_view.tab("Features")
        features_tab.grid_columnconfigure(0, weight=1)

        self.active_toggle_var = ctk.StringVar(value="off")
        self.active_toggle = ctk.CTkSwitch(
            features_tab,
            text="Active",
            variable=self.active_toggle_var,
            onvalue="on",
            offvalue="off",
            command=self._on_active_toggle
        )
        self.active_toggle.pack(pady=(20, 5))

        self.spamming_label = ctk.CTkLabel(features_tab, text="Waiting", text_color="red")
        self._update_spamming_label_visibility()

        self.active_setup_label = ctk.CTkLabel(features_tab, text="Active Setup: None")
        # This label will be shown/hidden by the _on_active_toggle method.

    def _handle_trigger_met(self):
        if self.spamming_label.winfo_exists():
            self.spamming_label.configure(text="Executing", text_color="green")

    def _handle_trigger_not_met(self):
        if self.spamming_label.winfo_exists():
            self.spamming_label.configure(text="Waiting", text_color="red")

    def _on_active_toggle(self):
        self._update_spamming_label_visibility()
        if self.active_toggle_var.get() == "on":
            active_setup_name = self.selected_setup_var.get()
            if not active_setup_name:
                messagebox.showerror("Error", "No setup is selected. Please select a setup from the dropdown.")
                self.active_toggle_var.set("off")
                self._update_spamming_label_visibility()
                return

            # Ensure the selected config is loaded before creating the snapshot
            self.config_manager.load_setup(active_setup_name)
            
            # Create the settings snapshot
            settings_snapshot = {
                "ProcessName": self.config_manager.get_setting("Settings", "ProcessName"),
                "TriggerKey": self.config_manager.get_setting("Settings", "TriggerKey"),
                "SpamKey": self.config_manager.get_setting("Settings", "SpamKey"),
                "DelayMS": self.config_manager.get_setting("Settings", "DelayMS")
            }

            if not self.spam_controller.is_operable():
                print("View: Spam Controller is not operable.")
                self.active_toggle_var.set("off")
                self._update_spamming_label_visibility()
                return
            
            if self.spam_controller.start(settings_snapshot):
                self.active_setup_label.configure(text=f"Active Setup: {active_setup_name}")
                self.active_setup_label.pack(pady=(0, 5))
        else:
            self.spam_controller.stop()
            self.active_setup_label.pack_forget()

    def _update_spamming_label_visibility(self):
        if not self.spamming_label.winfo_exists(): return
        if self.active_toggle_var.get() == "on":
            self.spamming_label.pack(pady=5)
        else:
            self.spamming_label.pack_forget()
            self._handle_trigger_not_met()

    def _on_closing(self):
        if self.spam_controller:
            self.spam_controller.stop()
        self.destroy()

    def _create_setup_tab_widgets(self):
        setup_tab = self.tab_view.tab("Setup")

        setup_tab.grid_columnconfigure(0, weight=1)

        # --- Setup Selection Frame ---
        selection_frame = ctk.CTkFrame(setup_tab)
        selection_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        selection_frame.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(selection_frame, text="Select Setup:").grid(row=0, column=0, padx=(10,5), pady=10, sticky="w")
        
        self.setup_selector = ctk.CTkComboBox(selection_frame, variable=self.selected_setup_var, command=self._on_setup_selected)
        self.setup_selector.grid(row=0, column=1, padx=(0,5), pady=10, sticky="ew")

        add_button = ctk.CTkButton(selection_frame, text="+", width=30, command=self._create_new_setup)
        add_button.grid(row=0, column=2, padx=(0,10), pady=10, sticky="e")

        # --- Separator Line ---
        separator = ctk.CTkFrame(setup_tab, height=2, fg_color="gray25")
        separator.grid(row=1, column=0, pady=5, sticky="ew")

        # --- Input Fields Group ---
        input_fields_group = ctk.CTkFrame(setup_tab) 
        input_fields_group.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        input_fields_group.grid_columnconfigure(1, weight=1)

        fields = [
            ("Setup Name:", "SetupName", 0),
            ("ProcessName:", "ProcessName", 1),
            ("TriggerKey:", "TriggerKey", 2),
            ("SpamKey:", "SpamKey", 3),
            ("Delay(ms):", "DelayMS", 4)
        ]
        self.entries = {}
        for label_text, config_key, row_idx in fields:
            label = ctk.CTkLabel(input_fields_group, text=label_text, anchor="w")
            label.grid(row=row_idx, column=0, padx=(10,5), pady=(5,5), sticky="w")
            
            string_var = ctk.StringVar()
            if config_key == "SetupName":
                self.setup_name_var = string_var
            else:
                self.entry_string_vars[config_key] = string_var

            entry = ctk.CTkEntry(input_fields_group, width=200, textvariable=string_var) 
            entry.grid(row=row_idx, column=1, padx=(0,10), pady=(5,5), sticky="ew")
            self.entries[config_key] = entry
        
        # --- Buttons Group ---
        buttons_group = ctk.CTkFrame(setup_tab) 
        buttons_group.grid(row=3, column=0, pady=(5, 10), padx=10, sticky="ew")
        buttons_group.grid_columnconfigure((0,1), weight=1)

        save_button = ctk.CTkButton(buttons_group, text="Save", command=self._save_settings)
        save_button.grid(row=0, column=0, padx=5, pady=10, sticky="ew") 

        delete_button = ctk.CTkButton(buttons_group, text="Delete", command=self._delete_setting, fg_color="red", hover_color="darkred")
        delete_button.grid(row=0, column=1, padx=5, pady=10, sticky="ew") 

        self._populate_setup_selector()
        
    def _create_new_setup(self):
        """Clears the UI fields to prepare for creating a new setup."""
        self.setup_selector.set("") # Clear selection in dropdown
        self.setup_name_var.set("New Setup") # Suggest a name
        
        # Clear other entry fields by setting them to default values from the config manager
        for config_key, string_var in self.entry_string_vars.items():
            default_val = self.config_manager.get_setting("Settings", config_key) # Use default from manager
            if config_key == "SpamKey" and isinstance(default_val, list):
                string_var.set(",".join(default_val))
            else:
                string_var.set(default_val or "")

        print("UI cleared for new setup creation.")
        # Set focus to the setup name entry to encourage editing
        self.entries["SetupName"].focus()

    def _populate_setup_selector(self):
        setups = self.config_manager.list_setups()
        self.setup_selector.configure(values=setups)
        if setups:
            # Check if active config is still valid, else pick first one
            current_active = self.config_manager.active_config_name
            if current_active and current_active in setups:
                self.selected_setup_var.set(current_active)
                self._load_settings_for_setup(current_active)
            else:
                self.selected_setup_var.set(setups[0])
                self._on_setup_selected(setups[0])
        else:
            # No configs exist, load a blank/default state
            self.setup_name_var.set("New Setup")
            self._load_settings_for_setup(None)

    def _on_setup_selected(self, selected_setup_name):
        self._load_settings_for_setup(selected_setup_name)

    def _load_settings_for_setup(self, setup_name):
        if setup_name is None: # For a blank state
             self.config_manager.active_config_name = None
             self.config_manager.config.clear()
        else:
            self.config_manager.load_setup(setup_name)
        
        self.setup_name_var.set(setup_name or "")

        for config_key, string_var in self.entry_string_vars.items():
            value = self.config_manager.get_setting("Settings", config_key)
            if config_key == "SpamKey" and isinstance(value, list):
                string_var.set(",".join(value))
            else:
                string_var.set(value or "") # Ensure we set something
        print(f"Settings loaded for: {setup_name}")

    def _save_settings(self):
        setup_name = self.setup_name_var.get()
        if not setup_name or setup_name.isspace():
            messagebox.showerror("Error", "Setup Name cannot be empty.")
            return

        settings_to_save = {key: var.get() for key, var in self.entry_string_vars.items()}
        self.config_manager.save_setup(setup_name, settings_to_save)
        
        print(f"Settings saved for: {setup_name}")
        # messagebox.showinfo("Success", f"Setup '{setup_name}' saved successfully.") # Dialog disabled per user request.

        self._populate_setup_selector()
        self.selected_setup_var.set(setup_name)

    def _delete_setting(self):
        setup_to_delete = self.selected_setup_var.get()
        if not setup_to_delete:
            messagebox.showerror("Error", "No setup selected to delete.")
            return

        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the setup '{setup_to_delete}'?"):
            if self.config_manager.delete_setup(setup_to_delete):
                print(f"Deleted setup: {setup_to_delete}")
                messagebox.showinfo("Success", f"Setup '{setup_to_delete}' has been deleted.")
                self._populate_setup_selector()
            else:
                messagebox.showerror("Error", f"Could not delete setup '{setup_to_delete}'.") 