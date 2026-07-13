import json
import os
import socket
from pathlib import Path

DEFAULTS = {
    "history_limit": 50,
    "poll_interval": 1.0,
    "port": 8000,
    "last_known_ip": None,
    "playback_mode": "time",
    # "palette": "midnight",
    "dark_palette": "midnight",
    "light_palette": "daylight",
    "onboarded": False
}

# Bounds used for validation when saving.
HISTORY_LIMIT_MIN, HISTORY_LIMIT_MAX = 1, 1000
POLL_INTERVAL_MIN = 0.2
PORT_MIN, PORT_MAX = 1024, 65535


def get_current_lan_ip() -> str | None:
    """
    Returns the LAN IP the OS would use to reach the outside world, correctly
    skipping virtual interfaces like Docker bridges. Returns None if detection
    fails (e.g. no network connectivity at all).
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return None
    finally:
        s.close()


def get_settings_path() -> Path:
    base_path = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    config_dir = Path(base_path) / "clipvault"
    os.makedirs(config_dir, exist_ok=True)
    return config_dir / "settings.json"


def load_settings() -> dict:
    """
    Returns the current settings, merged over the defaults so a missing or
    partially-written settings.json never causes a KeyError elsewhere in the app.
    """
    path = get_settings_path()
    if not path.exists():
        return dict(DEFAULTS)

    try:
        with open(path, "r") as f:
            saved = json.load(f)
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULTS)

    merged = dict(DEFAULTS)
    merged.update(saved)
    return merged


def validate_settings(new_values: dict) -> list[str]:
    """
    Checks proposed setting values against sane bounds.
    Returns a list of human-readable error strings; empty list means valid.
    """
    errors = []

    if "history_limit" in new_values:
        value = new_values["history_limit"]
        if not isinstance(value, int) or not (
            HISTORY_LIMIT_MIN <= value <= HISTORY_LIMIT_MAX
        ):
            errors.append(
                f"History limit must be a whole number between {HISTORY_LIMIT_MIN} and {HISTORY_LIMIT_MAX}."
            )

    if "poll_interval" in new_values:
        value = new_values["poll_interval"]
        if not isinstance(value, (int, float)) or value < POLL_INTERVAL_MIN:
            errors.append(
                f"Poll interval must be at least {POLL_INTERVAL_MIN} seconds."
            )

    if "port" in new_values:
        value = new_values["port"]
        if not isinstance(value, int) or not (PORT_MIN <= value <= PORT_MAX):
            errors.append(
                f"Port must be a whole number between {PORT_MIN} and {PORT_MAX}."
            )
    if "playback_mode" in new_values:
        if new_values["playback_mode"] not in ("time", "index"):
            errors.append("Playback mode must be 'time' or 'index'.")

    if "dark_palette" in new_values or "light_palette" in new_values:
        from palettes import PALETTES
        for key in ("dark_palette", "light_palette"):
            if key in new_values and new_values[key] not in PALETTES:
                errors.append(f"Unknown palette selected for {key}.")

    return errors


def save_settings(new_values: dict) -> list[str]:
    """
    Validates and saves the given settings, merged over whatever's already saved.
    Returns a list of validation errors; if non-empty, nothing was written.
    """
    errors = validate_settings(new_values)
    if errors:
        return errors

    current = load_settings()
    current.update(new_values)

    path = get_settings_path()
    with open(path, "w") as f:
        json.dump(current, f, indent=2)

    return []


def check_ip_changed() -> tuple[bool, str | None, str | None]:
    """
    Compares the current LAN IP against the last known one stored in settings.

    Returns (changed, old_ip, new_ip):
      - changed is False if detection failed, or the IP is unchanged
      - old_ip is whatever was previously stored (may be None on first run)
      - new_ip is the freshly detected IP (may be None if detection failed)
    """
    current_ip = get_current_lan_ip()
    if current_ip is None:
        return False, None, None

    settings = load_settings()
    old_ip = settings.get("last_known_ip")

    if old_ip == current_ip:
        return False, old_ip, current_ip

    return True, old_ip, current_ip


def _standalone_test():
    print("Current settings:", load_settings())

    print("\nTrying an invalid port...")
    errs = save_settings({"port": 80})
    print("Errors:", errs)

    print("\nSaving a valid change...")
    errs = save_settings({"history_limit": 100})
    print("Errors:", errs)
    print("New settings:", load_settings())


if __name__ == "__main__":
    _standalone_test()
