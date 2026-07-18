# import time

# import pyperclip

# from storage import add_entry


# def start_monitoring(poll_interval=1.0, on_change=None):
#     last_seen = pyperclip.paste()
#     while True:
#         time.sleep(poll_interval)
#         try:
#             current_value = pyperclip.paste()
#             if last_seen != current_value:
#                 inserted = add_entry(content=current_value)
#                 last_seen = current_value
#                 if inserted and on_change:
#                     on_change()
#         except pyperclip.PyperclipException as e:
#             print(f"Clipboard read failed: {e}")

import time
import pyperclip
from storage import add_entry, add_image_entry
from image_clipboard import get_clipboard_image_bytes


def start_monitoring(poll_interval=1.0, on_change=None):
    last_seen_text = pyperclip.paste()
    last_seen_image_bytes = get_clipboard_image_bytes()

    while True:
        time.sleep(poll_interval)
        try:
            current_image_bytes = get_clipboard_image_bytes()

            if current_image_bytes is not None:
                if current_image_bytes != last_seen_image_bytes:
                    inserted = add_image_entry(current_image_bytes)
                    last_seen_image_bytes = current_image_bytes
                    if inserted and on_change:
                        on_change()
                # Either way, an image is present this cycle -- don't also
                # process whatever text value the clipboard happens to hold
                # (e.g. the file path string alongside a copied image file).
                continue

            last_seen_image_bytes = None

            current_text = pyperclip.paste()
            if current_text != last_seen_text:
                inserted = add_entry(content=current_text)
                last_seen_text = current_text
                if inserted and on_change:
                    on_change()

        except pyperclip.PyperclipException as e:
            print(f"Clipboard read failed: {e}")
