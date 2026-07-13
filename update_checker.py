import requests
import subprocess
import sys
import os

GITHUB_REPO = "estifanosbereket1/clipqr"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def get_local_version() -> str:
    try:
        with open("VERSION", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return "0.0.0"

def perform_update():
    """
    Spawns a detached shell script that waits for this process to exit,
    then pulls the latest code, reinstalls dependencies, and relaunches
    the app. Returns immediately -- the caller should quit the app right
    after calling this.
    """
    project_dir = os.path.dirname(os.path.abspath(__file__))
    venv_python = os.path.join(project_dir, "venv", "bin", "python3")
    current_pid = os.getpid()

    update_script = f"""#!/bin/bash
# Wait for the current ClipQR process to fully exit
while kill -0 {current_pid} 2>/dev/null; do
    sleep 0.5
done

cd "{project_dir}"
git pull
"{venv_python}" -m pip install -r requirements.txt

# Relaunch
nohup "{venv_python}" "{project_dir}/main.py" > /tmp/clipqr_update.log 2>&1 &
"""

    script_path = "/tmp/clipqr_update.sh"
    with open(script_path, "w") as f:
        f.write(update_script)
    os.chmod(script_path, 0o755)

    subprocess.Popen(
        ["bash", script_path],
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _parse_version(version_str: str) -> tuple:
    """
    Converts "1.2.3" into (1, 2, 3) for proper numeric comparison --
    string comparison alone would incorrectly say "1.10.0" < "1.9.0".
    """
    cleaned = version_str.lstrip("v")
    parts = cleaned.split(".")
    return tuple(int(p) for p in parts if p.isdigit())


def check_for_update() -> dict:
    """
    Returns {
        "update_available": bool,
        "local_version": str,
        "latest_version": str | None,
        "release_url": str | None,
        "error": str | None,
    }
    """
    local_version = get_local_version()

    try:
        response = requests.get(GITHUB_API_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        return {
            "update_available": False,
            "local_version": local_version,
            "latest_version": None,
            "release_url": None,
            "error": str(e),
        }

    latest_version = data.get("tag_name", "").lstrip("v")
    release_url = data.get("html_url")

    try:
        is_newer = _parse_version(latest_version) > _parse_version(local_version)
    except (ValueError, TypeError):
        is_newer = False

    return {
        "update_available": is_newer,
        "local_version": local_version,
        "latest_version": latest_version,
        "release_url": release_url,
        "error": None,
    }


def _standalone_test():
    result = check_for_update()
    print(result)


if __name__ == "__main__":
    _standalone_test()
