# Repository Guidelines

Auger is a standalone third-party Apple TV (tvOS) client for Silo servers.
Change what the task needs, leave unrelated structure intact, and report nearby problems instead of making drive-by edits.

## Project Structure & Module Organization

SwiftUI app code lives under `iosApp/iosApp/` (with Apple TV views in `iosApp/iosApp/tvOS/`), unit tests live in `iosApp/Tests/`, the tvOS Top Shelf extension lives in `iosApp/TopShelf/`, shared resources and bundled licenses live in `iosApp/Resources/`, and generated Xcode structure is controlled by `iosApp/project.yml`.
Playback notes live in `docs/tvos-player/`, tvOS focus guidance lives in `docs/tvos-focus.md`, release documentation lives in `docs/release/`, and release automation lives in `fastlane/`.

## Server Compatibility Boundary

Auger talks to self-hosted Silo servers over `/api/v2`.
Keep wire-protocol names that Silo Server expects unchanged: Bonjour service types (`_silopair._tcp`, `_silocast._tcp`, `_silo._tcp`), HTTP headers (`X-Silo-Client`, `X-Silo-Client-Version`, `X-Silo-Client-Channel`), the native OAuth callback scheme (`org.siloserver.silo`), and incoming `silo://` deep-link compatibility alongside Auger's own `auger://` scheme.
Auger identifies itself as `X-Silo-Client: Auger`, uses the `com.artic0din.auger` identifier namespace (`com.artic0din.auger.topshelf`, `group.com.artic0din.auger`, `com.artic0din.auger.shared`), and sends diagnostics only to the user's own Silo server (never to a third-party hosted collector).

## Build, Test, and Development Commands

- `cd iosApp && xcodegen generate` regenerates `Auger.xcodeproj` from `project.yml`.
  Run this after target, signing, or source layout changes instead of hand-editing generated `.xcodeproj` files.
- Build unsigned for tvOS simulator:
  `xcodebuild build -project Auger.xcodeproj -scheme Auger -destination 'platform=tvOS Simulator,name=Apple TV 4K (3rd generation)' CODE_SIGN_IDENTITY='' CODE_SIGNING_ALLOWED=NO`
- Run unit tests on tvOS simulator (ad-hoc signed for Keychain tests):
  `xcodebuild test -project Auger.xcodeproj -scheme Auger -destination 'platform=tvOS Simulator,name=Apple TV 4K (3rd generation)' CODE_SIGN_ALLOWED=YES CODE_SIGN_IDENTITY=-`
- Unsigned compilation with `CODE_SIGNING_ALLOWED=NO` is compile-only evidence; do not install that artifact for an authenticated simulator run.
- See `docs/mac-builder.md` if building on a remote Mac host.

## Coding Style & Naming Conventions

Use Swift 5 and SwiftUI naming conventions.
Types use `PascalCase`; functions and properties use `camelCase`.
Keep Apple TV UI under `iosApp/iosApp/tvOS/` and update `iosApp/project.yml` for any target or resource changes.

For tvOS focus work, read `docs/tvos-focus.md` before editing navigation, menus, grids, or custom controls.
Prefer a stable native focus graph or a single composite focus owner; do not mix row-level focusable controls with manual directional focus mutation.

All user-facing copy in paths listed in `scripts/ci/catalog-text-paths.txt` must come from `iosApp/iosApp/Localizable.xcstrings` and be verified by `python3 scripts/ci/check-catalog-text.py` and `bash scripts/ci/check-string-localized.sh`.

## Testing Guidelines

Tests use XCTest under `iosApp/Tests/` (`AugerTests`, with `-module-alias Silo=Auger`).
Add focused regression tests when they protect changed behavior, and use rendered checks on an Apple TV simulator or device for visual changes.
Avoid tests that only mirror wording or implementation.
Also run the CI script checks in `.github/workflows/ci-scripts.yml` when touching CI scripts, Fastlane lanes, or localization/API guards.

## Writing

Run a final readability pass on every human-facing issue, pull request, document, or status update.

- Lead with the outcome.
- Use concrete, plain language and active voice.
- Cut filler, stock framing, repetition, and promotional claims.
- Preserve meaning, evidence, citations, uncertainty, and established terminology.
- Never rewrite exact quotations, commands, logs, identifiers, API names, or contractual language.

## Pull requests

Never create a pull request unless the developer explicitly asks for one.

Use a Conventional Commit title in plain language.
Start the body with the problem, explain the solution next, and include linked issues, validation evidence, risks, and follow-up work.

- Keep one concern per pull request.
- Every pull request must include evidence: before-and-after Apple TV captures (and a short recording when motion, timing, or focus matters) for visible changes, or the exact commands, commit SHA, and trimmed test results for non-visible changes.
- Check media for private information before attaching it to GitHub, and never commit PR-only assets to the repository.

## Security & Configuration Tips

Do not commit local signing overrides.
Start from `iosApp/Signing/Local.xcconfig.sample`, create `iosApp/Signing/Local.xcconfig`, and regenerate with XcodeGen after signing changes.
Keep App Store Connect keys, Match repo URLs, and team identifiers in environment variables only.
