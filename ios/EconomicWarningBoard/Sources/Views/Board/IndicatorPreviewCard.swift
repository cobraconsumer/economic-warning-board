import SwiftUI

/// Long-press preview for a dot -- a quick peek at what it is and why it
/// reads the way it does, without leaving the Board screen. Tapping still
/// opens the full IndicatorDetailView; this is just faster than a round trip
/// for someone scanning the whole board.
struct IndicatorPreviewCard: View {
    let indicator: Indicator

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            VStack(alignment: .leading, spacing: 4) {
                Text((IndicatorCopy.bucketLabels[indicator.bucket] ?? indicator.bucket).uppercased())
                    .font(.system(size: 11, weight: .semibold))
                    .tracking(1)
                    .foregroundStyle(.secondary)
                Text(indicator.name)
                    .font(.headline)
            }

            if !indicator.sparkline.isEmpty {
                SparklineChart(
                    values: indicator.sparkline,
                    thresholdValue: IndicatorCopy.thresholdLine[indicator.id]
                )
                .frame(height: 56)
            }

            if let value = indicator.value {
                Text(String(format: "%.2f %@", value, indicator.unit))
                    .font(.subheadline.weight(.semibold))
            }

            Text(indicator.whyText)
                .font(.footnote)
                .foregroundStyle(.secondary)
                .fixedSize(horizontal: false, vertical: true)
        }
        .padding(16)
        .frame(width: 280, alignment: .leading)
    }
}
