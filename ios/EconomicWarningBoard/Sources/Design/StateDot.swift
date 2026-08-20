import SwiftUI

/// State is encoded twice -- by color and by shape -- so it survives color
/// blindness and greyscale. This is the single most important accessibility
/// decision in the product; do not simplify it back to three colored circles.
/// Spec 5.1.
struct StateDot: View {
    let state: IndicatorState
    let bucket: Bucket
    var size: CGFloat = Metrics.dotSmall

    var body: some View {
        Group {
            switch state {
            case .green:
                Circle().fill(bucket.markColor)
            case .red:
                Circle().fill(EWB.broadMark)
                    .overlay(Circle().stroke(EWB.bg, lineWidth: 1.5).padding(-1.5))
                    .overlay(Circle().stroke(EWB.broadMark, lineWidth: 1.5).padding(-3))
            case .unavailable:
                Circle().strokeBorder(EWB.unavailable, style: StrokeStyle(lineWidth: 1.5, dash: [2, 2]))
            }
        }
        .frame(width: size, height: size)
        .accessibilityHidden(true)
    }
}
