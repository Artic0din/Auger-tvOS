#!/usr/bin/env bash
# Builds and runs the Apple unit tests on a simulator on this Mac.
#
# Regenerates the Xcode project first, so a branch switch or a new test file
# never runs against a stale project. Simulator builds are signed locally
# ("Sign to Run Locally", no developer account): CODE_SIGNING_ALLOWED=NO strips
# the Keychain entitlement and makes every Keychain-backed test fail. Tests run
# in the US region, whose date formats their expected text assumes; the
# language is left alone because some tests change it. Each test has a time
# limit, so one waiting on the network fails instead of hanging the run.
#
# Usage: scripts/apple-test.sh <Silo|SiloTV|SiloMac> [TestClass ...]
#   SILO_SIM_ID          simulator UDID (default: a booted, else any, iPhone or Apple TV)
#   SILO_DERIVED_DATA    DerivedData root (default: ~/Library/Developer/Xcode/DerivedData/silo-<scheme>)
#   SILO_TEST_TIMEOUT    seconds per test (default: 60)
#   SILO_SKIP_TESTS      space-separated Class or Class/testMethod to skip
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
scheme="${1:-}"
[[ $# -gt 0 ]] && shift

case "$scheme" in
  Silo) bundle=SiloTests; platform="iOS Simulator"; runtime=iOS; family=iPhone ;;
  SiloTV) bundle=SiloTVTests; platform="tvOS Simulator"; runtime=tvOS; family="Apple TV" ;;
  SiloMac) bundle=""; platform=macOS; runtime=""; family="" ;;
  *) echo "usage: scripts/apple-test.sh <Silo|SiloTV|SiloMac> [TestClass ...]" >&2; exit 2 ;;
esac

cd "$root/iosApp"
xcodegen generate --quiet

derived="${SILO_DERIVED_DATA:-$HOME/Library/Developer/Xcode/DerivedData/silo-$scheme}"
args=(-project Silo.xcodeproj -scheme "$scheme" -derivedDataPath "$derived")

if [[ "$scheme" == SiloMac ]]; then
  # SiloMac has no test bundle, so a compile-only build is the check.
  exec xcodebuild build "${args[@]}" -destination "platform=macOS" CODE_SIGNING_ALLOWED=NO
fi

# A booted simulator first, so a running one is reused.
sim="${SILO_SIM_ID:-$(xcrun simctl list devices available -j | python3 -c '
import json, sys
runtime, family = sys.argv[1], sys.argv[2]
matches = [
    device
    for key, devices in json.load(sys.stdin)["devices"].items()
    if f".SimRuntime.{runtime}-" in key
    for device in devices
    if family in device["name"]
]
matches.sort(key=lambda device: device["state"] != "Booted")
if matches:
    print(matches[0]["udid"])
' "$runtime" "$family")}"
[[ -n "$sim" ]] || { echo "apple-test: no available $family simulator; set SILO_SIM_ID" >&2; exit 1; }

timeout="${SILO_TEST_TIMEOUT:-60}"
args+=(-destination "platform=$platform,id=$sim"
       -test-timeouts-enabled YES
       -default-test-execution-time-allowance "$timeout"
       -maximum-test-execution-time-allowance "$timeout"
       -testRegion US)

for skipped in ${SILO_SKIP_TESTS:-}; do
  args+=("-skip-testing:$bundle/$skipped")
done

for test_class in "$@"; do
  args+=("-only-testing:$bundle/$test_class")
done

exec xcodebuild test "${args[@]}"
