import platform

if platform.system() == "Windows":
    try:
        import win32api
        import win32con
    except ImportError:
        print("ERROR: InputSimulator requires pywin32. Please install it.")
        win32api = win32con = None
else:
    win32api = win32con = None

class InputSimulator:
    def __init__(self):
        self.dependencies_available = bool(win32api and win32con) and platform.system() == "Windows"
        if not self.dependencies_available:
            if platform.system() == "Windows":
                print("InputSimulator: win32api/win32con not found. Input simulation will not function.")
            else:
                print("InputSimulator: Not running on Windows. Input simulation will not function.")

    def send_key_press_release(self, vk_code):
        if not self.dependencies_available or vk_code is None:
            return False
        try:
            win32api.keybd_event(vk_code, 0, 0, 0)
            win32api.keybd_event(vk_code, 0, win32con.KEYEVENTF_KEYUP, 0)
            return True
        except Exception as e:
            print(f"InputSimulator Error sending keystroke for VK '{hex(vk_code) if vk_code else None}': {e}")
            return False
    
    def is_key_down(self, vk_code):
        if not self.dependencies_available or vk_code is None:
            return False
        return bool(win32api.GetAsyncKeyState(vk_code) & 0x8000)

    def is_operable(self):
        return self.dependencies_available

if __name__ == '__main__':
    if platform.system() == "Windows" and win32api and win32con:
        simulator = InputSimulator()
        if simulator.is_operable():
            from src.core.key_mapper import KeyMapper
            key_mapper = KeyMapper()
            if key_mapper.is_operable():
                print("InputSimulator is operable. Testing key press for 'A' in 3 seconds...")
                print("Please focus a text input field.")
                import time
                time.sleep(3)
                
                vk_a = key_mapper.get_vk_code('A')
                if vk_a:
                    success = simulator.send_key_press_release(vk_a)
                    print(f"Sent 'A' key press: {'Success' if success else 'Failed'}")
                else:
                    print("Could not get VK code for 'A' to test simulator.")

                print("Testing IsKeyDown for Left Shift (hold it down in the next 5s)")
                vk_lshift = key_mapper.get_vk_code('LSHIFT')
                if vk_lshift:
                    for i in range(5):
                        if simulator.is_key_down(vk_lshift):
                            print(f"Left Shift IS down! ({i+1}s)")
                        else:
                            print(f"Left Shift is NOT down. ({i+1}s)")
                        time.sleep(1)
                else:
                    print("Could not get VK code for LSHIFT to test IsKeyDown.")
            else:
                print("KeyMapper not operable, cannot fully test InputSimulator.")
    else:
        print("InputSimulator example skipped (not on Windows or pywin32 missing).") 