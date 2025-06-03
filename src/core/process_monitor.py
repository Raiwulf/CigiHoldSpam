import platform

if platform.system() == "Windows":
    try:
        import win32gui
        import win32process
        import psutil
    except ImportError:
        print("ERROR: ProcessMonitor requires pywin32 and psutil. Please install them.")
        win32gui = win32process = psutil = None
else:
    win32gui = win32process = psutil = None

class ProcessMonitor:
    def __init__(self):
        self.dependencies_available = bool(win32gui and win32process and psutil) and platform.system() == "Windows"
        if not self.dependencies_available:
            if platform.system() == "Windows":
                print("ProcessMonitor: Dependencies (pywin32, psutil) not found. Process monitoring will not function.")
            else:
                print("ProcessMonitor: Not running on Windows. Process monitoring will not function.")

    def _get_process_name_from_hwnd(self, hwnd):
        if not self.dependencies_available: return None
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            return process.name()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess, Exception):
            return None

    def is_target_process_focused(self, target_process_name):
        if not self.dependencies_available or not target_process_name:
            return False
        
        try:
            current_focused_hwnd = win32gui.GetForegroundWindow()
            if current_focused_hwnd:
                focused_process_name = self._get_process_name_from_hwnd(current_focused_hwnd)
                if focused_process_name and focused_process_name.lower() == target_process_name.lower():
                    return True
        except Exception as e:
            pass
        return False

    def is_operable(self):
        return self.dependencies_available

if __name__ == '__main__':
    if platform.system() == "Windows" and psutil and win32gui and win32process:
        monitor = ProcessMonitor()
        if monitor.is_operable():
            import time
            print("Checking for Notepad focus for 10 seconds...")
            for i in range(10):
                if monitor.is_target_process_focused("notepad.exe"):
                    print(f"Notepad.exe IS focused! ({i+1}s)")
                else:
                    print(f"Notepad.exe is NOT focused. ({i+1}s)")
                time.sleep(1)
            print("Done testing Notepad focus.")
            
            print(f"Is 'nonexistentprocess123.exe' focused? {monitor.is_target_process_focused('nonexistentprocess123.exe')}")
    else:
        print("ProcessMonitor example skipped (not on Windows or dependencies missing).") 