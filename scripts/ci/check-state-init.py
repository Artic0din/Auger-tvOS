#!/usr/bin/env python3
"""Blocks a @State property that has a default and is also set in an initializer.

Once @State is a macro (SwiftUI 27), a declaration default plus an
`_name = State(initialValue:)` assignment in `init` is unsupported, and the
default can win. Give the property no default and let `init` supply the only
initial value.

Usage: scripts/ci/check-state-init.py [--root DIR]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCAN_DIRS = ["iosApp/iosApp", "iosApp/TopShelf", "iosApp/NotificationService", "iosApp/DownloadsActivity"]

INIT_ASSIGNMENT = re.compile(r"\b_(\w+)\s*=\s*State\s*\(")
# `@State`, then access modifiers or other attributes (possibly on the next
# line), then `var name`, then a type annotation, then `=`. A `{` stops the
# match so computed properties and observers pass.
DEFAULTED_STATE = re.compile(r"@State\b(?:[\s\w()]|@\w+)*?\bvar\s+(\w+)[^=\n{]*=(?!=)")


def scan_source(source: str) -> list[tuple[int, str]]:
    """Returns (line, name) for each defaulted @State the file also sets in init."""
    assigned = set(INIT_ASSIGNMENT.findall(source))
    hits = []
    for match in DEFAULTED_STATE.finditer(source):
        name = match.group(1)
        if name in assigned:
            line = source.count("\n", 0, match.start(1)) + 1
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
