# Mac Builder: Building and Testing Auger from a Remote Host

Xcode runs on macOS only.
When developing from a Linux workstation, Auger can be built and tested on a dedicated Mac ("mac-builder") over SSH and XcodeBuildMCP.

Placeholders used throughout:

| Placeholder | Meaning | Example |
|---|---|---|
| `mac-builder` | SSH host alias for the Mac | any alias you choose |
| `<mac-user>` | macOS account name on the Mac | `builder` |
| `<TEAM_ID>` | Apple Developer team ID | `ABCDE12345` |
| `<DEVICE_ID>` | `devicectl` device UUID | discover it dynamically, never hardcode |

## Architecture

```text
Workstation                                         Mac mini (Xcode)
───────────                                         ────────────────
source of truth  ──── rsync / git apply ──────────►  ~/auger-deploy
agent / editor   ──── ssh (stdio) ────────────────►  xcodebuildmcp  ──► xcodebuild
                                                                    ──► xcrun devicectl ──► Apple TV
                 ──── ssh (ad hoc) ───────────────►  shell for signing, logs, devicectl
```

Two independent channels reach the Mac:

1. **XcodeBuildMCP over SSH** for build, test, install, launch, simulator control, UI automation, and LLDB.
2. **Ad-hoc `ssh mac-builder '<command>'`** for `xcodegen`, keychain unlocking, reading raw build logs, and `devicectl --console`.

Keep the workstation as the source of truth for git history and commits.
Treat the Mac checkout as disposable build scratch.

## One-time setup

### On the Mac

```bash
# Xcode from the App Store or developer.apple.com, then:
sudo xcodebuild -license accept
sudo xcode-select -s /Applications/Xcode.app/Contents/Developer

brew install node xcodegen
npm install -g xcodebuildmcp        # lands at /opt/homebrew/bin/xcodebuildmcp

# Enable Remote Login (SSH):
sudo systemsetup -setremotelogin on
```

Enable Developer Mode on each physical Apple TV you deploy to, and pair it to the Mac once through Xcode -> Devices and Simulators.

### On the Linux host

`~/.ssh/config`:

```text
Host mac-builder
  HostName <mac>.<tailnet>.ts.net
  User <mac-user>
  IdentityFile ~/.ssh/id_ed25519_macbuilder
  IdentitiesOnly yes
  StrictHostKeyChecking yes
```

Push the public key with `ssh-copy-id` and confirm `ssh mac-builder true` succeeds without a prompt.

Create a wrapper script `~/.local/bin/xcodebuildmcp-mac`:

```sh
#!/bin/sh
set -eu

exec ssh \
  -T \
  -o BatchMode=yes \
  -o ConnectTimeout=10 \
  -o ServerAliveInterval=30 \
  -o ServerAliveCountMax=3 \
  -o LogLevel=ERROR \
  mac-builder \
  env \
  PATH=/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin \
  XCODEBUILDMCP_ENABLED_WORKFLOWS=simulator,simulator-management,device,debugging,ui-automation,xcode-ide,project-discovery,coverage,swift-package \
  /opt/homebrew/bin/xcodebuildmcp \
  mcp
```

`chmod +x ~/.local/bin/xcodebuildmcp-mac`, then register it with your MCP client.

## Syncing source to the Mac

Full sync:

```bash
rsync -az --delete \
  --exclude 'DerivedData' --exclude 'build' \
  /path/to/silo-apple/ mac-builder:~/auger-deploy/

ssh mac-builder 'cd ~/auger-deploy && git log --oneline -1 && git status --short | wc -l'
```

Confirm the commit and dirty-file count match your local tree before trusting any build result.

Regenerate the Xcode project after syncing:

```bash
ssh mac-builder 'cd ~/auger-deploy/iosApp && /opt/homebrew/bin/xcodegen generate'
```

## Session defaults

```jsonc
{
  "projectPath": "/Users/<mac-user>/auger-deploy/iosApp/Auger.xcodeproj",
  "scheme": "Auger",
  "simulatorId": "<tvos-sim-uuid>",
  "configuration": "Debug"
}
```

Discover simulator and device UUIDs dynamically with `list_sims` or `xcrun devicectl list devices`.

## Build and test recipes

### Simulator

Normal simulator builds use local signing and embed simulated entitlements so Keychain-backed sessions persist across launches.

### Compile-only check without signing

```bash
ssh mac-builder 'cd ~/auger-deploy/iosApp && \
  xcodebuild build -project Auger.xcodeproj -scheme Auger \
  -destination "generic/platform=tvOS" CODE_SIGNING_ALLOWED=NO 2>&1 \
  | grep -E "error:|BUILD (SUCCEEDED|FAILED)"'
```

Treat `CODE_SIGNING_ALLOWED=NO` output as compile-only evidence.
Do not install an unsigned product for authenticated simulator testing.

### Physical Apple TV

Unlock the keychain and build inside a single SSH command because `security unlock-keychain` does not persist across separate SSH sessions:

```bash
ssh mac-builder 'security unlock-keychain -p "$KEYCHAIN_PASSWORD" ~/Library/Keychains/login.keychain-db && \
  cd ~/auger-deploy/iosApp && \
  xcodebuild build -project Auger.xcodeproj -scheme Auger \
    -destination "id=<DEVICE_ID>" \
    -derivedDataPath ~/auger-build-tvos \
    DEVELOPMENT_TEAM=<TEAM_ID> -allowProvisioningUpdates 2>&1 | tail -30'
```

Install and launch:

```bash
ssh mac-builder 'xcrun devicectl device install app --device <DEVICE_ID> \
  ~/auger-build-tvos/Build/Products/Debug-appletvos/Auger.app'

ssh mac-builder 'xcrun devicectl device process launch --device <DEVICE_ID> com.artic0din.auger'
```

### Capturing `print()` from a device

```bash
ssh mac-builder 'nohup xcrun devicectl device process launch \
  --device <DEVICE_ID> --console com.artic0din.auger \
  >> /tmp/auger-run.log 2>&1 </dev/null & disown'
```

## Signing and keychain notes

If `codesign` fails with `User interaction is not allowed` after unlocking, update the key partition list:

```bash
ssh mac-builder 'security unlock-keychain -p "$KEYCHAIN_PASSWORD" ~/Library/Keychains/login.keychain-db && \
  security set-key-partition-list -S apple-tool:,apple:,codesign: -s \
    -k "$KEYCHAIN_PASSWORD" ~/Library/Keychains/login.keychain-db'
```

Keep keychain passwords in environment variables or the host keychain, never inline in commands or commits.

For local personal-team signing overrides, copy `iosApp/Signing/Local.xcconfig.sample` to `iosApp/Signing/Local.xcconfig` (gitignored) and run `xcodegen generate`.

## Quick reference

| Path / value | What |
|---|---|
| `~/auger-deploy` | Deploy checkout on the Mac (build scratch, never edit) |
| `~/auger-deploy/iosApp/Auger.xcodeproj` | Generated Xcode project |
| `~/auger-build-tvos` | Stable tvOS derived-data path |
| `/opt/homebrew/bin/xcodebuildmcp`, `/opt/homebrew/bin/xcodegen` | Tooling (Homebrew is not on non-interactive `PATH`) |
| `Auger` | tvOS scheme |
| `com.artic0din.auger` | Default bundle ID (override in `Local.xcconfig`) |
