import platform

if platform.system() == "Windows":
    try:
        import win32api
    except ImportError:
        print("ERROR: KeyMapper requires pywin32. Please install it.")
        win32api = None
else:
    win32api = None

class KeyMapper:
    def __init__(self):
        self.dependencies_available = bool(win32api) and platform.system() == "Windows"
        if not self.dependencies_available:
            if platform.system() == "Windows":
                print("KeyMapper: win32api not found. Key mapping will not function.")
            else:
                print("KeyMapper: Not running on Windows. Key mapping will not function.")

    def get_vk_code(self, key_char):
        if not self.dependencies_available: 
            return None

        if len(key_char) == 1 and key_char.isalnum():
            vk_scan_result = win32api.VkKeyScan(key_char[0]) 
            if vk_scan_result == -1: 
                return None
            return vk_scan_result & 0xFF
        
        try: 
            return int(key_char)
        except ValueError:
            pass
        
        key_char_upper = key_char.upper()
        named_keys = {
            "F1": 0x70, "F2": 0x71, "F3": 0x72, "F4": 0x73, "F5": 0x74, "F6": 0x75,
            "F7": 0x76, "F8": 0x77, "F9": 0x78, "F10": 0x79, "F11": 0x7A, "F12": 0x7B,
            "ENTER": 0x0D, "ESC": 0x1B, "ESCAPE": 0x1B, 
            "SHIFT": 0x10, "LSHIFT": 0xA0, "RSHIFT": 0xA1,
            "CTRL": 0x11, "LCTRL": 0xA2, "RCTRL": 0xA3,
            "ALT": 0x12, "LALT": 0xA4, "RALT": 0xA5,
            "SPACE": 0x20, "SPACEBAR": 0x20, "TAB": 0x09, "CAPSLOCK": 0x14,
            "LEFT": 0x25, "UP": 0x26, "RIGHT": 0x27, "DOWN": 0x28,
            "INSERT": 0x2D, "DELETE": 0x2E, "HOME": 0x24, "END": 0x23, 
            "PAGEUP": 0x21, "PAGEDOWN": 0x22,
            "NUMLOCK": 0x90, "SCROLLLOCK": 0x91,
            "0": 0x30, "1": 0x31, "2": 0x32, "3": 0x33, "4": 0x34,
            "5": 0x35, "6": 0x36, "7": 0x37, "8": 0x38, "9": 0x39,
        }
        if key_char_upper in named_keys:
            return named_keys[key_char_upper]

        if len(key_char) == 1:
            vk_scan_result = win32api.VkKeyScan(key_char[0])
            if vk_scan_result != -1:
                return vk_scan_result & 0xFF

        return None

    def is_operable(self):
        return self.dependencies_available

if __name__ == '__main__':
    if platform.system() == "Windows" and win32api:
        mapper = KeyMapper()
        if mapper.is_operable():
            print(f"VK for 'a': {hex(mapper.get_vk_code('a')) if mapper.get_vk_code('a') else None}")
            print(f"VK for 'A': {hex(mapper.get_vk_code('A')) if mapper.get_vk_code('A') else None}")
            print(f"VK for '2': {hex(mapper.get_vk_code('2')) if mapper.get_vk_code('2') else None}")
            print(f"VK for 'F1': {hex(mapper.get_vk_code('F1')) if mapper.get_vk_code('F1') else None}")
            print(f"VK for 'Enter': {hex(mapper.get_vk_code('Enter')) if mapper.get_vk_code('Enter') else None}")
            print(f"VK for 'SHIFT': {hex(mapper.get_vk_code('SHIFT')) if mapper.get_vk_code('SHIFT') else None}")
            print(f"VK for 'unknown': {mapper.get_vk_code('unknown')}")
            print(f"VK for ';': {hex(mapper.get_vk_code(';')) if mapper.get_vk_code(';') else None}")
            print(f"VK for '[': {hex(mapper.get_vk_code('[')) if mapper.get_vk_code('[') else None}")
            print(f"VK for '100': {hex(mapper.get_vk_code('100')) if mapper.get_vk_code('100') else None}")
    else:
        print("KeyMapper example skipped (not on Windows or pywin32 missing).") 