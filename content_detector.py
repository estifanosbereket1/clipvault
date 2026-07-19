import json
import re

from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.util import ClassNotFound

CANDIDATE_LANGUAGES = [
    "python",
    "bash",
    "javascript",
    "typescript",
    "sql",
    "yaml",
    "html",
    "css",
    "java",
    "go",
    "rust",
    "c",
    "cpp",
    "php",
    "ruby",
]

MIN_CONFIDENCE = 0.15

JWT_PATTERN = re.compile(r"^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$")
URL_PATTERN = re.compile(r"^https?://[^\s]+$")
UUID_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
IPV4_PATTERN = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$")
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

GIT_SSH_PATTERN = re.compile(r"^git@[\w.\-]+:[\w.\-/]+\.git$")
GIT_HTTPS_PATTERN = re.compile(r"^https?://[\w.\-]+/[\w.\-/]+\.git$")
DOCKER_IMAGE_PATTERN = re.compile(
    r"^([\w.\-]+(:[0-9]+)?/)?[\w.\-]+(/[\w.\-]+)*(:[\w.\-]+)?$"
)

MIN_LINES_FOR_CODE_DETECTION = 3




SSH_TARGET_PATTERN = re.compile(r"^ssh\s+[\w.\-]+@[\w.\-]+$")
SSH_BARE_TARGET_PATTERN = re.compile(r"^[\w\-]+@(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|[\w\-]+)$")

SECRET_PATTERNS = [
    ("AWS Access Key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("GitHub Personal Access Token", re.compile(r"ghp_[A-Za-z0-9]{36}")),
    ("GitHub Fine-Grained Token", re.compile(r"github_pat_[A-Za-z0-9_]{22,}")),
    ("GitHub OAuth Token", re.compile(r"gho_[A-Za-z0-9]{36}")),
    ("Slack Token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("Stripe Live Secret Key", re.compile(r"sk_live_[A-Za-z0-9]{20,}")),
    ("Stripe Test Secret Key", re.compile(r"sk_test_[A-Za-z0-9]{20,}")),
    ("Private Key", re.compile(r"-----BEGIN (RSA |OPENSSH |EC |DSA |)PRIVATE KEY-----")),
]


def contains_secret(text: str) -> str | None:
    for name, pattern in SECRET_PATTERNS:
        if pattern.search(text):
            return name
    return None

def _looks_like_docker_image(text: str) -> bool:
    if len(text) > 200 or " " in text or "\n" in text:
        return False
    if not DOCKER_IMAGE_PATTERN.match(text):
        return False
    # require at least a tag or a registry-style slash, so bare single words
    # (like "hello") don't get misclassified as image references
    return ":" in text or "/" in text


def _is_valid_ipv4(text: str) -> bool:
    if not IPV4_PATTERN.match(text):
        return False
    octets = text.split(".")
    return all(0 <= int(o) <= 255 for o in octets)


def _guess_code_language(text: str) -> str | None:
    line_count = text.count("\n") + 1
    if line_count < MIN_LINES_FOR_CODE_DETECTION:
        return None

    best_name = None
    best_score = 0.0

    for lang in CANDIDATE_LANGUAGES:
        lexer = get_lexer_by_name(lang)
        score = lexer.analyse_text(text)
        if score > best_score:
            best_score = score
            best_name = lexer.name

    if best_score >= MIN_CONFIDENCE:
        return best_name

    return None

def detect_type(text: str) -> str:
    stripped = text.strip()

    if not stripped:
        return "text"

    if JWT_PATTERN.match(stripped):
        return "jwt"

    if stripped[0] in "{[":
        try:
            json.loads(stripped)
            return "json"
        except (json.JSONDecodeError, ValueError):
            pass

    if GIT_SSH_PATTERN.match(stripped) or GIT_HTTPS_PATTERN.match(stripped):
        return "git_url"

    if SSH_TARGET_PATTERN.match(stripped) or SSH_BARE_TARGET_PATTERN.match(stripped):
        return "ssh_target"

    if URL_PATTERN.match(stripped):
        return "url"

    if UUID_PATTERN.match(stripped):
        return "uuid"

    if _is_valid_ipv4(stripped):
        return "ip_address"

    if EMAIL_PATTERN.match(stripped):
        return "email"

    if "Traceback (most recent call last)" in stripped:
        return "stack_trace"

    if _looks_like_docker_image(stripped):
        return "docker_image"

    code_language = _guess_code_language(stripped)
    if code_language:
        return f"code:{code_language}"

    return "text"


# def detect_type(text: str) -> str:
#     stripped = text.strip()

#     if not stripped:
#         return "text"

#     if JWT_PATTERN.match(stripped):
#         return "jwt"

#     if stripped[0] in "{[":
#         try:
#             json.loads(stripped)
#             return "json"
#         except (json.JSONDecodeError, ValueError):
#             pass

#     if URL_PATTERN.match(stripped):
#         return "url"

#     if UUID_PATTERN.match(stripped):
#         return "uuid"

#     if _is_valid_ipv4(stripped):
#         return "ip_address"

#     if EMAIL_PATTERN.match(stripped):
#         return "email"

#     if GIT_SSH_PATTERN.match(stripped) or GIT_HTTPS_PATTERN.match(stripped):
#         return "git_url"

#     if SSH_TARGET_PATTERN.match(stripped):
#         return "ssh_target"

#     if URL_PATTERN.match(stripped):
#         return "url"

#     if UUID_PATTERN.match(stripped):
#         return "uuid"

#     if "Traceback (most recent call last)" in stripped:
#         return "stack_trace"

#     if _looks_like_docker_image(stripped):
#         return "docker_image"

#     code_language = _guess_code_language(stripped)
#     if code_language:
#         return f"code:{code_language}"

#     return "text"


def _standalone_test():
    samples = {
        "jwt": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0In0.dQw4w9WgXcQ",
        "json": '{"name": "clip", "count": 5}',
        "url": "https://example.com/path?query=1",
        "uuid": "550e8400-e29b-41d4-a716-446655440000",
        "ip": "192.168.0.136",
        "email": "someone@example.com",
        "plain": "just some regular text I copied",
        "short_code": "x = 5",
        "python": "def add(a, b):\n    return a + b\n\nprint(add(1, 2))",
        "bash": "#!/bin/bash\nfor f in *.txt; do\n  echo $f\ndone",
        "typescript": "interface User {\n  name: string;\n  age: number;\n}\n\nconst u: User = { name: 'a', age: 1 };",
    }
    for label, text in samples.items():
        print(f"{label:16} -> {detect_type(text)}")


if __name__ == "__main__":
    _standalone_test()
