#if !os(tvOS)
import Foundation
import XCTest
@testable import Silo

/// Each Home row type keeps its card shape now that the flags are worked out
/// once per row.
@MainActor
final class HomeFeedRowCardStyleTests: XCTestCase {
    func testResumeRowUsesStills() throws {
        let section = try makeSection(type: "continue_watching", itemTypes: ["movie", "episode"])
        let style = HomeFeedRow.CardStyle(section)

        XCTAssertTrue(style.usesStills)
        XCTAssertTrue(style.isResume)
        XCTAssertFalse(style.isAudiobookRow)
        try assertArtwork(in: section, size: HomeStillCard.artworkSize(width: stillWidth))
    }

    func testNextUpEpisodeRowUsesStillsWithoutResume() throws {
        let section = try makeSection(type: "next_up", itemTypes: ["episode"])
        let style = HomeFeedRow.CardStyle(section)

        XCTAssertTrue(style.usesStills)
        XCTAssertFalse(style.isResume)
        try assertArtwork(in: section, size: HomeStillCard.artworkSize(width: stillWidth))
    }

    func testAudiobookResumeRowKeepsSquarePosters() throws {
        let section = try makeSection(type: "continue_watching", itemTypes: ["audiobook", "audiobook"])
        let style = HomeFeedRow.CardStyle(section)

        XCTAssertFalse(style.usesStills)
        XCTAssertTrue(style.isAudiobookRow)
        XCTAssertTrue(style.isResume)
        try assertArtwork(
            in: section,
            size: HomePosterCard.artworkSize(width: HomeFeedRow.posterWidth, aspect: .square)
        )
    }

    func testPlainRowUsesPosters() throws {
        let section = try makeSection(type: "recently_added", itemTypes: ["movie", "series"])
        let style = HomeFeedRow.CardStyle(section)

        XCTAssertFalse(style.usesStills)
        XCTAssertFalse(style.isAudiobookRow)
        XCTAssertFalse(style.isResume)
        try assertArtwork(
            in: section,
            size: HomePosterCard.artworkSize(width: HomeFeedRow.posterWidth, aspect: .poster)
        )
    }

    private var stillWidth: CGFloat {
        HomeFeedMetrics.stillWidth * UICustomizationPreferences.shared.cardPresentation.posterSize.scale
    }

    private func assertArtwork(in section: ResolvedSection, size: CGSize, line: UInt = #line) throws {
        for item in section.items {
            let artwork = try XCTUnwrap(HomeFeedRow.cardArtwork(for: item, in: section), line: line)
            XCTAssertEqual(artwork.pointSize, size, line: line)
        }
    }

    private func makeSection(type: String, itemTypes: [String]) throws -> ResolvedSection {
        let items = try itemTypes.enumerated().map { index, itemType in
            let fields: [String: Any] = [
                "contentId": "item-\(index)",
                "type": itemType,
                "title": "Item \(index)",
                "posterUrl": "https://example.invalid/poster-\(index).jpg",
                "backdropUrl": "https://example.invalid/backdrop-\(index).jpg",
            ]
            return try JSONDecoder().decode(SectionItem.self, from: JSONSerialization.data(withJSONObject: fields))
        }
        return ResolvedSection(
            id: type,
            sectionType: type,
            title: type,
            featured: false,
            itemLimit: nil,
            totalCount: items.count,
            isCustom: false,
            customized: false,
            items: items
        )
    }
}
#endif
