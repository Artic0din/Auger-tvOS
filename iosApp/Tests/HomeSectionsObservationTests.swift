import Foundation
import Observation
import XCTest
@testable import Silo

/// Home reloads assign a fresh sections array; only a real difference should
/// re-render the feed.
@MainActor
final class HomeSectionsObservationTests: XCTestCase {
    func testAssigningEqualSectionsDoesNotNotify() throws {
        let viewModel = HomeViewModel()
        viewModel.sections = [try makeSection(position: 120)]

        let reloaded = [try makeSection(position: 120)]

        let notified = observesChange(in: viewModel) { viewModel.sections = reloaded }

        XCTAssertFalse(notified)
    }

    func testChangedWatchPositionNotifies() throws {
        let viewModel = HomeViewModel()
        viewModel.sections = [try makeSection(position: 120)]

        let reloaded = [try makeSection(position: 240)]

        let notified = observesChange(in: viewModel) { viewModel.sections = reloaded }

        XCTAssertTrue(notified)
    }

    private func observesChange(in viewModel: HomeViewModel, _ change: () -> Void) -> Bool {
        let notified = ObservationFlag()
        withObservationTracking {
            _ = viewModel.sections
        } onChange: {
            notified.fired = true
        }
        change()
        return notified.fired
    }

    private func makeSection(position: Double) throws -> ResolvedSection {
        let fields: [String: Any] = [
            "contentId": "movie-1",
            "type": "movie",
            "title": "Test Item",
            "positionSeconds": position,
        ]
        let item = try JSONDecoder().decode(
            SectionItem.self,
            from: JSONSerialization.data(withJSONObject: fields)
        )
        return ResolvedSection(
            id: "continue",
            sectionType: "continue_watching",
            title: "Continue Watching",
            featured: false,
            itemLimit: nil,
            totalCount: 1,
            isCustom: false,
            customized: false,
            items: [item]
        )
    }
}

private final class ObservationFlag: @unchecked Sendable {
    var fired = false
}
