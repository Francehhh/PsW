import threading
import time
import sys
from PySide6.QtCore import QObject, Signal
import psutil
from src.utils.sync_manager import SyncManager

# --- Platform Specific Imports --- 
IS_WINDOWS = sys.platform == 'win32'

if IS_WINDOWS:
    try:
        import win32api
        import win32gui
        import win32con
        import win32process
        PYWIN32_AVAILABLE = True
    except ImportError:
        print("[HotkeyListener] WARNING: pywin32 not installed. Windows hotkey/window detection will not work.")
        PYWIN32_AVAILABLE = False
else:
    PYWIN32_AVAILABLE = False
    # TODO: Implement fallback using pynput/other libs for non-Windows?
    print("[HotkeyListener] WARNING: Non-Windows platform. Global hotkey functionality not implemented.")

# --- Constants & SyncManager ---
HOTKEY_ID = 1 # Arbitrary ID for our hotkey
sync_manager = SyncManager() # Instantiate SyncManager (assuming shared instance)

# --- Hotkey ID and Modifiers --- 
# Modifiers for RegisterHotKey (Windows)
# MOD_ALT | MOD_CONTROL | MOD_SHIFT | MOD_WIN
DEFAULT_MODIFIERS = win32con.MOD_ALT | win32con.MOD_CONTROL if PYWIN32_AVAILABLE else 0 # Default: Ctrl+Alt
# DEFAULT_MODIFIERS = 0 if PYWIN32_AVAILABLE else 0 # Try NO modifiers
DEFAULT_VK_CODE = 0x50 if PYWIN32_AVAILABLE else 0 # Virtual-Key code for 'P'
# DEFAULT_VK_CODE = win32con.VK_F9 if PYWIN32_AVAILABLE else 0 # Try F9 key

# --- Signal Emitter --- 
class HotkeySignalEmitter(QObject):
    hotkey_pressed = Signal(str, str) # Emette: nome_processo, titolo_finestra

signal_emitter = HotkeySignalEmitter()

# --- Listener Logic (Windows Specific) --- 
running = True
# Global hotkey variables - will be loaded from SyncManager in start()
hotkey_modifiers = 0
hotkey_vk_code = 0
listener_thread_id = None

def get_active_window_info_windows():
    """Ottiene informazioni sulla finestra attiva usando pywin32."""
    if not PYWIN32_AVAILABLE:
        return "Unknown", "Unknown (pywin32 unavailable)"
    try:
        hwnd = win32gui.GetForegroundWindow()
        if hwnd:
            window_title = win32gui.GetWindowText(hwnd)
            
            # Get process ID from window handle
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            process_name = "Unknown"
            try:
                process = psutil.Process(pid)
                process_name = process.name()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass # Fallback to Unknown if process info fails
                
            return process_name, window_title
    except Exception as e:
        print(f"[HotkeyListener] Errore get_active_window_info_windows: {e}")
    return "Unknown", "Unknown"

def listener_thread_func():
    global running, listener_thread_id
    listener_thread_id = threading.get_ident() # Store thread ID
    print(f"[HotkeyListener] Starting Windows message loop thread (ID: {listener_thread_id})...")
    
    # Hotkey values are now loaded in start() before this thread begins
    print(f"[HotkeyListener] Attempting to register hotkey (ID: {HOTKEY_ID}, Mod: {hotkey_modifiers}, VK: {hex(hotkey_vk_code)}) from loaded settings...")
    
    # Register the hotkey
    registered_ok = False
    try:
        if win32gui.RegisterHotKey(None, HOTKEY_ID, hotkey_modifiers, hotkey_vk_code):
            print(f"[HotkeyListener] Hotkey registered successfully.")
            registered_ok = True
        else:
            last_error = win32api.GetLastError()
            error_message = win32api.FormatMessage(last_error)
            print(f"[HotkeyListener] ERROR: Failed to register hotkey (ID: {HOTKEY_ID}). Error code: {last_error} - {error_message.strip()}")
            # Updated suggestion message
            print(f"[HotkeyListener] SUGGESTION: The configured hotkey (Modifiers: {hotkey_modifiers}, Key: {hex(hotkey_vk_code)}) might be already in use by another application or the system. Please configure a different hotkey in the application settings.")
            if listener_thread_id: # Check if thread ID was set before trying to post message
                win32api.PostThreadMessage(listener_thread_id, win32con.WM_QUIT, 0, 0) # Signal thread to exit
    except Exception as e:
         print(f"[HotkeyListener] EXCEPTION registering hotkey: {e}")
         if listener_thread_id: # Check if thread ID was set
             win32api.PostThreadMessage(listener_thread_id, win32con.WM_QUIT, 0, 0)

    # Start the message loop only if registration was successful
    if registered_ok:
        try:
            msg = win32gui.GetMessage(None, 0, 0)
            while running and msg:
                if msg[1] == win32con.WM_HOTKEY and msg[2] == HOTKEY_ID:
                    print(f"[HotkeyListener] Windows Hotkey (ID: {HOTKEY_ID}) detected!")
                    process_name, window_title = get_active_window_info_windows()
                    print(f"[HotkeyListener] Active Window: Process='{process_name}', Title='{window_title}'")
                    signal_emitter.hotkey_pressed.emit(process_name, window_title)
                
                # Needed for other messages if the loop becomes more complex
                # win32gui.TranslateMessage(msg)
                # win32gui.DispatchMessage(msg)
                
                # Get next message
                msg = win32gui.GetMessage(None, 0, 0)
            
        except Exception as e:
            print(f"[HotkeyListener] Error in message loop: {e}")
        finally:
            print("[HotkeyListener] Unregistering hotkey...")
            try:
                win32gui.UnregisterHotKey(None, HOTKEY_ID)
            except Exception as e:
                print(f"[HotkeyListener] Error unregistering hotkey: {e}")
    print("[HotkeyListener] Windows message loop thread finished.")

