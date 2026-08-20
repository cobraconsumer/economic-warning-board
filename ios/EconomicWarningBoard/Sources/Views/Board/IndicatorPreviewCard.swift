import SwiftUI

/// Long-press preview for a tile -- a quick peek at what it is and why it
/// reads the way it does, without leaving the Board screen. Tapping still
/// opens the full IndicatorDetailView; this is just faster than a round trip
/// for someone scanning the whole board. Not in the design brief yet (spec
/// section 9.1) -- styled to match the new token system as a reasonable
/// placeholder, not a final design.
struct IndicatorPreviewCard: View {
    let indicator: Indicator

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            VStack(alignment: .leading, spacing: 4) {
                Text(indicator.bucket.label.uppercased())
                    .font(.caption2.weight(.bold))
                    .tracking(1.6)
                    .foregroundStyle(EWB.ink3)
                Text(indicator.name)
                    .font(.headline)
                    .foregroundStyle(EWB.ink)
            }

            if !indicator.sparkline.isEmpty {
                SparklineChart(
                    values: indicator.sparkline,
                    thresholdValue: indicator.threshold,
                    color: indicator.state == .red ? EWB.broadText : indicator.bucket.textColor
                )
                .frame(height: 56)
            }

            Text(indicator.tileValueText + " " + indicator.unit)
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(EWB.ink)

            Text(indicator.whyText)
                .font(.footnote)
                .foregroundStyle(EWB.ink3)
                .fixedSize(horizontal: false, vertical: true)
        }
        .padding(16)
        .frame(width: 280, alignment: .leading)
        .background(EWB.bgRaise)
    }
}
