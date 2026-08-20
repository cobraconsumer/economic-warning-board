import SwiftUI

/// A 3-column grid of tiles. When the group's count % 3 == 1 (i.e. groups of
/// 7), the trailing item spans the full width as a wide row instead of
/// leaving a ragged hole -- groups of 6 use two clean rows and get no wide
/// item. Spec 5.2.
struct BucketGroupView: View {
    let bucket: Bucket
    let indicators: [Indicator]
    let flaggedCount: Int

    private let columns = Array(repeating: GridItem(.flexible(), spacing: Metrics.gapTile), count: 3)

    private var wideItem: Indicator? {
        indicators.count % 3 == 1 ? indicators.last : nil
    }

    private var gridItems: [Indicator] {
        wideItem != nil ? Array(indicators.dropLast()) : indicators
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text(bucket.label)
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(EWB.ink)
                Spacer()
                Text("\(flaggedCount) flagged")
                    .font(.footnote)
                    .foregroundStyle(EWB.ink3)
            }

            LazyVGrid(columns: columns, spacing: Metrics.gapTile) {
                ForEach(gridItems) { indicator in
                    tile(for: indicator)
                }
            }

            if let wideItem {
                tile(for: wideItem, wide: true)
            }
        }
    }

    @ViewBuilder
    private func tile(for indicator: Indicator, wide: Bool = false) -> some View {
        NavigationLink(value: indicator) {
            if wide {
                IndicatorWideTile(indicator: indicator)
            } else {
                IndicatorTile(indicator: indicator)
            }
        }
        .buttonStyle(.plain)
        .contextMenu {
            Label(
                indicator.accessibilityStateWord.capitalized,
                systemImage: indicator.state == .red ? "exclamationmark.circle" : "checkmark.circle"
            )
        } preview: {
            IndicatorPreviewCard(indicator: indicator)
        }
    }
}
