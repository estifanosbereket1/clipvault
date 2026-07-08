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

MIN_LINES_FOR_CODE_DETECTION = 3


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

    code_language = _guess_code_language(stripped)
    if code_language:
        return f"code:{code_language}"

    return "text"


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
