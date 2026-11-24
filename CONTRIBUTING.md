# Contributing to Auger

> [!IMPORTANT]
> The most helpful way to contribute right now is a clear, accurate [issue](https://github.com/Artic0din/silo-apple/issues).
> Pull requests are welcome when a maintainer asks for one.

## Why we ask for issues

Pull requests take time to review, verify against work already in flight, and own after merge.
Writing the change from a precise issue keeps every change on one workflow with the same tests and checks.
This applies whether or not you used AI.

## Write a useful issue

Open an [issue](https://github.com/Artic0din/silo-apple/issues) for bugs or feature requests in the Apple TV (tvOS) app.
This fork focuses on tvOS and drops iOS and macOS work.
Problems with the server or its API belong in [silo-server](https://github.com/Silo-Server/silo-server/issues/new/choose), not here.
Search existing issues first and add new details to an open issue rather than filing a duplicate.

Include the details needed to reproduce or evaluate the request:

- One problem or proposal per issue.
- Describe what you observed before any theory about the cause.
- Give exact steps to reproduce, expected and actual behavior, the app version and build, your Apple TV model and tvOS version, and the Silo server version.
- Paste raw logs rather than a summary.
  Redact credentials, tokens, personal data, and private media details, mark each redaction, and leave the rest untouched.
- For a feature request, describe the problem it solves and who it affects.
- If you found the cause or have a fix in mind, add it under a `Technical notes` heading separate from what you observed.
  Point to the files involved.
- Note if you used AI to draft or investigate the issue.

## Pull requests

Pull requests are welcome when a maintainer asks for one, usually in an issue comment.
If a problem matters and no maintainer has asked for a pull request, open an [issue](https://github.com/Artic0din/silo-apple/issues) instead.

When you open an invited pull request:

- Keep one concern per pull request.
- Use a Conventional Commit title (`feat`, `fix`, `refactor`, `perf`, `docs`, `test`, `chore`, `ci`).
- Link the issue it addresses.
- Fill in the pull request description with the problem, the approach, actual validation results, and any AI disclosure.
- Include evidence that the change works (see [Show visible changes](#show-visible-changes)).

## Development setup

Read [README.md](README.md) for prerequisites, signing setup, and build commands.
Regenerate `iosApp/Silo.xcodeproj` from `iosApp/project.yml` with `xcodegen generate` instead of hand-editing the generated project.

## Validate your change

Build and test the tvOS app before opening or updating a pull request.
The project and schemes still use the upstream `Silo` names until the app rebrand is complete:

```sh
cd iosApp
xcodegen generate
xcodebuild build \
  -project Silo.xcodeproj \
  -scheme SiloTV \
  -destination 'platform=tvOS Simulator,name=Apple TV 4K (3rd generation)' \
  CODE_SIGN_IDENTITY='' CODE_SIGNING_ALLOWED=NO
xcodebuild test \
  -project Silo.xcodeproj \
  -scheme SiloTV \
  -destination 'platform=tvOS Simulator,name=Apple TV 4K (3rd generation)' \
  CODE_SIGNING_ALLOWED=YES CODE_SIGN_IDENTITY=-
```

Simulator tests use ad-hoc signing so Keychain-dependent tests have an application identity.
They do not require a distribution certificate.
Exercise visible changes on an Apple TV simulator or device.

## Show visible changes

Every pull request shows evidence that the change works so reviewers can inspect it without building the branch.

- For UI, layout, focus, copy, metadata, artwork, or playback changes, attach before-and-after screenshots of the same screen and data on Apple TV under the pull request's **Evidence** heading.
  Add a short recording when motion, timing, or focus movement matters.
  Name the simulator or Apple TV model and the commit SHA for each capture.
- For non-visible changes such as refactors, CI, or tests, paste the commands you ran, the commit SHA, and trimmed test results.

Capture against a test library or public-domain media where you can.
Everything attached on GitHub is public, so crop or blur hostnames, URLs, account names, tokens, passwords, and personal media details.

## Licensing of contributions

This project is licensed under `AGPL-3.0-or-later` with two additional permissions: the App Store and DRM permission in [APPSTORE-EXCEPTION.md](APPSTORE-EXCEPTION.md) and the platform library permission in [PLATFORM-EXCEPTION.md](PLATFORM-EXCEPTION.md).

By submitting a contribution, you agree that it is licensed under those same terms, including both additional permissions, and that the project may distribute builds containing your contribution through application stores such as the Apple App Store and TestFlight as the App Store permission describes.
If you cannot agree to an additional permission, say so in your pull request before it is merged.

You retain copyright in your contribution.
No copyright assignment is requested.

## Practical notes

- Repository layout, build commands, and tvOS notes are in [README.md](README.md) and `docs/` (including [docs/tvos-focus.md](docs/tvos-focus.md)).
- Third-party components and their licenses are listed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
  Update it when a dependency changes.
- Coding agents must read [AGENTS.md](AGENTS.md) before changing the repository.
