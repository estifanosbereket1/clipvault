import os
import threading

import gi
import uvicorn

from clipboard_monitor import start_monitoring
from history_window import HistoryWindow, open_qr_popup
from hotkey import setup_signal_listener
from qr_server import app as qr_app
from storage import init_db
from tray import setup_tray_icon

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk


def main():
    init_db()
    threading.Thread(target=start_monitoring, daemon=True).start()
    threading.Thread(
        target=uvicorn.run,
        kwargs={
            "app": qr_app,
            "host": "0.0.0.0",
            "port": 8000,
            "ssl_keyfile": "192.168.0.136+2-key.pem",
            "ssl_certfile": "192.168.0.136+2.pem",
        },
        daemon=True,
    ).start()
    history_window = HistoryWindow(on_qr_clicked=open_qr_popup)

    def show_history_window():
        history_window.show_window()

    def on_hotkey_triggered():
        GLib.idle_add(show_history_window)

    setup_signal_listener(on_hotkey_triggered)

    def quit_app():
        pid_file = "/tmp/clipqr.pid"
        if os.path.exists(pid_file):
            os.remove(pid_file)
        Gtk.main_quit()

    indicator = setup_tray_icon(on_open=show_history_window, on_quit=quit_app)

    Gtk.main()


if __name__ == "__main__":
    main()
