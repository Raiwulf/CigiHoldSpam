import platform
import random
from .key_mapper import KeyMapper
from .process_monitor import ProcessMonitor
from .input_simulator import InputSimulator

CHECK_INTERVAL_MS = 100
DEFAULT_DELAY_MS = 100

class SpamController:
    def __init__(self, config_manager, root_tk_window, on_trigger_met_callback, on_trigger_not_met_callback):
        self.config_manager = config_manager
        self.root_tk_window = root_tk_window
        self.on_trigger_met_callback = on_trigger_met_callback
        self.on_trigger_not_met_callback = on_trigger_not_met_callback

        self.key_mapper = KeyMapper()
        self.process_monitor = ProcessMonitor()
        self.input_simulator = InputSimulator()

        self.is_active = False
        self.listener_job_id = None
        
        self.dependencies_available = (
            self.key_mapper.is_operable() and 
            self.process_monitor.is_operable() and 
            self.input_simulator.is_operable() and
            platform.system() == "Windows"
        )

        if not self.dependencies_available:
            print("SpamController: One or more core components are not operable. Controller will not function.")

    def _send_spam_key_action(self, spam_vk_code, spam_key_char):
        if not self.is_active:
            return
        if not self.dependencies_available:
            return 
        
        self.input_simulator.send_key_press_release(spam_vk_code)

    def _check_conditions_loop(self):
        if not self.is_active:
            if self.listener_job_id:
                self.root_tk_window.after_cancel(self.listener_job_id)
                self.listener_job_id = None
            self.on_trigger_not_met_callback()
            return
        
        if not self.dependencies_available:
            self.stop()
            return

        target_process_name = self.config_manager.get_setting("Settings", "ProcessName")
        trigger_key_char = self.config_manager.get_setting("Settings", "TriggerKey")
        
        trigger_vk_code = self.key_mapper.get_vk_code(trigger_key_char)
        
        is_key_pressed = False
        if trigger_vk_code is not None:
            is_key_pressed = self.input_simulator.is_key_down(trigger_vk_code)
        
        is_focused = self.process_monitor.is_target_process_focused(target_process_name)

        if is_focused and is_key_pressed:
            self.on_trigger_met_callback()
            
            spam_key_char = self.config_manager.get_setting("Settings", "SpamKey")
            spam_vk_code = self.key_mapper.get_vk_code(spam_key_char)
            
            if spam_vk_code is not None:
                try:
                    base_delay_ms_str = self.config_manager.get_setting("Settings", "DelayMS")
                    base_delay_ms = int(base_delay_ms_str)
                except ValueError:
                    base_delay_ms = DEFAULT_DELAY_MS
                
                jitter_ms = random.randint(-4, 4)
                actual_delay_ms = max(0, base_delay_ms + jitter_ms)
                
                self.root_tk_window.after(actual_delay_ms, 
                                          lambda svk=spam_vk_code, skc=spam_key_char: \
                                          self._send_spam_key_action(svk, skc))
        else:
            self.on_trigger_not_met_callback()

        if self.is_active:
            self.listener_job_id = self.root_tk_window.after(CHECK_INTERVAL_MS, self._check_conditions_loop)

    def start(self):
        if not self.dependencies_available:
            print("SpamController: Cannot start, dependencies not available or not on Windows.")
            return False
            
        if self.is_active:
            return True

        self.is_active = True
        if self.listener_job_id:
            self.root_tk_window.after_cancel(self.listener_job_id)
        self._check_conditions_loop()
        return True

    def stop(self):
        if not self.is_active:
            return

        self.is_active = False
        if self.listener_job_id:
            self.root_tk_window.after_cancel(self.listener_job_id)
            self.listener_job_id = None
        self.on_trigger_not_met_callback()
        
    def is_operable(self):
        return self.dependencies_available 