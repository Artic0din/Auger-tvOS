import SwiftUI

/// The Auger startup splash shown briefly over the app while initial state loads.
/// Uses the native `AugerMark` and `AugerWordmark` vector assets and honors Reduce Motion.
struct StartupSplashView: View {
    private static let displayDuration: Duration = .milliseconds(1600)

    let onFinished: () -> Void

    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var revealed = false

    var body: some View {
        ZStack {
            Color.siloBackground.ignoresSafeArea()

            HStack(spacing: 28) {
                Image("AugerMark")
                    .resizable()
                    .scaledToFit()
                    .frame(height: markHeight)
                    .scaleEffect(isShown ? 1 : 0.88)
                    .opacity(isShown ? 1 : 0)

                Image("AugerWordmark")
                    .resizable()
                    .scaledToFit()
                    .frame(height: wordmarkHeight)
                    .offset(x: isShown ? 0 : -18)
                    .opacity(isShown ? 1 : 0)
            }
            .animation(reduceMotion ? nil : .easeOut(duration: 0.55), value: revealed)
        }
        .accessibilityLabel(.shellSplashLoading)
        .task {
            revealed = true
            try? await Task.sleep(for: reduceMotion ? .milliseconds(800) : Self.displayDuration)
            guard !Task.isCancelled else { return }
            onFinished()
        }
    }

    private var isShown: Bool {
        reduceMotion || revealed
    }

    private var markHeight: CGFloat {
        #if os(tvOS)
        return 84
        #else
        return 56
        #endif
    }

    private var wordmarkHeight: CGFloat {
        #if os(tvOS)
        return 58
        #else
        return 38
        #endif
    }
}

extension EnvironmentValues {
    /// True while the startup splash covers the app being built underneath it.
    @Entry var isStartupSplashVisible = false
}
