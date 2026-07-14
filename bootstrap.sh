#!/bin/bash
set -e

REPO_URL="https://github.com/estifanosbereket1/clipvault.git"
INSTALL_DIR="${CLIPVAULT_DIR:-$HOME/ClipVault}"

echo "=== ClipVault Bootstrap ==="
echo ""

if ! command -v git &> /dev/null; then
    echo "git is required but not installed. Installing it now..."
    sudo apt update
    sudo apt install -y git
fi

if [ -d "$INSTALL_DIR/.git" ]; then
    echo "ClipVault already exists at $INSTALL_DIR, updating..."
    cd "$INSTALL_DIR"
    git fetch origin
    git reset --hard origin/main
else
    echo "Cloning ClipVault to $INSTALL_DIR..."
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

chmod +x install.sh
./install.sh < /dev/tty
