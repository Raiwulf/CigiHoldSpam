import platform
import random
import time
from .key_mapper import KeyMapper
from .process_monitor import ProcessMonitor
from .input_simulator import InputSimulator

CHECK_INTERVAL_MS = 16
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
        self.active_settings = {} # Store the "locked-in" settings
        self.is_spamming = False  # Toggle state for spamming
        self.was_trigger_pressed = False  # Track previous trigger key state
        self.key_held_down = False  # Track if key is currently held down to prevent rapid toggling
        self.spam_loop_job_id = None  # Job ID for the continuous spam loop
        
        self.dependencies_available = (
            self.key_mapper.is_operable() and 
            self.process_monitor.is_operable() and 
            self.input_simulator.is_operable() and
            platform.system() == "Windows"
        )

        if not self.dependencies_available:
            print("SpamController: One or more core components are not operable. Controller will not function.")

    def _send_individual_key_action(self, spam_vk_code):
        if not self.is_active or not self.dependencies_available:
            return
        self.input_simulator.send_key_press_release(spam_vk_code)

    def _execute_spam_sequence(self, spam_key_chars, base_delay_ms):
        if not self.is_active or not self.dependencies_available or not self.is_spamming:
            return

        for i, key_char in enumerate(spam_key_chars):
            if not self.is_spamming:  # Check again in case toggled off during sequence
                return
            spam_vk_code = self.key_mapper.get_vk_code(key_char)
            if spam_vk_code is None:
                print(f"SpamController: Unknown spam key '{key_char}'")
                continue

            if i > 0:
                inter_key_delay_jitter_ms = random.uniform(-4, 4)
                inter_key_actual_delay_ms = max(0, base_delay_ms + inter_key_delay_jitter_ms)
                time.sleep(inter_key_actual_delay_ms / 1000.0)
            
            self._send_individual_key_action(spam_vk_code)

    def _spam_loop(self, spam_key_chars, base_delay_ms):
        """Continuous loop that executes spam sequence with delay between iterations."""
        if not self.is_active or not self.is_spamming or not self.dependencies_available:
            self.spam_loop_job_id = None
            return
        
        # Execute the spam sequence
        self._execute_spam_sequence(spam_key_chars, base_delay_ms)
        
        # Schedule next iteration if still spamming
        if self.is_spamming:
            self.spam_loop_job_id = self.root_tk_window.after(
                base_delay_ms,
                lambda skcl=list(spam_key_chars), bdms=base_delay_ms: self._spam_loop(skcl, bdms)
            )
        else:
            self.spam_loop_job_id = None

    def _start_spamming(self):
        """Start the continuous spam loop."""
        if self.is_spamming:
            return  # Already spamming
        
        self.is_spamming = True
        
        # Get spam settings
        spam_key_chars_list = self.active_settings.get("SpamKey", [])
        if not spam_key_chars_list:
            self.is_spamming = False
            return
        
        try:
            base_delay_ms_str = self.active_settings.get("DelayMS")
            base_delay_ms = int(base_delay_ms_str)
        except (ValueError, TypeError):
            base_delay_ms = DEFAULT_DELAY_MS
        
        # Start the spam loop
        self._spam_loop(list(spam_key_chars_list), base_delay_ms)

    def _emergency_stop_spamming(self):
        """Emergency stop spamming - same logic as focus loss."""
        self._stop_spamming()
        self.on_trigger_not_met_callback()

    def _stop_spamming(self):
        """Stop the continuous spam loop."""
        if not self.is_spamming:
            return  # Not spamming

        self.is_spamming = False

        # Cancel the spam loop if it's scheduled
        if self.spam_loop_job_id:
            self.root_tk_window.after_cancel(self.spam_loop_job_id)
            self.spam_loop_job_id = None

    def _check_conditions_loop(self):
        if not self.is_active:
            if self.listener_job_id:
                self.root_tk_window.after_cancel(self.listener_job_id)
                self.listener_job_id = None
            # Stop spamming if active
            if self.is_spamming:
                self._stop_spamming()
            self.on_trigger_not_met_callback()
            return
        
        if not self.dependencies_available:
            self.stop()
            return

        # Use the locked-in settings, not the global config manager
        target_process_name = self.active_settings.get("ProcessName")
        trigger_key_char = self.active_settings.get("TriggerKey")
        
        trigger_vk_code = self.key_mapper.get_vk_code(trigger_key_char)
        
        is_key_pressed = False
        if trigger_vk_code is not None:
            is_key_pressed = self.input_simulator.is_key_down(trigger_vk_code)
        
        is_focused = self.process_monitor.is_target_process_focused(target_process_name)

        # Toggle logic: use the same emergency stop method as focus loss
        if is_focused and is_key_pressed and not self.key_held_down:
            # Key was just pressed - toggle spamming state
            self.key_held_down = True
            if self.is_spamming:
                # Use the same emergency stop as focus loss
                self._emergency_stop_spamming()
            else:
                # Start spamming
                self._start_spamming()
                self.on_trigger_met_callback()
        elif not is_key_pressed and self.key_held_down:
            # Key was just released - reset for next toggle
            self.key_held_down = False
        elif is_focused and self.is_spamming:
            # Keep showing trigger met callback while spamming
            self.on_trigger_met_callback()
        elif not is_focused and self.is_spamming:
            # Stop spamming if process loses focus (emergency stop)
            self._emergency_stop_spamming()
        elif not self.is_spamming:
            self.on_trigger_not_met_callback()

        # Update previous state for next iteration
        self.was_trigger_pressed = is_key_pressed

        if self.is_active:
            self.listener_job_id = self.root_tk_window.after(CHECK_INTERVAL_MS, self._check_conditions_loop)

    def start(self, settings_snapshot):
        if not self.dependencies_available:
            print("SpamController: Cannot start, dependencies not available or not on Windows.")
            return False
            
        if self.is_active:
            return True

        self.active_settings = settings_snapshot # Lock in the settings for this session
        print(f"SpamController started with settings: {self.active_settings}")

        # Reset toggle state
        self.is_spamming = False
        self.was_trigger_pressed = False
        self.key_held_down = False
        if self.spam_loop_job_id:
            self.root_tk_window.after_cancel(self.spam_loop_job_id)
            self.spam_loop_job_id = None

        self.is_active = True
        if self.listener_job_id:
            self.root_tk_window.after_cancel(self.listener_job_id)
        self._check_conditions_loop()
        return True

    def stop(self):
        if not self.is_active:
            return

        # Stop spamming if active (use emergency stop for consistency)
        if self.is_spamming:
            self._emergency_stop_spamming()

        self.is_active = False
        if self.listener_job_id:
            self.root_tk_window.after_cancel(self.listener_job_id)
            self.listener_job_id = None

        # Reset toggle state
        self.is_spamming = False
        self.was_trigger_pressed = False
        self.key_held_down = False
        self.active_settings = {} # Clear locked-in settings on stop
        
    def is_operable(self):
        return self.dependencies_available 