import SwiftUI

/// Filled = red, hollow = green, hollow-dashed = unavailable. Deliberately
/// plain: no glow, no shadow, no pulsing -- an instrument reading, not an
/// alarm. State changes animate subtly on refresh.
struct DotView: View {
    let state: IndicatorState

    var body: some View {
        Circle()
            .strokeBorder(strokeColor, style: strokeStyle)
            .background(Circle().fill(fillColor))
            .frame(width: 30, height: 30)
            .animation(.easeInOut(duration: 0.5), value: state)
    }

    private var fillColor: Color {
        state == .red ? Tier.broad.color : .clear
    }

    private var strokeColor: Color {
        switch state {
        case .red: return .clear
        case .green: return Color(.systemGray2)
        case .unavailable: return Color(.systemGray4)
        }
    }

    private var strokeStyle: StrokeStyle {
        state == .unavailable
            ? StrokeStyle(lineWidth: 2, dash: [3, 3])
            : StrokeStyle(lineWidth: 2)
    }
}
