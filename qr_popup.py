import qrcode

from settings_store import load_settings


def generate_qr_for_entry(entry_id: int) -> str:
    settings = load_settings()
    base_url = f"https://{settings['last_known_ip']}:{settings['port']}"
    url = f"{base_url}/c/{entry_id}"
    image_path = f"/tmp/clipqr_qr_{entry_id}.png"
    qrcode.make(url).save(image_path)
    return image_path


def generate_qr_for_url(url: str, label: str) -> str:
    image_path = f"/tmp/clipqr_qr_{label}.png"
    qrcode.make(url).save(image_path)
    return image_path
