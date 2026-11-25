# Sideloading (Unsigned tvOS IPA) Builds

The **Sideload IPA Build** workflow (`.github/workflows/sideload-ipa.yml`) produces an **unsigned** tvOS IPA (`Auger-unsigned.ipa`).
Users re-sign it with their own Apple account and sideload it onto Apple TV using Xcode, AltServer, atvloadly, or similar tools.
This is separate from the TestFlight pipeline ([ci-release.md](ci-release.md)).

## How it differs from the TestFlight build

- **No signing.** The archive is built with `CODE_SIGNING_ALLOWED=NO`; the IPA is `Payload/Auger.app` zipped.
- **No secrets.** No Match repo, distribution certificate, or App Store Connect key is read.
- **No upload.** Artifacts are attached to the workflow run and published to a GitHub prerelease.
- **No user-independent keychain.** The sideload lane sets `SILO_USER_INDEPENDENT_KEYCHAIN=NO` because unsigned archives lack Apple's User Management entitlement and re-signers generally cannot grant it.

## How it triggers

Manual: Actions -> **Sideload IPA Build** -> Run workflow -> enter `version`.
The run validates `version` via `scripts/ci/resolve-marketing-version.sh`, mints a `v<version>-build.<run>` tag, publishes the matching `Auger-source-<commit>.tar.gz` archive, and attaches `Auger-unsigned.ipa` to the prerelease.

## Telling two sideload builds apart

Each run stamps `CFBundleVersion` from `github.run_number` so every sideloaded IPA is distinguishable from other builds of the same marketing version.
The unsigned lane also sets `SILO_BUILD_CHANNEL=sideload`, which Auger reports to the Silo server as `X-Silo-Client-Channel`.

## Fastlane lane

```sh
bundle exec fastlane ios ipa_tvos_unsigned    # -> build/tvos-unsigned/Auger-unsigned.ipa
```

Runs locally with no signing credentials.

## Caveats for users

- **Re-signing changes entitlements.** Personal/free Apple accounts remap the keychain-sharing group and App Groups to the user's team prefix, so Top Shelf rows may stay empty.
- **Free accounts expire in 7 days** and are limited to 3 active apps; a paid Apple Developer account lasts about 1 year.
- **Apple TV needs a host machine.** Pair Apple TV with a Mac (Xcode / AltServer) or a Linux host running `atvloadly` over the network, and keep the host reachable for refreshes.
- **Top Shelf extension.** `AugerTopShelf` is embedded in `Auger.app`. Re-signers who cannot sign extensions on a free account can strip it before installing.
- **Shared sign-in across Apple TV users.** Without Apple's User Management entitlement, all Apple TV profiles share one Auger sign-in and profile choice.
