import difflib


def _word_diff(old_line: str, new_line: str) -> str:
    """
    Highlights word-level changes within a single modified line,
    e.g. "line [-two-]{+TWO changed+}"
    """
    old_words = old_line.split()
    new_words = new_line.split()
    matcher = difflib.SequenceMatcher(None, old_words, new_words)

    parts = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            parts.append(" ".join(old_words[i1:i2]))
        elif tag == "replace":
            parts.append(f"[-{' '.join(old_words[i1:i2])}-]")
            parts.append(f"{{+{' '.join(new_words[j1:j2])}+}}")
        elif tag == "delete":
            parts.append(f"[-{' '.join(old_words[i1:i2])}-]")
        elif tag == "insert":
            parts.append(f"{{+{' '.join(new_words[j1:j2])}+}}")

    return " ".join(parts)


def get_diff(old_text: str, new_text: str) -> dict:
    """
    Returns {
        "lines": list of (line_type, content) where line_type is
                 "add" / "remove" / "same" / "modified",
        "summary": {"added": n, "removed": n, "modified": n},
    }
    For "modified" lines, content is the word-diff-highlighted string.
    """
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()

    raw = [
        line
        for line in difflib.ndiff(old_lines, new_lines)
        if not line.startswith("? ")
    ]

    lines = []
    summary = {"added": 0, "removed": 0, "modified": 0}

    i = 0
    while i < len(raw):
        prefix = raw[i][:2]
        content = raw[i][2:]

        # A "- " immediately followed by "+ " is treated as one modified line
        if prefix == "- " and i + 1 < len(raw) and raw[i + 1][:2] == "+ ":
            old_line = content
            new_line = raw[i + 1][2:]
            lines.append(("modified", _word_diff(old_line, new_line)))
            summary["modified"] += 1
            i += 2
            continue

        if prefix == "+ ":
            lines.append(("add", content))
            summary["added"] += 1
        elif prefix == "- ":
            lines.append(("remove", content))
            summary["removed"] += 1
        elif prefix == "  ":
            lines.append(("same", content))

        i += 1

    return {"lines": lines, "summary": summary}


def format_summary(summary: dict) -> str:
    parts = []
    if summary["modified"]:
        parts.append(f"{summary['modified']} modified")
    if summary["added"]:
        parts.append(f"{summary['added']} added")
    if summary["removed"]:
        parts.append(f"{summary['removed']} removed")
    return ", ".join(parts) if parts else "No changes"


def _standalone_test():
    old = "line one\nline two\nline three"
    new = "line one\nline TWO changed\nline three\nline four added"

    result = get_diff(old, new)
    print(format_summary(result["summary"]))
    print()
    for line_type, content in result["lines"]:
        marker = {"add": "+", "remove": "-", "same": " ", "modified": "~"}[line_type]
        print(f"{marker} {content}")


if __name__ == "__main__":
    _standalone_test()
