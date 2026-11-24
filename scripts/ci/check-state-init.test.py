#!/usr/bin/env python3
"""Tests for check-state-init.py."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import time
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
            "@State private var flag: Bool\n        = false",
            "@State @available(iOS 18, *) private var flag = false",
            "@State // seeded in init\n    private var flag = false",
            "@State /* note */ private var flag = false",
            "@State private var flag: [\n        String: Bool\n    ] = [:]",
            "@State private var flag: (Int) -> Void = { _ in }",
            "@State private var flag:\n        Bool = false",
            "@State private var flag: Bool\n        // seeded in init\n\n        = false",
        ]:
            source = f"struct V: View {{\n    {declaration}\n    init() {{ _flag = State(initialValue: true) }}\n}}"
            self.assertEqual([name for _, name in guard.scan_source(source)], ["flag"], declaration)

    def test_flags_each_assignment_form(self) -> None:
        for assignment in [
            "_flag = State(initialValue: true)",
            "self._flag = State(wrappedValue: true)",
            "_flag = State<Bool>(initialValue: true)",
            "_flag = State<[String: Set<Int>]>(initialValue: [:])",
            "_flag = State<[String: Array<Set<Int>>]>(initialValue: [:])",
            "_flag = State<[\n            String: Array<Set<Int>>\n        ]>(initialValue: [:])",
            "_flag = State<() async throws -> Void>(initialValue: {})",
            "_flag = State<() async throws(LoadError) -> Void>(initialValue: {})",
            "_flag = State<InlineArray<4, Int>>(initialValue: [1, 2, 3, 4])",
            "_flag = State<`Type`>(initialValue: x)",
            "self._flag = .init(initialValue: true)",
            "_flag = .init(wrappedValue: true)",
            "_flag = .init()",
        ]:
            source = f"struct V: View {{\n    @State private var flag = false\n    init() {{ {assignment} }}\n}}"
            self.assertEqual([name for _, name in guard.scan_source(source)], ["flag"], assignment)

    def test_matches_across_the_file_with_an_ignore_marker(self) -> None:
        extension = (
            "struct A: View {\n    @State private var flag = false\n}\n"
            "extension A {\n    init(on: Bool) { _flag = State(initialValue: on) }\n}"
        )
        self.assertEqual(guard.scan_source(extension), [(2, "flag")])
        other_type = (
            "struct A: View {\n    @State private var flag = false // state-init-ignore: B sets its own\n}\n"
            "struct B: View {\n    @State private var flag: Bool\n    init() { _flag = State(initialValue: true) }\n}"
        )
        self.assertEqual(guard.scan_source(other_type), [])

    def test_ignores_comments(self) -> None:
        for source in [
            "struct V {\n    @State private var flag = false\n    init() { // _flag = State(initialValue: true)\n    }\n}",
            "struct V {\n    @State private var flag = false\n    init() { /* _flag = State(initialValue: true) */ }\n}",
            "struct V {\n    @State private var flag = false\n    init() { /* a /* b */ _flag = State(initialValue: true) */ }\n}",
            "struct V {\n    // @State private var flag = false\n    @State private var flag: Bool\n    init() { _flag = State(initialValue: true) }\n}",
        ]:
            self.assertEqual(guard.scan_source(source), [], source)

    def test_comment_markers_inside_strings_hide_nothing(self) -> None:
        source = (
            'struct V {\n    @State private var glob = "*/"\n    @State private var flag = false\n'
            '    init() { let u = "https://x/*"; _flag = State(initialValue: true) }\n}'
        )
        self.assertEqual(guard.scan_source(source), [(3, "flag")])

    def test_comment_markers_inside_any_string_hide_nothing(self) -> None:
        decl = "    @State private var flag = false\n"
        assign = "    init() { _flag = State(initialValue: true) }\n"
        for before in [
            '    let a = """\n    /* not a comment\n    """\n',
            '    let a = #"""\n    /* not a comment\n    """#\n',
            '    let a = #"a "quote" // not a comment"#\n',
            '    let a = "\\(x ? "/*" : "y")"\n',
            '    let a = #"""x"#\n',
            '    let a = ##"""x"##\n',
            '    let a = #/[/][*] /*/#\n',
            '    let a = #/a\\/#[/][*] /*/#\n',
            '    let a = ##/a\\/##[/][*] /*/##\n',
        ]:
            source = "struct V {\n" + before + decl + assign + "}"
            self.assertEqual([name for _, name in guard.scan_source(source)], ["flag"], before)
        source = "struct V {\n" + decl + '    init() { let a = #"x // y"#; _flag = State(initialValue: true) }\n}'
        self.assertEqual([name for _, name in guard.scan_source(source)], ["flag"])

    def test_assignment_text_inside_a_string_is_not_an_assignment(self) -> None:
        for literal in ['"_flag = State("', '"""\n_flag = State(\n"""', '#"_flag = State("#', '#/a\\/#_flag = State(true)/#']:
            source = f"struct V {{\n    @State private var flag = false\n    let s = {literal}\n}}"
            self.assertEqual(guard.scan_source(source), [], literal)

    def test_ignore_marker_must_be_a_trailing_comment_with_a_reason(self) -> None:
        assign = "\n    init() { _flag = State(initialValue: true) }\n}"
        for declaration in [
            '@State private var flag = "state-init-ignore: no"',
            "@State private var flag = false // see state-init-ignore: rules",
            "@State private var flag = false // state-init-ignore:",
        ]:
            source = "struct V {\n    " + declaration + assign
            self.assertEqual([name for _, name in guard.scan_source(source)], ["flag"], declaration)
        source = "struct V {\n    @State private var flag = #/ // state-init-ignore: no /# != nil" + assign
        self.assertEqual([name for _, name in guard.scan_source(source)], ["flag"], "marker inside a regex")
        source = "struct V {\n    @State private var flag = false // state-init-ignore: B owns it" + assign
        self.assertEqual(guard.scan_source(source), [])

    def test_comparisons_with_state_are_not_a_generic_initializer(self) -> None:
        source = (
            "struct V {\n    @State private var flag = false\n    @State private var count = 0\n"
            "    init(State: Int) {\n        _flag = State < 2\n        _count = .init(initialValue: 3)\n"
            "        let marker = 3 > (2)\n    }\n}"
        )
        self.assertEqual(guard.scan_source(source), [(3, "count")])

    def test_a_later_greater_than_does_not_close_a_comparison(self) -> None:
        for statements in [
            "_flag = State < 2\n        print(3 > (2))",
            "_flag = State < x\n        foo > (y)",
        ]:
            source = (
                "struct V {\n    @State private var flag = false\n    init(State: Int, x: Int, y: Int) {\n"
                "        " + statements + "\n    }\n}"
            )
            self.assertEqual(guard.scan_source(source), [], statements)

    def test_long_whitespace_after_state_scans_quickly(self) -> None:
        source = "@State private var flag = false\ninit() { _flag = State" + " " * 16000 + "< 2 }"
        start = time.monotonic()
        guard.scan_source(source)
        self.assertLess(time.monotonic() - start, 0.05)

    def test_many_unclosed_generics_scan_quickly(self) -> None:
        body = "    _flag = State < 2\n" * 2000
        source = "struct V {\n    @State private var flag = false\n    init(State: Int) {\n" + body + "    }\n}"
        start = time.monotonic()
        guard.scan_source(source)
        self.assertLess(time.monotonic() - start, 0.1)

    def test_long_comment_scans_quickly(self) -> None:
        source = "@State " + "a " * 200 + "\n" + "@State /*" + " x" * 5000 + "*/ var y = 1\n"
        start = time.monotonic()
        guard.scan_source(source)
        self.assertLess(time.monotonic() - start, 1.0)

    def test_many_line_comments_scan_quickly(self) -> None:
        source = "// note\n" * 20000 + "@State private var flag = false\n"
        start = time.monotonic()
        guard.scan_source(source)
        self.assertLess(time.monotonic() - start, 0.1)

    def test_reports_the_declaration_line(self) -> None:
        source = "struct V {\n\n    @State private var flag = false\n    init() { _flag = State(initialValue: true) }\n}"
        self.assertEqual(guard.scan_source(source), [(3, "flag")])

    def test_passes_without_default_or_without_init_assignment(self) -> None:
        for source in [
            "@State private var flag: Bool\ninit() { _flag = State(initialValue: true) }",
            "@State private var flag = false\ninit() { _other = State(initialValue: true) }",
            "@State private var flag = false",
            "@State private var flag: Bool { true }\ninit() { _flag = State(initialValue: true) }",
            "@State private var flag = false\nfunc f() { let _flag = State(initialValue: true) }",
            "@State private var flag = false\ninit(input: Bool) { let _flag: Set<Bool>\n _flag = .init([input]) }",
            "@State private var flag: [\n    String: Bool\n]\ninit() { _flag = State(initialValue: [:]) }",
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

    def test_every_scan_root_is_checked(self) -> None:
        # Listed here rather than read from the guard, so dropping a root fails.
        for scan_dir in ["iosApp/iosApp", "iosApp/TopShelf", "iosApp/NotificationService", "iosApp/DownloadsActivity"]:
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / scan_dir).mkdir(parents=True)
                (root / scan_dir / "View.swift").write_text(
                    "@State private var flag = false\ninit() { _flag = State(initialValue: true) }\n"
                )
                result = self.run_guard(root)
                self.assertEqual(result.returncode, 1, scan_dir)
                self.assertIn(f"{scan_dir}/View.swift:1: @State var flag", result.stdout)


if __name__ == "__main__":
    unittest.main()
