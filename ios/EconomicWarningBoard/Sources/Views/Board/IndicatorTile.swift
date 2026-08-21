import SwiftUI

extension Indicator {
    var tileValueText: String {
        guard let value else { return "—" }
        return String(format: abs(value) >= 100 ? "%.0f" : "%.2f", value)
    }

    /// Tile-only: appends a bare "%" for percentage-based units so a value
    /// like 0.00 reads as "0.00%" instead of a bare "0.00" that a scanning
    /// eye can mistake for the underlying count being literally zero (e.g.
    /// jobless claims at their 1-year low reads as 0% above it, not as zero
    /// claims filed). The Detail screen already spells the unit out in full,
    /// so this stays tile-only rather than folding into tileValueText.
    var compactValueText: String {
        unit.hasPrefix("%") ? tileValueText + "%" : tileValueText
    }

    var accessibilityStateWord: String {
        switch state {
        case .red: return "flagged"
        case .green: return "clear"
        case .unavailable: return "unavailable"
        }
    }

    /// Weight scaled by run length, capped low so a long run can never
    /// approach a red state's visual weight -- spec-v0.6-tile-information.md
    /// section 7. The server already gates direction to toward/away only
    /// past a 3-step minimum, so any non-flat trend here is real.
    var trendArrowOpacity: Double {
        guard let steps = trend?.steps else { return 0 }
        return min(0.85, 0.45 + 0.04 * Double(steps))
    }
}

/// Small, bucket-hued, never a tier color -- a trend is a direction, not a
/// state. Spec section 2's "no tier colors on tiles" non-negotiable.
struct TrendArrow: View {
    let indicator: Indicator
    var size: CGFloat = 9

    var body: some View {
        if let trend = indicator.trend, trend.direction != .flat {
            Image(systemName: trend.direction == .toward ? "arrow.up.right" : "arrow.down.right")
                .font(.system(size: size, weight: .bold))
                .foregroundStyle(indicator.bucket.markColor.opacity(indicator.trendArrowOpacity))
                .accessibilityHidden(true)
        }
    }
}

/// Label top-left, dot top-right, value bottom-left. Fixed 70pt height;
/// labels wrap to two lines -- that's expected, indicator names never
/// truncate. Flagged state is carried by four channels at once (border,
/// wash, dot shape, value color), not just one. Spec 5.2.
struct IndicatorTile: View {
    let indicator: Indicator

    var body: some View {
        VStack(alignment: .leading, spacing: 3) {
            HStack(alignment: .top, spacing: 4) {
                Text(IndicatorCopy.shortName[indicator.id] ?? indicator.name)
                    .font(.caption2.weight(.semibold))
                    .foregroundStyle(EWB.ink)
                    .lineLimit(2)
                    .multilineTextAlignment(.leading)
                    .fixedSize(horizontal: false, vertical: true)
                Spacer(minLength: 4)
                StateDot(state: indicator.state, bucket: indicator.bucket)
                    .padding(.top, 2)
                    .padding(.trailing, 2)
            }
            Spacer(minLength: 0)
            HStack(spacing: 3) {
                Text(indicator.compactValueText)
                    .font(.caption2.monospacedDigit())
                    .foregroundStyle(indicator.state == .red ? EWB.broadText : EWB.ink2)
                TrendArrow(indicator: indicator)
            }
        }
        .padding(10)
        .frame(height: 70, alignment: .topLeading)
        .frame(maxWidth: .infinity, alignment: .topLeading)
        .background(tileBackground)
        .overlay(tileBorder)
        .contentShape(Rectangle())
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(indicator.name), \(indicator.accessibilityStateWord), \(indicator.tileValueText) \(indicator.unit)\(trendAccessibilitySuffix)")
    }

    private var trendAccessibilitySuffix: String {
        guard let trend = indicator.trend, trend.direction != .flat else { return "" }
        return ", " + trend.text
    }

    private var tileBackground: some View {
        ZStack {
            RoundedRectangle(cornerRadius: Radius.tile).fill(EWB.glass)
            if indicator.state == .red {
                RadialGradient(colors: [EWB.broadMark.opacity(0.16), .clear],
                               center: .bottomTrailing, startRadius: 0, endRadius: 90)
            }
        }
    }

    private var tileBorder: some View {
        RoundedRectangle(cornerRadius: Radius.tile)
            .strokeBorder(indicator.state == .red ? EWB.broadMark.opacity(0.45) : EWB.stroke, lineWidth: 1)
    }
}

/// The 7th item in a group of 7 spans the full grid width as a 54pt row
/// instead of leaving a ragged hole on a 3-column layout. Groups of 6 use
/// two clean rows and never get one of these. Spec 5.2.
struct IndicatorWideTile: View {
    let indicator: Indicator

    var body: some View {
        HStack(spacing: 12) {
            StateDot(state: indicator.state, bucket: indicator.bucket)
            Text(IndicatorCopy.shortName[indicator.id] ?? indicator.name)
                .font(.caption2.weight(.semibold))
                .foregroundStyle(EWB.ink)
                .lineLimit(2)
                .multilineTextAlignment(.leading)
                .frame(width: 104, alignment: .leading)

            if !indicator.sparkline.isEmpty {
                SparklineChart(
                    values: indicator.sparkline,
                    thresholdValue: indicator.threshold,
                    color: indicator.state == .red ? EWB.broadText : indicator.bucket.textColor
                )
                .frame(height: 24)
            } else {
                Spacer()
            }

            HStack(spacing: 3) {
                Text(indicator.compactValueText)
                    .font(.caption.monospacedDigit())
                    .foregroundStyle(indicator.state == .red ? EWB.broadText : EWB.ink2)
                TrendArrow(indicator: indicator, size: 10)
            }
        }
        .padding(.horizontal, 12)
        .frame(height: 54)
        .frame(maxWidth: .infinity)
        .background(
            ZStack {
                RoundedRectangle(cornerRadius: Radius.tile).fill(EWB.glass)
                if indicator.state == .red {
                    RadialGradient(colors: [EWB.broadMark.opacity(0.16), .clear],
                                   center: .trailing, startRadius: 0, endRadius: 120)
                }
            }
        )
        .overlay(
            RoundedRectangle(cornerRadius: Radius.tile)
                .strokeBorder(indicator.state == .red ? EWB.broadMark.opacity(0.45) : EWB.stroke, lineWidth: 1)
        )
        .contentShape(Rectangle())
        .accessibilityElement(children: .combine)
        .accessibilityLabel("\(indicator.name), \(indicator.accessibilityStateWord), \(indicator.tileValueText) \(indicator.unit)\(trendAccessibilitySuffix)")
    }

    private var trendAccessibilitySuffix: String {
        guard let trend = indicator.trend, trend.direction != .flat else { return "" }
        return ", " + trend.text
    }
}
