# Coding Standards

Judgement rules a reviewer applies to every diff.
Mechanical rules live in `scripts/ci/` and run in CI; they are not repeated here.
Report each violation as `file:line`, the rule, and the fix.

## Tests

- **Independent expectations.**
  A test's expected result comes from outside the code under test: a literal, a fixture, or a direct observation of behaviour such as `XCTAssertTrue(didFinish)`.
  A test whose only check compares the new code with another path computing the same answer (the old implementation, or the same helper called twice) passes whenever both are wrong, so it protects nothing.
  An equivalence check between two paths is fine when the same test also checks that behaviour independently on at least one path; an unrelated assertion such as `XCTAssertNotNil(input)` doesn't count.
- **Shown failing.**
  When a bug-fix PR doesn't say how its test failed before the fix, ask the author for that run.

## SwiftUI identity

- **Stable row identity.**
  A `ForEach` over data that can be replaced, filtered, reordered or deduplicated while on screen, or whose rows keep focus or `@State`, is keyed by a value unique to each element and stable across reloads.
  `id: \.offset` and fields that can repeat (a chapter number, a title) fail that test.
  A short list built once for display only, such as fact chips or rating badges, may key by offset.
