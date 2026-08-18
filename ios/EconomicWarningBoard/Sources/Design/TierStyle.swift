import SwiftUI

extension Tier {
    /// Quiet neutral gray, Watch amber, Warning orange, Broad red -- a calm
    /// instrument panel, not a threat display. No glow, no saturation ramp.
    var color: Color {
        switch self {
        case .quiet: return Color(.systemGray)
        case .watch: return Color(red: 0.80, green: 0.58, blue: 0.12)
        case .warning: return Color(red: 0.87, green: 0.42, blue: 0.12)
        case .broad: return Color(red: 0.72, green: 0.15, blue: 0.15)
        }
    }

    var label: String { rawValue }

    var explanation: String {
        switch self {
        case .quiet:
            return "No unusual conditions. Most of history looks like this."
        case .watch:
            return "Early signs are showing up. Historically the tier that matters most — it has led every recession studied by 4 to 12 months."
        case .warning:
            return "Conditions have broadened. Historically arrives at or near the start of a downturn, not far ahead of it."
        case .broad:
            return "Red across most of the board. Has not occurred outside an actual recession in the 35 years studied."
        }
    }
}
