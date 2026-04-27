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

    def mostrar_mensaje_con_x(self, texto):
        self._commands.put((self._mostrar_mensaje_con_x_ui, (texto,)))

    # --------------------------
    # FUNCIONES INTERNAS UI
    # --------------------------

    def _mostrar_mensaje_ui(self, texto):
        win = tk.Toplevel(self.root)

        width = 400
        height = 150

        # Primero definimos tamaño
        win.geometry(f"{width}x{height}")

        # Necesario para que Tk calcule medidas reales
        win.update_idletasks()

        # Obtener tamaño de pantalla
        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()

        # Calcular centro
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)

        # Aplicar posición final
        win.geometry(f"{width}x{height}+{x}+{y}")

        # Ahora sí: quitar bordes
        win.overrideredirect(True)

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
            font=("Arial", 14, "bold"),
            wraplength=350
        ).pack(expand=True)

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

    def _mostrar_mensaje_con_x_ui(self, texto):
        win = tk.Toplevel(self.root)

        width = 400
        height = 150

        # Tamaño inicial
        win.geometry(f"{width}x{height}")
        win.update_idletasks()

        # Centrado
        screen_width = win.winfo_screenwidth()
        screen_height = win.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        win.geometry(f"{width}x{height}+{x}+{y}")

        # Quitar bordes
        win.overrideredirect(True)

        # Siempre delante
        win.attributes("-topmost", True)
        win.lift()
        win.focus_force()
        win.grab_set()

        # --------------------------
        # Barra superior personalizada
        # --------------------------
        top_bar = tk.Frame(win, bg="#333333", height=30)
        top_bar.pack(fill="x", side="top")

        # Botón X
        close_btn = tk.Button(
            top_bar,
            text="✕",
            font=("Arial", 12, "bold"),
            fg="white",
            bg="#333333",
            bd=0,
            activebackground="#555555",
            command=win.destroy
        )
        close_btn.pack(side="right", padx=5)

        # --------------------------
        # Contenido del mensaje
        # --------------------------
        frame = tk.Frame(win, bd=2, relief="ridge")
        frame.pack(expand=True, fill="both")

        tk.Label(
            frame,
            text=texto,
            font=("Arial", 14, "bold"),
            wraplength=350
        ).pack(expand=True)

        self._current_window = win
