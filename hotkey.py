import os
import signal


def setup_signal_listener(on_triggered):
    pid = os.getpid()
    with open("/tmp/clipqr.pid", "w") as f:
        f.write(str(pid))

    def handle_signal(signum, frame):
        on_triggered()

    signal.signal(signal.SIGUSR1, handle_signal)
    print(f"Listening for SIGUSR1 on PID {pid}")


def on_hotkey_pressed():
    print("Hotkey triggered! Would open history window here.")


if __name__ == "__main__":
    setup_signal_listener(on_hotkey_pressed)
    while True:
        signal.pause()
