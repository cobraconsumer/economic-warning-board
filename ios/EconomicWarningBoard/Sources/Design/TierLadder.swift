import SwiftUI

/// Carries tier escalation visually since the one-warm-family color decision
/// means Watch and Warning are otherwise hard to tell apart on their own.
/// Not optional. Spec 5.3.
struct TierLadder: View {
    let tier: Tier

    var body: some View {
        HStack(spacing: 3) {
            ForEach(Tier.allCases, id: \.self) { step in
                Capsule()
                    .fill(step.markColor)
                    .opacity(step == tier ? 1.0 : 0.34)
                    .frame(width: 19, height: 4)
            }
        }
        .accessibilityHidden(true)
    }
}
