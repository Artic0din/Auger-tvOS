import SwiftUI

struct SiloWordmarkView: View {
    var width: CGFloat = 150
    var subtitle: String? = nil

    var body: some View {
        VStack(spacing: 8) {
            Image("AugerWordmark")
                .resizable()
                .scaledToFit()
                .frame(width: width)
                .accessibilityLabel("Auger") // i18n-ignore: brand name

            if let subtitle {
                Text(subtitle)
                    .font(.siloCaption)
                    .foregroundColor(.siloSecondaryText)
                    .tracking(2)
            }
        }
    }
}
