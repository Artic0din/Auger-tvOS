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
import bisect
import re
import sys
from pathlib import Path

SCAN_DIRS = ["iosApp/iosApp", "iosApp/TopShelf", "iosApp/NotificationService", "iosApp/DownloadsActivity"]

IGNORE = re.compile(r"^//\s*state-init-ignore:\s*\S")

# `_name = State(...)`, `State<T>(...)`, or State's own contextual
# `.init(initialValue:)`, `.init(wrappedValue:)` and `.init()` (add a label here if
# the app ever extends State with its own initializer); a local
# `let _name = ...` declares a new value and is not the property's storage.
# After `State`, `calls_state` decides whether it is called.
INIT_ASSIGNMENT = re.compile(
    r"(?<![\w.])(?<!let )(?<!var )(?:self\s*\.\s*)?_(\w+)\s*=\s*"
    r"(?:(State)\b|\.\s*init\s*\(\s*(?:initialValue\s*:|wrappedValue\s*:|\)))"
)

_TYPE_KEYWORDS = {"async", "throws", "any", "some", "inout", "borrowing", "consuming", "sending", "each", "repeat"}
_CLOSERS = {"<": ">", "[": "]", "(": ")"}


def _skip_space(code: str, i: int) -> int:
    while i < len(code) and code[i].isspace():
        i += 1
    return i


def calls_state(code: str, i: int) -> bool:
    """Whether the `State` ending at `i` is called, directly or as `State<T>(`.

    Generic arguments are read as a type, which may span lines: brackets nest
    and match, two names or integers sit side by side only after a keyword such
    as `some` or `async`, and nothing else but `.,:?!&@`, backticks and `->`
    appears. A `State < x` comparison
    breaks one of those rules before it can reach a later `> (`.
    """
    n = len(code)
    i = _skip_space(code, i)
    if code.startswith("(", i):
        return True
    if not code.startswith("<", i):
        return False
    stack, previous_name, i = ["<"], None, i + 1
    while i < n and stack:
        ch = code[i]
        if ch.isspace():
            i += 1
            continue
        if ch.isalnum() or ch == "_":
            j = i
            while j < n and (code[j].isalnum() or code[j] == "_"):
                j += 1
            if previous_name is not None and previous_name not in _TYPE_KEYWORDS:
                return False
            previous_name, i = code[i:j], j
            continue
        previous_name = None
        if code.startswith("->", i):
            i += 2
            continue
        if ch in _CLOSERS:
            stack.append(ch)
        elif ch in ">])":
            if _CLOSERS[stack.pop()] != ch:
                return False
        elif ch not in ".,:?!&@`":
            return False
        i += 1
    return not stack and code.startswith("(", _skip_space(code, i))


# `@State`, then attributes and modifiers, then `var name`. Each repeated token
# ends in mandatory whitespace, so the match never backtracks into ambiguous
# splits. `has_default` then reads the type annotation for a default.
_MODIFIER = r"(?:@\w+(?:\([^()]*\))?|private|fileprivate|internal|public|package|open|static|nonisolated)"
STATE_DECLARATION = re.compile(r"@State\b(?:\([^()]*\))?\s+(?:" + _MODIFIER + r"(?:\(\w+\))?\s+)*var\s+(\w+)\b")


def has_default(code: str, i: int) -> bool:
    """Whether the declaration from offset `i` (after its name) has a default.

    Brackets in the type annotation may span lines, and so may the gap after
    `:`. Outside them, a `{` or `;` ends the declaration without a default, and
    so does a line break unless the next non-blank line starts with `=`
    (comments are already blanked).
    """
    depth, n, last = 0, len(code), ""
    while i < n:
        ch = code[i]
        if code.startswith("->", i):
            i += 2
            continue
        if ch in "[(<":
            depth += 1
        elif ch in "])>":
            depth -= 1
        elif depth <= 0 and ch == "=":
            return not code.startswith("==", i)
        elif depth <= 0 and ch in "{;":
            return False
        elif depth <= 0 and ch == "\n":
            j = i + 1
            while j < n and code[j] in " \t\n":
                j += 1
            if last == ":":
                i = j
                continue
            return code.startswith("=", j) and not code.startswith("==", j)
        if not ch.isspace():
            last = ch
        i += 1
    return False


class _Lexer:
    """Blanks comments and string-literal text, keeping every newline and offset.

    Handles `//` and nested `/* */` comments, one-line, multiline and raw
    (`#"..."#`) strings, and code inside `\\(...)` interpolation, which may
    hold strings of its own, and extended `#/.../#` regex literals. Records
    each `//` comment by line for the ignore marker.

    shortcut: a bare `/.../` regex literal is lexed as code, since telling it
    from division needs Swift's own heuristics; the app uses only `#/.../#`.
    Upgrade if bare regex literals appear in the app sources.
    """

    def __init__(self, source: str) -> None:
        self.src = source
        self.out = list(source)
        self.n = len(source)
        self.line_comments: dict[int, list[str]] = {}
        self.newlines = [k for k, ch in enumerate(source) if ch == "\n"]

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
                line = bisect.bisect_left(self.newlines, i) + 1
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
                elif hashes and i + hashes < n and src[i + hashes] == "/":
                    # Extended regex literal `#/.../#`: no comments or code inside.
                    close, j = "/" + "#" * hashes, i + hashes + 1
                    while j < n and not src.startswith(close, j):
                        j += 2 if src[j] == "\\" else 1
                    end = min(j + len(close), n)
                    self.blank(i, end)
                    i = end
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
        # `"""` opens a multiline string only when the line ends there;
        # `#"""x"#` is a one-line raw string holding `""x`.
        rest = src[quote + 3 : (src.find("\n", quote) + 1 or n + 1) - 1]
        multiline = src.startswith('"""', quote) and not rest.strip()
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
    assigned = {
        m.group(1) for m in INIT_ASSIGNMENT.finditer(code) if not m.group(2) or calls_state(code, m.end())
    }
    hits = []
    for match in STATE_DECLARATION.finditer(code):
        name = match.group(1)
        if not has_default(code, match.end()):
            continue
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
