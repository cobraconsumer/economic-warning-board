import SwiftUI

struct BucketRow: View {
    let label: String
    let indicators: [Indicator]

    private let columns = Array(repeating: GridItem(.flexible(), spacing: 14), count: 7)

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(label.uppercased())
                .font(.system(size: 13, weight: .semibold))
                .tracking(1)
                .foregroundStyle(.secondary)

            LazyVGrid(columns: columns, alignment: .leading, spacing: 14) {
                ForEach(indicators) { indicator in
                    NavigationLink(value: indicator) {
                        DotView(state: indicator.state)
                    }
                    .buttonStyle(.plain)
                    .accessibilityLabel("\(indicator.name), \(indicator.state.rawValue)")
                    .contextMenu {
                        Label(
                            indicator.state.rawValue.capitalized,
                            systemImage: indicator.state == .red ? "exclamationmark.circle" : "checkmark.circle"
                        )
                    } preview: {
                        IndicatorPreviewCard(indicator: indicator)
                    }
                }
            }
        }
    }
}
