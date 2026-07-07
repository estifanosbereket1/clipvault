import gi

gi.require_version("Gio", "2.0")
from gi.repository import Gio

MEDIA_KEYS_SCHEMA = "org.gnome.settings-daemon.plugins.media-keys"
CUSTOM_KEYBINDING_SCHEMA = (
    "org.gnome.settings-daemon.plugins.media-keys.custom-keybinding"
)
CUSTOM_KEYBINDING_BASE_PATH = (
    "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/"
)


def _get_media_keys_settings():
    return Gio.Settings.new(MEDIA_KEYS_SCHEMA)


def _next_free_custom_path():
    """
    Finds the next unused customN path (custom0, custom1, ...) so we don't
    collide with existing custom shortcuts the user may have made manually.
    """
    settings = _get_media_keys_settings()
    existing_paths = settings.get_strv("custom-keybindings")

    n = 0
    while True:
        candidate = f"{CUSTOM_KEYBINDING_BASE_PATH}custom{n}/"
        if candidate not in existing_paths:
            return candidate
        n += 1


def register_custom_shortcut(name: str, shell_command: str, accelerator: str) -> str:
    """
    Registers a new GNOME custom keyboard shortcut.

    name: display name shown in Settings -> Keyboard -> Custom Shortcuts
    shell_command: the raw command to run, e.g. "kill -SIGUSR1 $(cat /tmp/clipqr.pid)"
                    (this function wraps it in `bash -c` automatically, since GNOME
                    does not run custom shortcut commands through a shell itself)
    accelerator: GTK accelerator string, e.g. "<Control><Alt>v"

    Returns the dconf path this shortcut was registered under, in case you need
    to unregister it later.
    """
    path = _next_free_custom_path()

    binding_settings = Gio.Settings.new_with_path(CUSTOM_KEYBINDING_SCHEMA, path)
    binding_settings.set_string("name", name)
    binding_settings.set_string("command", f'bash -c "{shell_command}"')
    binding_settings.set_string("binding", accelerator)

    media_keys_settings = _get_media_keys_settings()
    existing_paths = media_keys_settings.get_strv("custom-keybindings")
    media_keys_settings.set_strv("custom-keybindings", existing_paths + [path])

    return path


def unregister_custom_shortcut(path: str):
    """
    Removes a previously registered custom shortcut by its dconf path
    (the value returned from register_custom_shortcut).
    """
    media_keys_settings = _get_media_keys_settings()
    existing_paths = media_keys_settings.get_strv("custom-keybindings")

    if path in existing_paths:
        existing_paths.remove(path)
        media_keys_settings.set_strv("custom-keybindings", existing_paths)


def get_all_keybindings():
    """
    Returns a list of (accelerator, description) for shortcuts we can see:
      - all registered custom keybindings (ours and any the user made manually)
      - window manager keybindings (org.gnome.desktop.wm.keybindings)

    NOTE: this does not see every possible shortcut on the system (some apps
    manage their own global hotkeys outside gsettings entirely), but it covers
    GNOME's own custom shortcuts and window manager bindings, which is the
    most common source of real conflicts.
    """
    results = []

    # Custom keybindings
    media_keys_settings = _get_media_keys_settings()
    for path in media_keys_settings.get_strv("custom-keybindings"):
        binding_settings = Gio.Settings.new_with_path(CUSTOM_KEYBINDING_SCHEMA, path)
        accel = binding_settings.get_string("binding")
        name = binding_settings.get_string("name")
        if accel:
            results.append((accel, f"Custom shortcut: {name}"))

    # Window manager keybindings (e.g. switch workspace, close window, etc.)
    wm_settings = Gio.Settings.new("org.gnome.desktop.wm.keybindings")
    for key in wm_settings.list_keys():
        try:
            accels = wm_settings.get_strv(key)
        except Exception:
            continue
        for accel in accels:
            if accel:
                results.append((accel, f"Window manager: {key}"))

    return results


def is_combo_taken(accelerator: str) -> str | None:
    """
    Checks whether the given accelerator string is already bound to something.
    Returns the description of the conflicting binding if taken, otherwise None.
    """
    for existing_accel, description in get_all_keybindings():
        if existing_accel == accelerator:
            return description
    return None


def _standalone_test():
    print("Current known keybindings:")
    for accel, desc in get_all_keybindings():
        print(f"  {accel!r:20} -> {desc}")

    test_accel = "<Control><Alt>v"
    conflict = is_combo_taken(test_accel)
    print(f"\nIs {test_accel!r} taken? {conflict or 'No'}")


if __name__ == "__main__":
    _standalone_test()
