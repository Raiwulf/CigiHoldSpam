import configparser
import os

CONFIG_DIR = "configs"
DEFAULT_SETUP_NAME = "Default"
DEFAULT_SETTINGS = {
    "Settings": {
        "ProcessName": "Notepad.exe",
        "TriggerKey": "2",
        "SpamKey": "3",
        "DelayMS": "100"
    }
}

class ConfigManager:
    def __init__(self):
        self.config_dir = CONFIG_DIR
        self.config = configparser.ConfigParser()
        os.makedirs(self.config_dir, exist_ok=True)
        self.active_config_name = None
    
    def get_config_path(self, setup_name):
        return os.path.join(self.config_dir, f"{setup_name}.ini")

    def list_setups(self):
        setups = [f.replace(".ini", "") for f in os.listdir(self.config_dir) if f.endswith(".ini")]
        if not setups:
            # Create a default config if none exist
            self.save_setup(DEFAULT_SETUP_NAME, DEFAULT_SETTINGS["Settings"])
            return [DEFAULT_SETUP_NAME]
        return setups

    def load_setup(self, setup_name):
        config_path = self.get_config_path(setup_name)
        if not os.path.exists(config_path):
            print(f"ConfigManager: Setup '{setup_name}' not found.")
            # Optionally create a default one if the requested one doesn't exist
            # self.save_setup(setup_name, DEFAULT_SETTINGS["Settings"])
            self.config.read_dict(DEFAULT_SETTINGS) # load default settings in memory
            self.active_config_name = setup_name # Treat as new unsaved config
            return

        self.config.read(config_path)
        self.active_config_name = setup_name
        
        # Ensure all default keys exist
        made_changes = False
        for section, settings in DEFAULT_SETTINGS.items():
            if not self.config.has_section(section):
                self.config.add_section(section)
                made_changes = True
            for key, value in settings.items():
                if not self.config.has_option(section, key):
                    self.config.set(section, key, value)
                    made_changes = True
        if made_changes:
            self._write_config_file(self.config, config_path)

    def _write_config_file(self, parser_obj, path):
        with open(path, 'w') as f:
            parser_obj.write(f)

    def save_setup(self, setup_name, settings_dict):
        # Create a new parser object for saving to ensure clean saves
        save_parser = configparser.ConfigParser()
        save_parser.add_section("Settings")
        for key, value in settings_dict.items():
            save_parser.set("Settings", key, str(value))
        
        config_path = self.get_config_path(setup_name)
        self._write_config_file(save_parser, config_path)
        
        # After saving, make this the active config
        self.load_setup(setup_name)

    def delete_setup(self, setup_name):
        config_path = self.get_config_path(setup_name)
        if os.path.exists(config_path):
            os.remove(config_path)
            if self.active_config_name == setup_name:
                self.config = configparser.ConfigParser() # Clear current config
                self.active_config_name = None
            return True
        return False

    def get_setting(self, section, key):
        if self.config.has_option(section, key):
            value = self.config.get(section, key)
            if key == "SpamKey":
                return [k.strip() for k in value.split(',')]
            return value
        
        # Fallback to default if not found in current config
        default_value = DEFAULT_SETTINGS.get(section, {}).get(key)
        if key == "SpamKey" and default_value:
            return [k.strip() for k in default_value.split(',')]
        return default_value

    def set_setting(self, section, key, value):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, str(value))
        # This method is now less important but let's make it work correctly if ever called
        if self.active_config_name:
             self._write_config_file(self.config, self.get_config_path(self.active_config_name))
