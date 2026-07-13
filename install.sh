#!/bin/bash
set -e

echo "=== ClipVault Installer ==="
echo ""

# Resolve the project directory as the location of this script itself,
# so the installer works correctly regardless of where it's run from.
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Installing ClipVault from: $PROJECT_DIR"
echo ""

read -p "Run 'sudo apt update' first to ensure package lists are current? [Y/n] " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    sudo apt update
fi

echo "--- Installing system dependencies ---"
sudo apt install -y \
    python3-venv python3-pip git \
    python3-gi gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1 \
    xclip \
    libnss3-tools

echo "System dependencies installed."

echo ""
echo "--- Setting up Python virtual environment ---"

VENV_DIR="$PROJECT_DIR/venv"

if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment already exists, skipping creation."
else
    python3 -m venv "$VENV_DIR" --system-site-packages
    echo "Virtual environment created."
fi

echo "Installing Python dependencies..."
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/requirements.txt"

echo "Python dependencies installed."

echo ""
echo "--- Setting up mkcert (for HTTPS certificates) ---"

if command -v mkcert &> /dev/null; then
    echo "mkcert already installed, skipping."
else
    echo "Installing mkcert..."
    TMP_MKCERT="$(mktemp)"
    curl -sJL "https://dl.filippo.io/mkcert/latest?for=linux/amd64" -o "$TMP_MKCERT"
    chmod +x "$TMP_MKCERT"
    sudo mv "$TMP_MKCERT" /usr/local/bin/mkcert
    echo "mkcert installed."
fi

echo "Setting up local certificate authority..."
mkcert -install
echo "Certificate authority ready."

echo ""
echo "--- Setting up autostart (systemd) ---"

SYSTEMD_DIR="$HOME/.config/systemd/user"
mkdir -p "$SYSTEMD_DIR"

cat > "$SYSTEMD_DIR/clipvault.service" <<EOF
[Unit]
Description=ClipVault clipboard manager
After=graphical-session.target
PartOf=graphical-session.target

[Service]
Type=simple
ExecStart=$VENV_DIR/bin/python3 $PROJECT_DIR/main.py
WorkingDirectory=$PROJECT_DIR
Restart=on-failure
RestartSec=3

[Install]
WantedBy=graphical-session.target
EOF

systemctl --user daemon-reload
systemctl --user enable clipvault.service

echo "Autostart configured. ClipVault will start automatically on login."

echo ""
echo "--- Setting up application launcher ---"

APPS_DIR="$HOME/.local/share/applications"
mkdir -p "$APPS_DIR"

cat > "$APPS_DIR/clipvault.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=ClipVault
Comment=Clipboard manager with QR-to-phone sync
Exec=$VENV_DIR/bin/python3 $PROJECT_DIR/main.py
Icon=$PROJECT_DIR/assets/icons/app-icon.png
Terminal=false
Categories=Utility;
StartupNotify=true
EOF

update-desktop-database "$APPS_DIR" 2>/dev/null || true

echo "Application launcher created. ClipVault is now available in your app menu."

echo ""
echo "=== Installation complete! ==="
echo ""
echo "Starting ClipVault now..."
systemctl --user start clipvault.service
echo "Done. Look for the ClipVault icon in your system tray."
