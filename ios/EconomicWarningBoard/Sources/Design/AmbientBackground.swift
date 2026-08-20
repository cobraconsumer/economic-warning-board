import SwiftUI

/// A static radial wash from the top-left into the base surface, plus a
/// weaker one low-right. Static, not `.blur()` over a scrolling layer --
/// blurring a live layer on every scroll frame is the most likely source of
/// jank in this app. Spec section 6.
struct AmbientBackground<Content: View>: View {
    @Environment(\.colorScheme) private var colorScheme
    @ViewBuilder var content: Content

    private var meshScale: Double { colorScheme == .dark ? 1.0 : 0.5 }

    var body: some View {
        ZStack {
            EWB.bg.ignoresSafeArea()
            RadialGradient(
                colors: [EWB.bizMark.opacity(0.38 * meshScale), .clear],
                center: UnitPoint(x: -0.1, y: -0.05), startRadius: 0, endRadius: 340
            )
            .ignoresSafeArea()
            .allowsHitTesting(false)
            RadialGradient(
                colors: [EWB.finMark.opacity(0.30 * meshScale), .clear],
                center: UnitPoint(x: 0.9, y: 0.02), startRadius: 0, endRadius: 300
            )
            .ignoresSafeArea()
            .allowsHitTesting(false)
            content
        }
    }
}

extension View {
    /// `.ultraThinMaterial` with a 1pt stroke and an inner top highlight --
    /// the highlight is what sells it as glass; without it a card reads as a
    /// flat translucent rectangle. Spec section 6.
    func glassCard(radius: CGFloat = Radius.card) -> some View {
        self
            .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: radius))
            .overlay(RoundedRectangle(cornerRadius: radius).strokeBorder(EWB.stroke, lineWidth: 1))
            .overlay(alignment: .top) {
                LinearGradient(colors: [EWB.ink.opacity(0.14), .clear], startPoint: .top, endPoint: .bottom)
                    .frame(height: 1)
                    .padding(.horizontal, 1)
                    .clipShape(RoundedRectangle(cornerRadius: radius))
            }
    }
}
