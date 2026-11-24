# CI / TestFlight Release

Releases run from GitHub Actions on `main`.
Each run picks its own version and build number for the tvOS app (`Auger`, bundle identifier `com.artic0din.auger`).

## TestFlight build

Actions -> **TestFlight Release** -> Run workflow, leaving `bump` on `build`.
The very first run has no earlier tag to continue from: enter `1.0.0` as `version`.

The run tags the commit `v1.0.0-beta.66`, publishes a GitHub prerelease with the pull requests merged since the previous build (grouped by label), and uploads tvOS `1.0.0 (66)` to TestFlight's external groups.

TestFlight's "What to Test" uses Claude to summarize those pull request titles into what changed and what to test.
The run sends only section names and titles, never pull request bodies, comments, or code.
If summarization fails or `ANTHROPIC_API_KEY` is unset, the run falls back to the plain list of Features and Fixes.

CI does not run `AugerTests`, and a release does not wait for them.
Run tests locally before starting a release.

The prerelease and its `Auger-source-<commit>.tar.gz` archive are published before the binary because the app links that archive (see `THIRD_PARTY_NOTICES.md`).
Never delete a prerelease whose build shipped.

When distribution succeeds, the run adds a `"TestFlight: distributed ..."` line to the prerelease.
If a run fails before that, use **Re-run failed jobs** to keep the same build number.
To abandon the build instead, delete its GitHub release and tag.
The next run refuses to start while the newest prerelease lacks that line.

## Store release

1. Actions -> **Promote to App Store** -> enter the TestFlight build to ship, such as `v1.0.0-beta.66`.
   It drafts the GitHub release `v1.0.0` on that build's commit, with notes since the last App Store release.
   Nothing is rebuilt.
2. In App Store Connect, add that build to the tvOS version and submit it for review.
3. Start the next version right away: run TestFlight Release with `bump: patch` (fixes only) or `bump: minor` (new features).
4. Edit the draft notes on GitHub, and publish them as the latest release once Apple approves the version.

If App Review rejects the build, delete the draft, fix the problem, and run TestFlight Release with `version: 1.0.0` before promoting the new build.

## Numbers

- `1.0.0` is the marketing version. It stays the same for every TestFlight build until promoted to the App Store.
- `66` is the build number: one more than the latest TestFlight build (and any build already tagged).
- Tags: `vX.Y.Z-beta.B` for TestFlight builds (GitHub prereleases) and `vX.Y.Z` for App Store releases.

## Required repository secrets

| Secret | Purpose |
|---|---|
| `TEAM_ID` | Apple Developer team ID |
| `MATCH_GIT_URL` | Private match certs repo URL |
| `MATCH_PASSWORD` | match encryption passphrase |
| `MATCH_GIT_BASIC_AUTHORIZATION` | base64 `user:token` for read-only HTTPS clone of the certs repo |
| `APP_STORE_CONNECT_API_KEY_KEY_ID` | ASC API key ID |
| `APP_STORE_CONNECT_API_KEY_ISSUER_ID` | ASC API key issuer ID |
| `APP_STORE_CONNECT_API_KEY_KEY` | base64 of the `.p8` key (`base64 < AuthKey_XXX.p8 \| tr -d '\n'`) |
| `TESTFLIGHT_EXTERNAL_GROUPS` | comma-separated external TestFlight group name(s) |
| `ANTHROPIC_API_KEY` | Optional. Claude API key for the What to Test summary; without it the run uses the plain list |

## Renewing signing assets (run locally, not in CI)

CI runs `match` read-only and cannot create certs or profiles.
When a cert expires, a device is added, or entitlements / App IDs change, regenerate locally and push to the certs repo:

```sh
bundle exec fastlane ios sync_signing
```

Then re-run the release workflow.
