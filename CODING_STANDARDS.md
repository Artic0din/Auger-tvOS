# Coding Standards

Judgement rules a reviewer applies to every diff.
Mechanical rules live in `scripts/ci/` and run in CI; they are not repeated here.
Report each violation as `file:line`, the rule, and the fix.

## Tests

- **Fixed expectations.**
  A test asserts against literal expected values written in the test.
  A test whose only check compares the new code with another code path computing the same answer (for example the old implementation, or the same helper called twice) passes whenever both are wrong, so it protects nothing.
  An equivalence check between two paths is fine beside at least one fixed-value assertion.
- **Red before green.**
  A bug-fix test must fail on the code before the fix.
  Ask the author how they saw it fail when the PR doesn't say.

## SwiftUI identity

- **Stable row identity.**
  A `ForEach` over data that can be replaced, filtered, reordered or deduplicated while on screen, or whose rows keep focus or `@State`, is keyed by a value unique to each element and stable across reloads.
  `id: \.offset` and fields that can repeat (a chapter number, a title) fail that test.
  A short list built once for display only, such as fact chips or rating badges, may key by offset.
