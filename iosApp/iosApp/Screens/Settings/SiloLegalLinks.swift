import Foundation

enum SiloLegalLinks {
    static let privacyPolicy = URL(string: "https://github.com/Artic0din/Auger-tvOS/blob/main/PRIVACY.md")!
    static let repository = URL(string: "https://github.com/Artic0din/Auger-tvOS")!

    /// The published source archive for this build. Release lanes stamp it as
    /// `SiloSourceURL`; local builds have none and link the repository.
    static let sourceCode = sourceURL(
        stamped: Bundle.main.object(forInfoDictionaryKey: "SiloSourceURL") as? String
    )

    /// Accepts only a release asset of this repository, so a malformed or
    /// unexpanded stamp still leads to the right source.
    static func sourceURL(stamped: String?) -> URL {
        guard let stamped,
              let url = URL(string: stamped),
              url.scheme == "https",
              url.host == repository.host,
              url.path.hasPrefix(repository.path + "/releases/download/") else {
            return repository
        }
        return url
    }
}
