import time

import pyperclip

from storage import add_entry


def start_monitoring(poll_interval=1.0):
    last_seen = pyperclip.paste()
    while True:
        time.sleep(poll_interval)
        try:
            current_value = pyperclip.paste()
            if last_seen != current_value:
                add_entry(current_value)
                last_seen = current_value
        except pyperclip.PyperclipException as e:
            print(f"Clipboard read failed: {e}")
