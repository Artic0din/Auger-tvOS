#!/usr/bin/env bash
# Builds and runs Auger tvOS unit tests on a simulator on this Mac.
#
# Regenerates the Xcode project first, so a branch switch or a new test file
# never runs against a stale project. Simulator builds are signed locally
# ("Sign to Run Locally", no developer account), even when a local xcconfig
# turns signing off: CODE_SIGNING_ALLOWED=NO strips the Keychain entitlement
# and makes every Keychain-backed test fail. Tests run in the US region, whose
# date formats their expected text assumes; the language is left alone because
# some tests change it. Each test has a time limit, so one waiting on the
# network fails instead of hanging the run.
#
# Usage: scripts/apple-test.sh [Auger] [TestClass ...]
#   SILO_SIM_ID          simulator UDID (default: a booted, else any, Apple TV
#                        on a runtime at or above the project's deployment target)
#   SILO_DERIVED_DATA    DerivedData root (default: ~/Library/Developer/Xcode/DerivedData/auger-<scheme>)
#   SILO_TEST_TIMEOUT    seconds per test (default: 60)
#   SILO_SKIP_TESTS      space-separated Class or Class/testMethod to skip
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
scheme="${1:-Auger}"
[[ $# -gt 0 ]] && shift

case "$scheme" in
  Auger) bundle=AugerTests; platform="tvOS Simulator"; runtime=tvOS; family=Apple-TV ;;
  *) echo "usage: scripts/apple-test.sh [Auger] [TestClass ...]" >&2; exit 2 ;;
esac

cd "$root/iosApp"
xcodegen generate --quiet

derived="${SILO_DERIVED_DATA:-$HOME/Library/Developer/Xcode/DerivedData/auger-$scheme}"
# Use the committed Package.resolved as the release lanes do, so a stale
# lockfile fails here rather than at release.
# After changing a package pin in project.yml, refresh and commit the lockfile:
#   (cd iosApp && xcodegen generate && xcodebuild -resolvePackageDependencies -project Auger.xcodeproj -scheme Auger)
args=(-project Auger.xcodeproj -scheme "$scheme" -derivedDataPath "$derived"
      -disableAutomaticPackageResolution -onlyUsePackageVersionsFromResolvedFile)

# Match the device type, not the editable name; a booted simulator first, so a
# running one is reused.
# Skip runtimes older than the deployment target in project.yml.
if [[ -z "${SILO_SIM_ID:-}" ]]; then
  minimum="$(sed -n -E "s/^ *$runtime: *[\"']?([0-9]+(\.[0-9]+)*)[\"']? *(#.*)?$/\1/p" project.yml | head -1)"
  [[ -n "$minimum" ]] || { echo "apple-test: no $runtime deploymentTarget in project.yml; set SILO_SIM_ID" >&2; exit 1; }
fi
sim="${SILO_SIM_ID:-$(xcrun simctl list devices available -j | python3 -c '
import json, re, sys
runtime, family, minimum = sys.argv[1], sys.argv[2], sys.argv[3]
floor = tuple(int(part) for part in minimum.split("."))
prefix = f".SimRuntime.{runtime}-"
matches = [
    device
    for key, devices in json.load(sys.stdin)["devices"].items()
    if prefix in key
    # Keys look like SimRuntime.tvOS-27-2, sometimes with a device suffix.
    and tuple(map(int, re.match(r"(\d+)-(\d+)", key.split(prefix)[1]).groups())) >= floor
    for device in devices
    if device["deviceTypeIdentifier"].rsplit(".", 1)[-1].startswith(family)
]
matches.sort(key=lambda device: device["state"] != "Booted")
if matches:
    print(matches[0]["udid"])
' "$runtime" "$family" "$minimum")}"
[[ -n "$sim" ]] || { echo "apple-test: no available $runtime $minimum+ $family simulator; set SILO_SIM_ID" >&2; exit 1; }

timeout="${SILO_TEST_TIMEOUT:-60}"
args+=(-destination "platform=$platform,id=$sim"
       -test-timeouts-enabled YES
       -default-test-execution-time-allowance "$timeout"
       -maximum-test-execution-time-allowance "$timeout"
       -testRegion US
       CODE_SIGNING_ALLOWED=YES CODE_SIGN_IDENTITY=-)

for skipped in ${SILO_SKIP_TESTS:-}; do
  args+=("-skip-testing:$bundle/$skipped")
done

for test_class in "$@"; do
  args+=("-only-testing:$bundle/$test_class")
done

exec xcodebuild test "${args[@]}"
