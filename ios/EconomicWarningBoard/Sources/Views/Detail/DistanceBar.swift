import SwiftUI

/// Fixed 0...1.5 scale, tick at 1.0 == exactly the threshold. Reads directly
/// off the server-computed `position` (evaluate.py's compute_position) --
/// the client never derives direction from a parsed threshold string, since
/// some rules flag above and some below, and a couple are multi-part.
/// Spec 5.4. Per section 7.2, "0/20 and nothing is close" is a stronger
/// statement than "0/20" -- this bar is what makes that case, so it renders
/// identically whether the indicator is clear or flagged.
struct DistanceBar: View {
    let indicator: Indicator

    var body: some View {
        if indicator.state == .unavailable {
            Text("Distance unavailable while the series is unreported.")
                .font(.footnote)
                .foregroundStyle(EWB.ink3)
        } else if let position = indicator.position, let value = indicator.value {
            let clamped = min(max(position, 0), 1.5)
            let fillFraction = clamped / 1.5
            let tickFraction: CGFloat = 1.0 / 1.5
            let barColor = indicator.state == .red ? EWB.broadMark : indicator.bucket.markColor
            let labelColor = indicator.state == .red ? EWB.broadText : indicator.bucket.textColor

            VStack(alignment: .leading, spacing: 8) {
                HStack(alignment: .firstTextBaseline) {
                    Text("DISTANCE TO THRESHOLD")
                        .font(.caption2.weight(.bold))
                        .tracking(1.6)
                        .foregroundStyle(EWB.ink3)
                    Spacer()
                    Text(label(for: position, flagged: indicator.state == .red))
                        .font(.footnote.weight(.semibold))
                        .foregroundStyle(labelColor)
                }

                GeometryReader { geo in
                    let width = geo.size.width
                    ZStack(alignment: .leading) {
                        Capsule().fill(EWB.stroke2).frame(height: 7)
                        Capsule().fill(barColor).frame(width: width * fillFraction, height: 7)
                        Rectangle()
                            .fill(EWB.ink3)
                            .frame(width: 1, height: 14)
                            .offset(x: width * tickFraction - 0.5, y: -3.5)
                    }
                }
                .frame(height: 14)

                HStack {
                    Text("today · \(formatted(value)) \(indicator.unit)")
                    Spacer()
                    Text("threshold \(formatted(indicator.threshold)) \(indicator.unit)")
                }
                .font(.caption2)
                .foregroundStyle(EWB.ink4)
            }
        }
    }

    /// Flagged always reads "past threshold" -- spec 5.4. A rule can flag
    /// on memory (recent inversion, sustained rise) rather than today's raw
    /// level, so `position` alone (e.g. 0.5, mid-bar) would otherwise claim
    /// headroom on an indicator that is, in fact, past its threshold.
    private func label(for position: Double, flagged: Bool) -> String {
        if flagged || position >= 1.0 { return "past threshold" }
        let headroom = max(0, min(1, 1 - position))
        return "\(Int((headroom * 100).rounded()))% of headroom left"
    }

    private func formatted(_ n: Double?) -> String {
        guard let n else { return "—" }
        return String(format: abs(n) >= 100 ? "%.0f" : "%.2f", n)
    }
}
