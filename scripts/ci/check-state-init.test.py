#!/usr/bin/env python3
"""Tests for check-state-init.py."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("check-state-init.py")
_SPEC = importlib.util.spec_from_file_location("check_state_init", SCRIPT)
guard = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(guard)


class ScanSourceTests(unittest.TestCase):
    def test_flags_defaulted_state_set_in_init(self) -> None:
        for declaration in [
            "@State private var flag: Bool = false",
            "@State var flag = false",
            "@State private(set) var flag: Bool? = nil",
            "@State\n    private var flag: Bool = false",
            "@MainActor @State private var flag: [String: Int] = [:]",
        ]:
            source = f"struct V: View {{\n    {declaration}\n    init() {{ _flag = State(initialValue: true) }}\n}}"
            self.assertEqual([name for _, name in guard.scan_source(source)], ["flag"], declaration)

    def test_reports_the_declaration_line(self) -> None:
        source = "struct V {\n\n    @State private var flag = false\n    init() { _flag = State(initialValue: true) }\n}"
        self.assertEqual(guard.scan_source(source), [(3, "flag")])

    def test_passes_without_default_or_without_init_assignment(self) -> None:
        for source in [
            "@State private var flag: Bool\ninit() { _flag = State(initialValue: true) }",
            "@State private var flag = false\ninit() { _other = State(initialValue: true) }",
            "@State private var flag = false",
            "@State private var flag: Bool { true }\ninit() { _flag = State(initialValue: true) }",
            "@Binding var flag: Bool\nvar other = 1\ninit() { _flag = State(initialValue: true) }",
        ]:
            self.assertEqual(guard.scan_source(source), [], source)


class CommandTests(unittest.TestCase):
    def run_guard(self, root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(root)], capture_output=True, text=True
        )

    def test_exit_status_and_location(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_dir = root / "iosApp/iosApp/Screens"
            source_dir.mkdir(parents=True)
            view = source_dir / "View.swift"
            view.write_text("@State private var flag: Bool\ninit() { _flag = State(initialValue: true) }\n")
            self.assertEqual(self.run_guard(root).returncode, 0)

            view.write_text("@State private var flag = false\ninit() { _flag = State(initialValue: true) }\n")
            result = self.run_guard(root)
            self.assertEqual(result.returncode, 1)
            self.assertIn("iosApp/iosApp/Screens/View.swift:1: @State var flag", result.stdout)


if __name__ == "__main__":
    unittest.main()
