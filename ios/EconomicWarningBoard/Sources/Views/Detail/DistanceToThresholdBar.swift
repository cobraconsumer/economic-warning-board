import SwiftUI

/// Per spec-v0.5-candidates.md section 7: "the single most informative
/// artifact of this review was the gap table, and the app currently
/// discards that information." Shows where today's reading sits relative
/// to the threshold and the indicator's own recent range -- makes the
/// honest case for a quiet board visible, not just assumed.
struct DistanceToThresholdBar: View {
    let indicator: Indicator

    var body: some View {
        if let threshold = IndicatorCopy.thresholdLine[indicator.id],
           let value = indicator.value,
           !indicator.sparkline.isEmpty {
            let aboveIsBad = IndicatorCopy.aboveIsBad[indicator.id] ?? true
            let sparkMin = indicator.sparkline.min() ?? value
            let sparkMax = indicator.sparkline.max() ?? value
            let domainMin = min(sparkMin, threshold, value)
            let domainMax = max(sparkMax, threshold, value)
            let span = max(domainMax - domainMin, 0.0001)
            let padding = span * 0.08
            let lo = domainMin - padding
            let totalSpan = span + padding * 2

            VStack(alignment: .leading, spacing: 8) {
                Text("Distance to threshold")
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(.secondary)

                GeometryReader { geo in
                    let width = geo.size.width
                    let valueX = width * CGFloat((value - lo) / totalSpan)
                    let thresholdX = width * CGFloat((threshold - lo) / totalSpan)
                    let dangerX = aboveIsBad ? thresholdX : 0
                    let dangerWidth = aboveIsBad ? max(width - thresholdX, 0) : max(thresholdX, 0)

                    ZStack(alignment: .leading) {
                        Capsule()
                            .fill(Color(.systemGray5))
                            .frame(height: 8)

                        Capsule()
                            .fill(Tier.broad.color.opacity(0.15))
                            .frame(width: dangerWidth, height: 8)
                            .offset(x: dangerX)

                        Rectangle()
                            .fill(Color(.systemGray2))
                            .frame(width: 2, height: 16)
                            .offset(x: thresholdX - 1, y: -4)

                        Circle()
                            .fill(indicator.state == .red ? Tier.broad.color : Color.primary)
                            .frame(width: 12, height: 12)
                            .offset(x: valueX - 6, y: -2)
                    }
                }
                .frame(height: 20)

                HStack {
                    Text("now: \(formatted(value))")
                    Spacer()
                    Text("threshold: \(formatted(threshold))")
                }
                .font(.caption)
                .foregroundStyle(.secondary)
            }
        }
    }

    private func formatted(_ n: Double) -> String {
        String(format: abs(n) >= 100 ? "%.0f" : "%.2f", n)
    }
}
