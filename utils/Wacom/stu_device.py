# test_load.py
import os
import ctypes

SDK_DIR = os.path.join(os.path.dirname(__file__), "sdk")
os.add_dll_directory(SDK_DIR)

wgss = ctypes.WinDLL(os.path.join(SDK_DIR, "wgssSTU.dll"))

print("✅ Wacom STU SDK cargado correctamente")
