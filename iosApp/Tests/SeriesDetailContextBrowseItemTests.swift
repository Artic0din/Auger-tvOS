import Foundation
import XCTest
@testable import Silo

/// A catalog item resolves the same series context directly as it does
/// through the Home section item it used to be converted to.
final class SeriesDetailContextBrowseItemTests: XCTestCase {
    func testBrowseItemMatchesSectionItemConversion() throws {
        let cases: [(String, [String: Any])] = [
            ("movie", ["type": "movie"]),
            ("series", ["type": "series"]),
            ("episode", ["type": "episode", "seriesId": "series-1", "seasonNumber": 2, "episodeNumber": 3]),
            ("upper-case episode", ["type": "Episode", "seriesId": "series-1"]),
            ("blank series id", ["type": "episode", "seriesId": "  "]),
            ("own series id", ["type": "episode", "seriesId": "item-1"]),
            ("episode number on another type", ["type": "movie", "seriesId": "series-1", "episodeNumber": 1]),
        ]
        for (name, fields) in cases {
            let item = try browseItem(fields)
            XCTAssertEqual(
                SeriesDetailContext(browseItem: item),
                SeriesDetailContext(item: SectionItem(browseItem: item)),
                name
            )
        }
    }

    func testEpisodeResolvesItsSeriesSeasonAndEpisode() throws {
        let item = try browseItem(["type": "episode", "seriesId": " series-1 ", "seasonNumber": 2])

        XCTAssertEqual(
            SeriesDetailContext(browseItem: item),
            SeriesDetailContext(seriesContentId: "series-1", episodeContentId: "item-1", seasonNumber: 2)
        )
    }

    private func browseItem(_ fields: [String: Any]) throws -> BrowseItem {
        var all = fields
        all["contentId"] = "item-1"
        all["title"] = "Item"
        return try JSONDecoder().decode(BrowseItem.self, from: JSONSerialization.data(withJSONObject: all))
    }
}
