#!/bin/bash
set -e

echo "=== ClipVault Uninstaller ==="
echo ""

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "--- Stopping and disabling the service ---"
if systemctl --user is-active --quiet clipvault.service 2>/dev/null; then
    systemctl --user stop clipvault.service
    echo "Service stopped."
else
    echo "Service not running, skipping stop."
fi

if systemctl --user is-enabled --quiet clipvault.service 2>/dev/null; then
    systemctl --user disable clipvault.service
    echo "Service disabled."
else
    echo "Service not enabled, skipping disable."
fi

SYSTEMD_FILE="$HOME/.config/systemd/user/clipvault.service"
if [ -f "$SYSTEMD_FILE" ]; then
    rm "$SYSTEMD_FILE"
    systemctl --user daemon-reload
    echo "Service file removed."
fi

echo ""
echo "--- Removing application launcher ---"
DESKTOP_FILE="$HOME/.local/share/applications/clipvault.desktop"
if [ -f "$DESKTOP_FILE" ]; then
    rm "$DESKTOP_FILE"
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
    echo "Launcher removed."
else
    echo "No launcher found, skipping."
fi

echo ""
echo "--- Removing the GNOME custom hotkey (if set) ---"
python3 -c "
import sys
sys.path.insert(0, '$PROJECT_DIR')
try:
    from gnome_shortcuts import find_shortcut_by_name, unregister_custom_shortcut
    existing = find_shortcut_by_name('Open ClipVault')
    if existing:
        path, _ = existing
        unregister_custom_shortcut(path)
        print('Hotkey removed.')
    else:
        print('No hotkey found, skipping.')
except Exception as e:
    print(f'Could not remove hotkey automatically: {e}')
" 2>/dev/null || echo "Could not remove hotkey automatically (venv may already be gone)."

echo ""
read -p "Delete your clipboard history and settings too? This cannot be undone. [y/N] " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf "$HOME/.config/clipvault"
    rm -rf "$HOME/.local/share/clipvault"
    echo "Clipboard history and settings deleted."
else
    echo "Keeping your data at ~/.config/clipvault and ~/.local/share/clipvault."
fi

echo ""
read -p "Remove the project folder itself ($PROJECT_DIR)? [y/N] " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "This will delete the folder this script is running from."
    read -p "Are you sure? Type 'yes' to confirm: " -r CONFIRM
    if [[ "$CONFIRM" == "yes" ]]; then
        cd "$HOME"
        rm -rf "$PROJECT_DIR"
        echo "Project folder removed."
    else
        echo "Skipped."
    fi
else
    echo "Project folder left in place. (You can delete it manually, or keep it to reinstall later.)"
fi

echo ""
echo "=== ClipVault has been uninstalled. ==="
