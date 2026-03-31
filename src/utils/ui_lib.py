# ui_lib.py

import tkinter as tk
import threading
import queue

class UILibrary:

    def __init__(self):
        self._commands = queue.Queue()
        self._result = None
        self._ready = threading.Event()

        self._thread = threading.Thread(target=self._ui_loop, daemon=True)
        self._thread.start()
        self._ready.wait()

    def _ui_loop(self):
        self.root = tk.Tk()
        self.root.withdraw()  # Oculta ventana principal
        self._ready.set()
        self._process_queue()
        self.root.mainloop()

    def _process_queue(self):
        while not self._commands.empty():
            func, args = self._commands.get()
            func(*args)

        self.root.after(50, self._process_queue)

    # --------------------------
    # FUNCIONES PÚBLICAS
    # --------------------------

    def mostrar_mensaje(self, texto):
        self._commands.put((self._mostrar_mensaje_ui, (texto,)))

    def mostrar_confirmacion(self, texto):
        self._result = None
        self._commands.put((self._mostrar_confirmacion_ui, (texto,)))

        while self._result is None:
            pass  # espera resultado

        return self._result
    def cerrar_mensaje(self):
        if hasattr(self, "_current_window"):
            self._current_window.after(0, self._current_window.destroy)
    # --------------------------
    # FUNCIONES INTERNAS UI
    # --------------------------

    def _mostrar_mensaje_ui(self, texto):
        win = tk.Toplevel(self.root)
        win.geometry("400x150")
        win.overrideredirect(True)  # Quita barra y botón cerrar

        # Centrar ventana
        win.update_idletasks()
        width = 400
        height = 150
        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()

        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)

        win.geometry(f"{width}x{height}+{x}+{y}")

        # Siempre delante
        win.attributes("-topmost", True)
        win.lift()
        win.focus_force()
        win.grab_set()

        # Contenido
        frame = tk.Frame(win, bd=2, relief="ridge")
        frame.pack(expand=True, fill="both")

        tk.Label(
            frame,
            text=texto,
            font=("Arial", 12),
            wraplength=350
        ).pack(expand=True)

        # Guardamos referencia si quieres cerrarla luego
        self._current_window = win

    def _mostrar_confirmacion_ui(self, texto):
        win = tk.Toplevel(self.root)
        win.title("Confirmación")
        win.geometry("350x150")

        tk.Label(win, text=texto, wraplength=300).pack(pady=20)

        def aceptar():
            self._result = True
            win.destroy()

        def cancelar():
            self._result = False
            win.destroy()

        tk.Button(win, text="Aceptar", command=aceptar).pack(side="left", padx=30, pady=10)
        tk.Button(win, text="Cancelar", command=cancelar).pack(side="right", padx=30, pady=10)