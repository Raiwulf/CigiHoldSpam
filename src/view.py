import customtkinter as ctk
from PIL import ImageTk
import os
import sys
from core.config_manager import ConfigManager
from core.spam_controller import SpamController

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("CigiHoldSpam")
        self.geometry("300x300")

        self.config_manager = ConfigManager()

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

        icon_actual_path = resource_path(os.path.join("res", "resolute_cmp.ico"))
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

    def _handle_trigger_met(self):
        if self.spamming_label.winfo_exists():
            self.spamming_label.configure(text="Executing", text_color="green")

    def _handle_trigger_not_met(self):
        if self.spamming_label.winfo_exists():
            self.spamming_label.configure(text="Waiting", text_color="red")

    def _on_active_toggle(self):
        self._update_spamming_label_visibility()
        if self.active_toggle_var.get() == "on":
            if not self.spam_controller.is_operable():
                print("View: Spam Controller is not operable.")
                self.active_toggle_var.set("off")
                self._update_spamming_label_visibility()
                return
            
            self.spam_controller.start()
        else:
            self.spam_controller.stop()

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
        setup_tab.grid_rowconfigure(0, weight=0)
        setup_tab.grid_rowconfigure(1, weight=0)
        setup_tab.grid_rowconfigure(2, weight=1)

        input_fields_group = ctk.CTkFrame(setup_tab) 
        input_fields_group.grid(row=0, column=0, pady=(20,10), padx=10, sticky="") 
        
        input_fields_group.grid_columnconfigure(0, weight=0) 
        input_fields_group.grid_columnconfigure(1, weight=0) 

        fields = [
            ("ProcessName:", "ProcessName", 0),
            ("TriggerKey:", "TriggerKey", 1),
            ("SpamKey:", "SpamKey", 2),
            ("Delay(ms):", "DelayMS", 3)
        ]
        self.entries = {}
        for label_text, config_key, row_idx in fields:
            label = ctk.CTkLabel(input_fields_group, text=label_text, anchor="w")
            label.grid(row=row_idx, column=0, padx=(10,5), pady=(5,5), sticky="w")
            
            entry = ctk.CTkEntry(input_fields_group, width=150) 
            entry.grid(row=row_idx, column=1, padx=(0,10), pady=(5,5), sticky="w")
            entry.insert(0, self.config_manager.get_setting("Settings", config_key))
            self.entries[config_key] = entry
        
        buttons_group = ctk.CTkFrame(setup_tab) 
        buttons_group.grid(row=1, column=0, pady=(10,20), padx=10, sticky="") 

        buttons_group.grid_columnconfigure(0, weight=0) 
        buttons_group.grid_columnconfigure(1, weight=0) 

        button_width = 100 
        save_button = ctk.CTkButton(buttons_group, text="Save", command=self._save_settings, width=button_width)
        save_button.grid(row=0, column=0, padx=(10,5), pady=10, sticky="") 

        load_button = ctk.CTkButton(buttons_group, text="Load", command=self._load_settings_from_config, width=button_width)
        load_button.grid(row=0, column=1, padx=(5,10), pady=10, sticky="") 

    def _load_settings_from_config(self):
        for config_key, entry_widget in self.entries.items():
            entry_widget.delete(0, ctk.END)
            value = self.config_manager.get_setting("Settings", config_key)
            if config_key == "SpamKey" and isinstance(value, list):
                entry_widget.insert(0, ",".join(value))
            else:
                entry_widget.insert(0, value)
        print("Settings loaded!")

    def _save_settings(self):
        for config_key, entry_widget in self.entries.items():
            self.config_manager.set_setting("Settings", config_key, entry_widget.get())
        print("Settings saved!") 