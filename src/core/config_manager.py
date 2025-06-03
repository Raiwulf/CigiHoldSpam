import configparser
import os

CONFIG_FILE = "config.ini"
DEFAULT_SETTINGS = {
    "Settings": {
        "ProcessName": "Notepad.exe",
        "TriggerKey": "2",
        "SpamKey": "3",
        "DelayMS": "100"
    }
}

class ConfigManager:
    def __init__(self, config_file=CONFIG_FILE):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self._load_config()

    def _load_config(self):
        if not os.path.exists(self.config_file):
            self._create_default_config()
        self.config.read(self.config_file)
        for section, settings in DEFAULT_SETTINGS.items():
            if not self.config.has_section(section):
                self.config.add_section(section)
            for key, value in settings.items():
                if not self.config.has_option(section, key):
                    self.config.set(section, key, value)
        self._save_config()

    def _create_default_config(self):
        for section, settings in DEFAULT_SETTINGS.items():
            self.config.add_section(section)
            for key, value in settings.items():
                self.config.set(section, key, value)
        self._save_config()

    def _save_config(self):
        with open(self.config_file, 'w') as f:
            self.config.write(f)

    def get_setting(self, section, key):
        if not self.config.has_section(section) or not self.config.has_option(section, key):
            default_value = DEFAULT_SETTINGS.get(section, {}).get(key)
            if key == "SpamKey" and default_value:
                return [k.strip() for k in default_value.split(',')]
            return default_value
        value = self.config.get(section, key)
        if key == "SpamKey":
            return [k.strip() for k in value.split(',')]
        return value

    def set_setting(self, section, key, value):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, str(value))
        self._save_config()
