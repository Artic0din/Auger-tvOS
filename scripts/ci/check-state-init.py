#!/usr/bin/env python3
"""Blocks a @State property that has a default and is also set in an initializer.

Once @State is a macro (SwiftUI 27), a declaration default plus an
`_name = State(initialValue:)` assignment in `init` is unsupported, and the
default can win. Give the property no default and let `init` supply the only
initial value. A file-wide match can pair a property with a same-named one
in another type; end that declaration line with
`// state-init-ignore: <reason>`.

Usage: scripts/ci/check-state-init.py [--root DIR]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCAN_DIRS = ["iosApp/iosApp", "iosApp/TopShelf", "iosApp/NotificationService", "iosApp/DownloadsActivity"]

IGNORE = re.compile(r"^//\s*state-init-ignore:\s*\S")

INIT_ASSIGNMENT = re.compile(r"(?<![\w.])(?:self\s*\.\s*)?_(\w+)\s*=\s*State\s*(?:<[^\n]*?>)?\s*\(")

# `@State`, then attributes and modifiers, then `var name`, an optional type
# annotation, and `=` on that line or at the start of the next. Each repeated
# token ends in mandatory whitespace, so the match never backtracks into
# ambiguous splits. A `{` ends the annotation, so computed properties pass.
_MODIFIER = r"(?:@\w+(?:\([^()]*\))?|private|fileprivate|internal|public|package|open|static|nonisolated)"
DEFAULTED_STATE = re.compile(
    r"@State\b(?:\([^()]*\))?\s+(?:" + _MODIFIER + r"(?:\(\w+\))?\s+)*var\s+(\w+)\b[^=\n{]*(?:\n[ \t]*)?=(?!=)"
)

class _Lexer:
    """Blanks comments and string-literal text, keeping every newline and offset.

    Handles `//` and nested `/* */` comments, one-line, multiline and raw
    (`#"..."#`) strings, and code inside `\\(...)` interpolation, which may
    hold strings of its own. Records each `//` comment by line for the ignore
    marker.
    """

    def __init__(self, source: str) -> None:
        self.src = source
        self.out = list(source)
        self.n = len(source)
        self.line_comments: dict[int, list[str]] = {}

    def blank(self, start: int, end: int) -> None:
        for k in range(start, min(end, self.n)):
            if self.out[k] != "\n":
                self.out[k] = " "

    def code(self, i: int, in_interpolation: bool = False) -> int:
        """Lexes code from `i`; inside interpolation, returns just past the closing `)`."""
        src, n, depth = self.src, self.n, 0
        while i < n:
            if src.startswith("//", i):
                end = src.find("\n", i)
                end = n if end == -1 else end
                line = src.count("\n", 0, i) + 1
                self.line_comments.setdefault(line, []).append(src[i:end])
                self.blank(i, end)
                i = end
            elif src.startswith("/*", i):
                nest, j = 1, i + 2
                while j < n and nest:
                    if src.startswith("/*", j):
                        nest, j = nest + 1, j + 2
                    elif src.startswith("*/", j):
                        nest, j = nest - 1, j + 2
                    else:
                        j += 1
                self.blank(i, j)
                i = j
            elif src[i] in '#"':
                hashes = 0
                while i + hashes < n and src[i + hashes] == "#":
                    hashes += 1
                if i + hashes < n and src[i + hashes] == '"':
                    i = self.string(i, hashes)
                else:
                    i += max(hashes, 1)
            elif in_interpolation and src[i] == "(":
                depth, i = depth + 1, i + 1
            elif in_interpolation and src[i] == ")":
                if depth == 0:
                    return i + 1
                depth, i = depth - 1, i + 1
            else:
                i += 1
        return i

    def string(self, start: int, hashes: int) -> int:
        """Blanks the literal opening at `start`; returns the offset just past it."""
        src, n = self.src, self.n
        quote = start + hashes
        multiline = src.startswith('"""', quote)
        close = ('"""' if multiline else '"') + "#" * hashes
        escape = "\\" + "#" * hashes
        i = quote + (3 if multiline else 1)
        segment = start
        while i < n:
            if src.startswith(close, i):
                i += len(close)
                break
            if not multiline and src[i] == "\n":
                break
            if src.startswith(escape + "(", i):
                self.blank(segment, i)
                i = self.code(i + len(escape) + 1, in_interpolation=True)
                segment = i
                continue
            i += len(escape) + 1 if src.startswith(escape, i) else 1
        self.blank(segment, i)
        return i


def strip_comments_and_strings(source: str) -> tuple[str, dict[int, list[str]]]:
    lexer = _Lexer(source)
    lexer.code(0)
    return "".join(lexer.out), lexer.line_comments


def scan_source(source: str) -> list[tuple[int, str]]:
    """Returns (line, name) for each defaulted @State the same file also sets in init."""
    code, line_comments = strip_comments_and_strings(source)
    assigned = set(INIT_ASSIGNMENT.findall(code))
    hits = []
    for match in DEFAULTED_STATE.finditer(code):
        name = match.group(1)
        line = code.count("\n", 0, match.start(1)) + 1
        ignored = any(IGNORE.match(comment) for comment in line_comments.get(line, []))
        if name in assigned and not ignored:
            hits.append((line, name))
    return hits


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args(argv)

    failures = []
    for scan_dir in SCAN_DIRS:
        directory = args.root / scan_dir
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob("*.swift")):
            for line, name in scan_source(path.read_text(encoding="utf-8")):
                failures.append(f"{path.relative_to(args.root)}:{line}: @State var {name}")

    if not failures:
        print("check-state-init: ok")
        return 0
    print("\n".join(failures))
    print(
        "\nerror: these @State properties have a default and are also set in init.\n"
        "Under the SwiftUI 27 @State macro the default can win. Remove the default\n"
        "so `_name = State(initialValue:)` in init is the only initial value."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
