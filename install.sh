echo "=== ClipVault Installer ==="
echo ""

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Installing ClipVault from: $PROJECT_DIR"
echo ""

detect_package_manager() {
    if command -v apt &> /dev/null; then
        echo "apt"
    elif command -v pacman &> /dev/null; then
        echo "pacman"
    elif command -v dnf &> /dev/null; then
        echo "dnf"
    else
        echo "unknown"
    fi
}

PKG_MANAGER=$(detect_package_manager)
echo "Detected package manager: $PKG_MANAGER"
echo ""

if [ "$PKG_MANAGER" == "unknown" ]; then
    echo "⚠ Couldn't detect apt, pacman, or dnf on this system."
    echo "  Please install these manually before continuing:"
    echo "  - Python 3 with venv/pip"
    echo "  - GTK3 + Python GObject bindings (PyGObject)"
    echo "  - libappindicator/ayatana-appindicator (for the tray icon)"
    echo "  - xclip (or wl-clipboard on Wayland)"
    echo "  - NSS tools (required by mkcert)"
    echo "  - git"
    read -p "Press Enter once these are installed, or Ctrl+C to stop and do it now. "
else
    read -p "Install system dependencies now using $PKG_MANAGER? [Y/n] " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        echo "--- Installing system dependencies ---"
        case "$PKG_MANAGER" in
            apt)
                sudo apt update
                sudo apt install -y \
                    python3-venv python3-pip git \
                    python3-gi gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1 \
                    xclip \
                    libnss3-tools
                ;;
            pacman)
                sudo pacman -Syu --needed --noconfirm \
                    python python-pip git \
                    python-gobject gtk3 libappindicator-gtk3 \
                    xclip \
                    nss
                ;;
            dnf)
                sudo dnf install -y \
                    python3-pip git \
                    python3-gobject gtk3 \
                    xclip \
                    nss-tools
                echo ""
                echo "⚠ Fedora's default repos may not include Ayatana AppIndicator support."
                echo "  If the tray icon doesn't appear after install, you may need:"
                echo "  sudo dnf copr enable alebastr/kde-gtk-config"
                echo "  or check https://extensions.gnome.org/extension/615/appindicator-support/"
                ;;
        esac
        echo "System dependencies installed."
    else
        echo "Skipping automatic dependency install -- make sure they're installed manually."
    fi
fi
