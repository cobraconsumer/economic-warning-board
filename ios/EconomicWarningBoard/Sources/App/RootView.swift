import SwiftUI

struct RootView: View {
    var body: some View {
        NavigationStack {
            BoardView()
                .navigationDestination(for: Indicator.self) { indicator in
                    IndicatorDetailView(indicator: indicator)
                }
        }
    }
}
