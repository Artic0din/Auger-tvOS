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

IGNORE = "state-init-ignore"

INIT_ASSIGNMENT = re.compile(r"(?<![\w.])(?:self\s*\.\s*)?_(\w+)\s*=\s*State\s*(?:<[^\n]*?>)?\s*\(")

# `@State`, then attributes and modifiers, then `var name`, an optional type
# annotation, and `=` on that line or at the start of the next. Each repeated
# token ends in mandatory whitespace, so the match never backtracks into
# ambiguous splits. A `{` ends the annotation, so computed properties pass.
_MODIFIER = r"(?:@\w+(?:\([^()]*\))?|private|fileprivate|internal|public|package|open|static|nonisolated)"
DEFAULTED_STATE = re.compile(
    r"@State\b(?:\([^()]*\))?\s+(?:" + _MODIFIER + r"(?:\(\w+\))?\s+)*var\s+(\w+)\b[^=\n{]*(?:\n[ \t]*)?=(?!=)"
)

def strip_comments(source: str) -> str:
    """Blanks `//` and nested `/* */` comments outside strings, keeping every offset."""
    out = list(source)
    i, n = 0, len(source)

    def blank(start: int, end: int) -> None:
        for k in range(start, end):
            if out[k] != "\n":
                out[k] = " "

    while i < n:
        if source.startswith("//", i):
            end = source.find("\n", i)
            end = n if end == -1 else end
            blank(i, end)
            i = end
        elif source.startswith("/*", i):
            depth, j = 1, i + 2
            while j < n and depth:
                if source.startswith("/*", j):
                    depth, j = depth + 1, j + 2
                elif source.startswith("*/", j):
                    depth, j = depth - 1, j + 2
                else:
                    j += 1
            blank(i, j)
            i = j
        elif source[i] == '"':
            # Step over a one-line string so a `//` or `/*` inside it is not
            # read as a comment.
            j = i + 1
            while j < n and source[j] not in '"\n':
                j += 2 if source[j] == "\\" else 1
            i = j + 1
        else:
            i += 1
    return "".join(out)


def scan_source(source: str) -> list[tuple[int, str]]:
    """Returns (line, name) for each defaulted @State the same file also sets in init."""
    code = strip_comments(source)
    lines = source.split("\n")
    assigned = set(INIT_ASSIGNMENT.findall(code))
    hits = []
    for match in DEFAULTED_STATE.finditer(code):
        name = match.group(1)
        line = code.count("\n", 0, match.start(1)) + 1
        if name in assigned and IGNORE not in lines[line - 1]:
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
