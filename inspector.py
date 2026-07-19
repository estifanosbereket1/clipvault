import base64
import json
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs
import re

def _decode_jwt_segment(segment: str) -> dict:
    padded = segment + "=" * (-len(segment) % 4)
    decoded_bytes = base64.urlsafe_b64decode(padded)
    return json.loads(decoded_bytes)


def inspect_jwt(token: str) -> dict:
    """
    Returns {"header": dict, "payload": dict, "expiry_info": str | None, "error": str | None}
    """
    try:
        parts = token.strip().split(".")
        header = _decode_jwt_segment(parts[0])
        payload = _decode_jwt_segment(parts[1])
    except Exception as e:
        return {"header": None, "payload": None, "expiry_info": None, "error": str(e)}

    expiry_info = None
    if "exp" in payload:
        try:
            exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
            now = datetime.now(timezone.utc)
            if exp_time > now:
                delta = exp_time - now
                expiry_info = f"Expires {exp_time.strftime('%Y-%m-%d %H:%M UTC')} (in {delta.days}d {delta.seconds // 3600}h)"
            else:
                delta = now - exp_time
                expiry_info = f"Expired {exp_time.strftime('%Y-%m-%d %H:%M UTC')} ({delta.days}d {delta.seconds // 3600}h ago)"
        except Exception:
            expiry_info = None

    return {"header": header, "payload": payload, "expiry_info": expiry_info, "error": None}


def inspect_json(text: str) -> dict:
    """Returns {"pretty": str, "error": str | None}"""
    try:
        parsed = json.loads(text)
        pretty = json.dumps(parsed, indent=2, ensure_ascii=False)
        return {"pretty": pretty, "error": None}
    except Exception as e:
        return {"pretty": None, "error": str(e)}


def inspect_url(url: str) -> dict:
    """Returns {"scheme": str, "hostname": str, "path": str, "query_params": dict, "error": str | None}"""
    try:
        parsed = urlparse(url)
        query_params = {k: v[0] if len(v) == 1 else v for k, v in parse_qs(parsed.query).items()}
        return {
            "scheme": parsed.scheme,
            "hostname": parsed.hostname or "",
            "path": parsed.path or "/",
            "query_params": query_params,
            "error": None,
        }
    except Exception as e:
        return {"scheme": None, "hostname": None, "path": None, "query_params": None, "error": str(e)}



def inspect_git_url(url: str) -> dict:
    """
    Returns {"host": str, "owner": str, "repo": str, "https_clone": str,
             "ssh_clone": str, "browser_url": str, "error": str | None}
    """
    try:
        if url.startswith("git@"):
            # git@host:owner/repo.git
            match = re.match(r"^git@([\w.\-]+):([\w.\-]+)/([\w.\-]+?)(\.git)?$", url.strip())
            if not match:
                raise ValueError("Couldn't parse SSH git URL")
            host, owner, repo = match.group(1), match.group(2), match.group(3)
        else:
            # https://host/owner/repo.git
            match = re.match(r"^https?://([\w.\-]+)/([\w.\-]+)/([\w.\-]+?)(\.git)?$", url.strip())
            if not match:
                raise ValueError("Couldn't parse HTTPS git URL")
            host, owner, repo = match.group(1), match.group(2), match.group(3)

        return {
            "host": host,
            "owner": owner,
            "repo": repo,
            "https_clone": f"https://{host}/{owner}/{repo}.git",
            "ssh_clone": f"git@{host}:{owner}/{repo}.git",
            "browser_url": f"https://{host}/{owner}/{repo}",
            "error": None,
        }
    except Exception as e:
        return {"host": None, "owner": None, "repo": None, "https_clone": None,
                "ssh_clone": None, "browser_url": None, "error": str(e)}


def inspect_docker_image(ref: str) -> dict:
    """Returns {"pull_command": str, "run_command": str, "error": str | None}"""
    ref = ref.strip()
    if not ref:
        return {"pull_command": None, "run_command": None, "error": "Empty reference"}
    return {
        "pull_command": f"docker pull {ref}",
        "run_command": f"docker run -it {ref}",
        "error": None,
    }


def inspect_ssh_target(target: str) -> dict:
    """Returns {"ssh_command": str, "scp_template": str, "error": str | None}"""
    cleaned = target.strip()
    if cleaned.startswith("ssh "):
        cleaned = cleaned[len("ssh "):].strip()

    if "@" not in cleaned:
        return {"ssh_command": None, "scp_template": None, "error": "No user@host found"}

    return {
        "ssh_command": f"ssh {cleaned}",
        "scp_template": f"scp <local_file> {cleaned}:<remote_path>",
        "error": None,
    }

def _standalone_test():
    jwt_sample = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0IiwiZXhwIjoxODAwMDAwMDAwfQ.dQw4w9WgXcQ"
    print("JWT:", inspect_jwt(jwt_sample))

    json_sample = '{"name": "test", "nested": {"a": 1, "b": [1,2,3]}}'
    print("\nJSON:", inspect_json(json_sample))

    url_sample = "https://example.com/search?q=clipvault&page=2"
    print("\nURL:", inspect_url(url_sample))

    print("Git SSH:", inspect_git_url("git@github.com:torvalds/linux.git"))
    print("Git HTTPS:", inspect_git_url("https://github.com/torvalds/linux.git"))
    print("Docker:", inspect_docker_image("ghcr.io/someorg/someimage:v1.2.3"))
    print("SSH:", inspect_ssh_target("ssh deploy@myserver.com"))
    print("SSH bare:", inspect_ssh_target("user@192.168.1.10"))


if __name__ == "__main__":
    _standalone_test()
