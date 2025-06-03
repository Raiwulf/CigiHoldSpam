import platform
import random

# Attempt to import Windows-specific modules
if platform.system() == "Windows":
    try:
        import win32gui
        import win32api
        import win32process
        import win32con  # For keyboard event constants
        import psutil    # For more robust process name fetching
    except ImportError:
        print("ERROR: OSListener requires pywin32 and psutil. Please install them.")
        win32gui = win32api = win32process = win32con = psutil = None
else:
    win32gui = win32api = win32process = win32con = psutil = None

CHECK_INTERVAL_MS = 100
DEFAULT_DELAY_MS = 100  # Default if config value is invalid

class OSListener:
    def __init__(self, config_manager, root_tk_window, on_trigger_met_callback, on_trigger_not_met_callback):
        self.config_manager = config_manager
        self.root_tk_window = root_tk_window # For self.after()
        self.on_trigger_met_callback = on_trigger_met_callback
        self.on_trigger_not_met_callback = on_trigger_not_met_callback

        self.is_active = False
        self.listener_job_id = None
        self.dependencies_available = bool(win32gui and win32api and win32process and win32con and psutil)

        if not self.dependencies_available and platform.system() == "Windows":
            print("OSListener: Windows-specific dependencies not found. Listener will not function.")
        elif platform.system() != "Windows":
            print("OSListener: Not running on Windows. Listener will not function.")


    def _get_vk_code(self, key_char):
        if not self.dependencies_available: return None
        
        if len(key_char) == 1 and key_char.isalnum():
            vk_scan_result = win32api.VkKeyScan(key_char[0])
            if vk_scan_result == -1: return None
            return vk_scan_result & 0xFF
        
        try:
            return int(key_char)
        except ValueError:
            pass
        
        key_char_upper = key_char.upper()
        # Add common named keys
        named_keys = {
            "F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73, "F5": 0x74, "F6": 0x75,
            "F7": 0x76, "F8": 0x77, "F9": 0x78, "F10": 0x79, "F11": 0x7A, "F12": 0x7B,
            "ENTER": 0x0D, "ESC": 0x1B, "SHIFT": 0x10, "CTRL": 0x11, "ALT": 0x12,
            "SPACE": 0x20, "TAB": 0x09, "CAPSLOCK": 0x14,
            "LEFT": 0x25, "UP": 0x26, "RIGHT": 0x27, "DOWN": 0x28,
            "INSERT": 0x2D, "DELETE": 0x2E, "HOME": 0x24, "END": 0x23, 
            "PAGEUP": 0x21, "PAGEDOWN": 0x22,
        }
        if key_char_upper in named_keys:
            return named_keys[key_char_upper]

        # For keys like '2', VkKeyScan should handle it. If not, this would be a fallback.
        # However, VkKeyScan is generally preferred.
        # e.g. if key_char == "2": return 0x32 # VK_KEY_2
            
        print(f"OSListener Warning: Could not map key_char '{key_char}' to a VK code.")
        return None

    def _get_process_name_from_hwnd(self, hwnd):
        if not self.dependencies_available: return None
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            return process.name()
        except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
            return None

    def _send_key_action(self, spam_vk_code, spam_key_char):
        if not self.is_active: # Re-check if active, might have been stopped during delay
            return
        if not self.dependencies_available:
            return

        try:
            win32api.keybd_event(spam_vk_code, 0, 0, 0)
            win32api.keybd_event(spam_vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
            # print(f"OSListener: Sent (delayed) keystroke: {spam_key_char} (VK: {hex(spam_vk_code)})")
        except Exception as e:
            print(f"OSListener Error sending (delayed) keystroke for '{spam_key_char}': {e}")

    def _check_conditions_loop(self):
        if not self.is_active:
            if self.listener_job_id:
                self.root_tk_window.after_cancel(self.listener_job_id)
                self.listener_job_id = None
            self.on_trigger_not_met_callback() # Ensure UI is reset
            return

        if not self.dependencies_available:
             # Stop loop if dependencies somehow became unavailable after start
            self.stop()
            return

        target_process_name_config = self.config_manager.get_setting("Settings", "ProcessName")
        trigger_key_char = self.config_manager.get_setting("Settings", "TriggerKey")
        trigger_vk_code = self._get_vk_code(trigger_key_char)

        is_focused = False
        is_key_pressed = False

        if trigger_vk_code is not None:
            if win32api.GetAsyncKeyState(trigger_vk_code) & 0x8000:
                is_key_pressed = True
        
        current_focused_hwnd = win32gui.GetForegroundWindow()
        if current_focused_hwnd:
            focused_process_name = self._get_process_name_from_hwnd(current_focused_hwnd)
            if focused_process_name and target_process_name_config and \
               focused_process_name.lower() == target_process_name_config.lower():
                is_focused = True

        if is_focused and is_key_pressed:
            self.on_trigger_met_callback()
            
            spam_key_char = self.config_manager.get_setting("Settings", "SpamKey")
            spam_vk_code = self._get_vk_code(spam_key_char)
            
            if spam_vk_code is not None:
                try:
                    base_delay_ms_str = self.config_manager.get_setting("Settings", "DelayMS")
                    base_delay_ms = int(base_delay_ms_str)
                except ValueError:
                    print(f"OSListener Warning: Invalid DelayMS '{base_delay_ms_str}'. Defaulting to {DEFAULT_DELAY_MS}ms.")
                    base_delay_ms = DEFAULT_DELAY_MS
                
                jitter_ms = random.randint(-4, 4)
                actual_delay_ms = max(0, base_delay_ms + jitter_ms)
                
                self.root_tk_window.after(actual_delay_ms, 
                                          lambda svk=spam_vk_code, skc=spam_key_char: \
                                          self._send_key_action(svk, skc))
            else:
                print(f"OSListener: Could not schedule SpamKey: Unknown VK code for '{spam_key_char}'.")
        else:
            self.on_trigger_not_met_callback()

        if self.is_active: # Reschedule if still active
            self.listener_job_id = self.root_tk_window.after(CHECK_INTERVAL_MS, self._check_conditions_loop)

    def start(self):
        if not self.dependencies_available:
            print("OSListener: Cannot start, dependencies not available.")
            return False # Indicate failure to start
            
        if self.is_active:
            return True # Already active

        self.is_active = True
        print("OSListener: Activated.")
        if self.listener_job_id: # Should not happen if is_active was false, but defensive
            self.root_tk_window.after_cancel(self.listener_job_id)
        self._check_conditions_loop() # Start the loop
        return True # Indicate success

    def stop(self):
        if not self.is_active:
            return

        self.is_active = False
        print("OSListener: Deactivated.")
        if self.listener_job_id:
            self.root_tk_window.after_cancel(self.listener_job_id)
            self.listener_job_id = None
        self.on_trigger_not_met_callback() # Ensure UI is reset when explicitly stopped
        
    def is_operable(self):
        """Checks if the listener can operate (OS is Windows and dependencies are loaded)."""
        return platform.system() == "Windows" and self.dependencies_available 