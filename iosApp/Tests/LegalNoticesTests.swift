import XCTest
@testable import Silo

/// Settings > About legal notices: the build's source link and the bundled
/// license texts behind Open Source Licenses.
final class LegalNoticesTests: XCTestCase {
    func testStampedReleaseArchiveIsTheSourceLink() {
        for tag in ["v1.0.0", "v1.4.0%2Btvos"] {
            let archive = "https://github.com/Artic0din/Auger-tvOS/releases/download/\(tag)/"
                + "Auger-source-\(String(repeating: "a", count: 40)).tar.gz"

            XCTAssertEqual(SiloLegalLinks.sourceURL(stamped: archive).absoluteString, archive)
        }
    }

    func testMissingOrForeignStampLinksTheRepository() {
        let stamps: [String?] = [
            nil,
            "",
            "$(SILO_SOURCE_URL)",
            "http://github.com/Artic0din/Auger-tvOS/releases/download/v1/a.tar.gz",
            "https://example.com/Artic0din/Auger-tvOS/releases/download/v1/a.tar.gz",
            "https://github.com/someone/silo-apple/releases/download/v1/a.tar.gz",
            "https://github.com/Artic0din/Auger-tvOS-fork/releases/download/v1/a.tar.gz",
        ]

        for stamp in stamps {
            XCTAssertEqual(SiloLegalLinks.sourceURL(stamped: stamp), SiloLegalLinks.repository, stamp ?? "nil")
        }
    }

    /// Includes LICENSE and APPSTORE-EXCEPTION.md, which project.yml copies
    /// from the repository root rather than OpenSourceLicenses/.
    func testEveryAcknowledgementResourceIsBundled() {
        for resource in OpenSourceAcknowledgements.resources {
            XCTAssertNotNil(OpenSourceAcknowledgements.resourceURL(for: resource), resource.name)
        }
    }
}
