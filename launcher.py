import threading
import webbrowser
import tkinter as tk
from tkinter import messagebox

from werkzeug.serving import make_server

from app import app


HOST = "127.0.0.1"
PORT = 8780
URL = f"http://{HOST}:{PORT}"


class ServerThread(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.server = make_server(HOST, PORT, app)

    def run(self):
        self.server.serve_forever()

    def stop(self):
        self.server.shutdown()


class Launcher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("WORKOUT Generator")
        self.root.geometry("460x230")
        self.root.resizable(False, False)

        self.server_thread = None

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _build_ui(self):
        container = tk.Frame(self.root, padx=28, pady=24)
        container.pack(fill="both", expand=True)

        title = tk.Label(
            container,
            text="WORKOUT Generator",
            font=("Segoe UI", 18, "bold"),
        )
        title.pack(anchor="w")

        subtitle = tk.Label(
            container,
            text=(
                "Il generatore gira solo sul tuo PC.\n"
                "La GUI viene aperta nel browser predefinito."
            ),
            justify="left",
            font=("Segoe UI", 10),
        )
        subtitle.pack(anchor="w", pady=(8, 18))

        self.status = tk.Label(
            container,
            text="Avvio in corso...",
            font=("Segoe UI", 10, "bold"),
        )
        self.status.pack(anchor="w", pady=(0, 14))

        buttons = tk.Frame(container)
        buttons.pack(fill="x")

        open_button = tk.Button(
            buttons,
            text="Apri WORKOUT Generator",
            command=self.open_browser,
            padx=14,
            pady=8,
        )
        open_button.pack(side="left")

        close_button = tk.Button(
            buttons,
            text="Chiudi",
            command=self.close,
            padx=14,
            pady=8,
        )
        close_button.pack(side="right")

    def start_server(self):
        try:
            self.server_thread = ServerThread()
            self.server_thread.start()
        except OSError as exc:
            messagebox.showerror(
                "Impossibile avviare",
                (
                    f"Non riesco ad avviare il server locale sulla porta {PORT}.\n\n"
                    "È possibile che WORKOUT Generator sia già aperto.\n\n"
                    f"Dettaglio: {exc}"
                ),
            )
            self.root.destroy()
            return

        self.status.config(text=f"Attivo su {URL}")
        self.root.after(500, self.open_browser)

    def open_browser(self):
        webbrowser.open(URL)

    def close(self):
        if self.server_thread is not None:
            try:
                self.server_thread.stop()
                self.server_thread.join(timeout=2)
            except Exception:
                pass

        self.root.destroy()

    def run(self):
        self.root.after(100, self.start_server)
        self.root.mainloop()


if __name__ == "__main__":
    Launcher().run()
