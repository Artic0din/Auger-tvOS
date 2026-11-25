import Foundation

/// Auger's custom URL scheme for Top Shelf items and in-app deep links.
///
/// `tvOS-Info.plist` registers only `auger` for OS dispatch so Auger does not
/// collide with another Silo client on the same Apple TV. Links parsed inside
/// Auger still accept both `auger://` and server-generated `silo://` URLs.
enum SiloURLScheme {
    static let current = "auger"
    static let compatible = "silo"

    static func isAppURL(_ url: URL) -> Bool {
        guard let scheme = url.scheme?.lowercased() else { return false }
        return scheme == current || scheme == compatible
    }
}
