import Foundation

/// Auger's custom URL scheme for Top Shelf items and in-app deep links.
///
/// Server-generated links may still use the `silo://` scheme, so both `auger`
/// and `silo` are accepted when parsing incoming URLs while Auger emits
/// `auger://` for its own links.
enum SiloURLScheme {
    static let current = "auger"
    static let compatible = "silo"

    static func isAppURL(_ url: URL) -> Bool {
        guard let scheme = url.scheme?.lowercased() else { return false }
        return scheme == current || scheme == compatible
    }
}
