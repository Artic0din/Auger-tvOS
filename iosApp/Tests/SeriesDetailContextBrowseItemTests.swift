import Foundation
import XCTest
@testable import Silo

/// A catalog item resolves its series context directly, by the same rule
/// the Home section item applies.
final class SeriesDetailContextBrowseItemTests: XCTestCase {
    func testBrowseItemResolvesOnlyEpisodesWithAParentSeries() throws {
        let episode = SeriesDetailContext(seriesContentId: "series-1", episodeContentId: "item-1", seasonNumber: 2)
        let cases: [(String, [String: Any], SeriesDetailContext?)] = [
            ("movie", ["type": "movie"], nil),
            ("series", ["type": "series", "seriesId": "series-1"], nil),
            ("episode", ["type": "episode", "seriesId": "series-1", "seasonNumber": 2, "episodeNumber": 3], episode),
            ("upper-case type", ["type": "Episode", "seriesId": "series-1", "seasonNumber": 2], episode),
            ("trimmed series id", ["type": "episode", "seriesId": " series-1 ", "seasonNumber": 2], episode),
            ("episode number on another type", ["type": "special", "seriesId": "series-1", "seasonNumber": 2, "episodeNumber": 1], episode),
            ("blank series id", ["type": "episode", "seriesId": "  "], nil),
            ("own series id", ["type": "episode", "seriesId": "item-1"], nil),
        ]
        for (name, fields, expected) in cases {
            let item = try browseItem(fields)
            XCTAssertEqual(SeriesDetailContext(browseItem: item), expected, name)
            XCTAssertEqual(SeriesDetailContext(item: SectionItem(browseItem: item)), expected, name)
        }
    }

    private func browseItem(_ fields: [String: Any]) throws -> BrowseItem {
        var all = fields
        all["contentId"] = "item-1"
        all["title"] = "Item"
        return try JSONDecoder().decode(BrowseItem.self, from: JSONSerialization.data(withJSONObject: all))
    }
}