listener_thread = None

def start():
    global listener_thread, running, hotkey_modifiers, hotkey_vk_code
    if not IS_WINDOWS or not PYWIN32_AVAILABLE:
        print("[HotkeyListener] Cannot start listener: Not on Windows or pywin32 unavailable.")
        return
        
    if listener_thread is None or not listener_thread.is_alive():
        # Load hotkey configuration from SyncManager before starting
        try:
            config = sync_manager.get_hotkey_config()
            hotkey_modifiers = config.get('modifiers', 0) # Provide default if key missing
            hotkey_vk_code = config.get('vk_code', 0)
            print(f"[HotkeyListener] Loaded hotkey config: Mod={hotkey_modifiers}, VK={hex(hotkey_vk_code)}")
            
            # Check if a valid hotkey is configured (both must be non-zero)
            if hotkey_modifiers == 0 or hotkey_vk_code == 0:
                 print("[HotkeyListener] WARNING: No valid hotkey configured (modifiers or vk_code is 0). Listener will not start.")
                 # Do not proceed to start the listener thread if hotkey is invalid
                 return 

        except Exception as e:
             print(f"[HotkeyListener] ERROR loading hotkey config: {e}. Listener will not start.")
             # Ensure fallback defaults are set, but still return
             hotkey_modifiers = 0 
             hotkey_vk_code = 0
             return # Do not start listener after error

        # Proceed only if config loaded and is valid
        running = True
        listener_thread = threading.Thread(target=listener_thread_func, daemon=True)
        listener_thread.start()

def stop():
    global running, listener_thread_id
    if not IS_WINDOWS or not PYWIN32_AVAILABLE:
        return
        
    print("[HotkeyListener] Stopping listener thread...")
    running = False
    # Post a WM_QUIT message to the listener thread's message queue
    if listener_thread_id:
        try:
            win32api.PostThreadMessage(listener_thread_id, win32con.WM_QUIT, 0, 0)
        except Exception as e:
             print(f"[HotkeyListener] Error posting WM_QUIT: {e}")
             
    if listener_thread and listener_thread.is_alive():
        listener_thread.join(timeout=1) 
    listener_thread_id = None # Reset thread ID
    print("[HotkeyListener] Stop sequence complete.")

# --- Funzione per aggiornare l'hotkey (da chiamare dalle impostazioni) ---
def update_hotkey_combination(config_str: str, modifiers: int, vk_code: int):
    global hotkey_modifiers, hotkey_vk_code # Keep these globals for the listener thread
    if not IS_WINDOWS or not PYWIN32_AVAILABLE:
        print("[HotkeyListener] Cannot update hotkey: Not on Windows or pywin32 unavailable.")
        return
        
    print(f"[HotkeyListener] Attempting to update hotkey to: Str='{config_str}', Mod={modifiers}, VK={vk_code}")

    # 1. Save the new configuration using SyncManager (now includes config_str)
    try:
        # Pass all three parameters to the updated set_hotkey_config
        sync_manager.set_hotkey_config(config_str, modifiers, vk_code)
        print("[HotkeyListener] New hotkey configuration saved via SyncManager.")
    except Exception as e:
        print(f"[HotkeyListener] ERROR saving new hotkey configuration via SyncManager: {e}")
        # Decide if we should proceed without saving or return? For now, proceed, but log error.

    # 2. Stop the current listener
    stop()
    time.sleep(0.2) # Give time for thread to potentially stop

    # 3. Update global variables for the listener thread (will be re-read by start, but good practice)
    hotkey_modifiers = modifiers
    hotkey_vk_code = vk_code

    # 4. Start listener with new keys (which will reload from the saved config via SyncManager)
    start()

# --- Test Locale --- 
if __name__ == '__main__':
    if not IS_WINDOWS or not PYWIN32_AVAILABLE:
        print("Questo test richiede Windows e pywin32.")
        sys.exit(1)
        
    # Load initial config for the test message
    # This might run before main app initializes SyncManager properly,
    # so we load directly here for the print statement.
    # In a real app, start() would handle the loading.
    initial_config = sync_manager.get_hotkey_config()
    initial_mod = initial_config.get('modifiers', 'N/A')
    initial_vk = initial_config.get('vk_code', 'N/A')
    print(f"Avvio listener hotkey Windows in modalità test (Hotkey from settings: Mod={initial_mod}, VK={hex(initial_vk) if isinstance(initial_vk, int) else initial_vk})")
    print("(Premi l'hotkey configurato per testare, Ctrl+C nel terminale per uscire)")
    
    def test_signal(proc, title):
        print(f"---> SEGNALE RICEVUTO: Proc='{proc}', Title='{title}'")
    
    signal_emitter.hotkey_pressed.connect(test_signal)
    start()
    
    try:
        # Mantieni il thread principale attivo per permettere al listener di funzionare
        # In un'app Qt, questo ruolo è svolto dal loop di eventi Qt
        while True:
            time.sleep(10) # Dormi a lungo, il lavoro è nel thread listener
    except KeyboardInterrupt:
        stop()
    
    print("Test terminato.") 