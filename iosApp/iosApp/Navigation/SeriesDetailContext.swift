import Foundation

/// Selection carried into the single Series page from a season or episode link.
struct SeriesDetailContext: Hashable {
    let seriesContentId: String
    let episodeContentId: String?
    let seasonNumber: Int?

    init(seriesContentId: String, episodeContentId: String?, seasonNumber: Int?) {
        self.seriesContentId = seriesContentId
        self.episodeContentId = episodeContentId
        self.seasonNumber = seasonNumber
    }

    init?(item: SectionItem) {
        self.init(
            type: item.type, episodeNumber: item.episodeNumber, seriesId: item.seriesId,
            contentId: item.contentId, seasonNumber: item.seasonNumber
        )
    }

    init?(browseItem item: BrowseItem) {
        self.init(
            type: item.type, episodeNumber: item.episodeNumber, seriesId: item.seriesId,
            contentId: item.contentId, seasonNumber: item.seasonNumber
        )
    }

    private init?(type: String, episodeNumber: Int?, seriesId: String?, contentId: String, seasonNumber: Int?) {
        guard type.lowercased() == "episode" || episodeNumber != nil,
              let seriesId = Self.parentID(seriesId, childID: contentId) else { return nil }
        self.init(seriesContentId: seriesId, episodeContentId: contentId, seasonNumber: seasonNumber)
    }

    init?(detail: ItemDetail) {
        guard detail.type == "episode" || detail.type == "season",
              let seriesId = Self.parentID(detail.seriesId, childID: detail.contentId) else { return nil }
        self.init(
            seriesContentId: seriesId,
            episodeContentId: detail.type == "episode" ? detail.contentId : nil,
            seasonNumber: detail.seasonNumber
        )
    }

    private static func parentID(_ value: String?, childID: String) -> String? {
        guard let value = value?.trimmingCharacters(in: .whitespacesAndNewlines),
              !value.isEmpty, value != childID else { return nil }
        return value
    }
}
