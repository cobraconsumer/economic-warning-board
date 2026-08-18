import SwiftUI

/// Non-negotiable content per spec 2.3: the tiers, the honest out-of-sample
/// lead times, the 35-year false-Warning record, the 2020 exception, the
/// three named blind spots, the historical chart, and "what this is not"
/// stated prominently in the app itself, not just the store listing.
struct MethodologyView: View {
    @EnvironmentObject private var store: BoardStore
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 32) {
                whatThisIsNot
                tiersSection
                trackRecordSection
                if let history = store.board?.history, !history.isEmpty {
                    historySection(history)
                }
                blindSpotsSection
                methodologyLinks
            }
            .padding(20)
        }
        .navigationTitle("Methodology")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button("Done") { dismiss() }
            }
        }
    }

    private var whatThisIsNot: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("What this is not").font(.headline)
            VStack(alignment: .leading, spacing: 4) {
                bulletText("Not a prediction.")
                bulletText("Not a probability.")
                bulletText("Not financial advice.")
                bulletText("Not a recommendation to buy or sell anything.")
            }
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(.secondarySystemBackground), in: RoundedRectangle(cornerRadius: 14))
    }

    private var tiersSection: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("The tiers").font(.headline)
            ForEach(Tier.allCases, id: \.self) { tier in
                HStack(alignment: .top, spacing: 12) {
                    Circle().fill(tier.color).frame(width: 12, height: 12).padding(.top, 5)
                    VStack(alignment: .leading, spacing: 2) {
                        Text(tier.label).font(.subheadline.weight(.semibold))
                        Text(tier.explanation).font(.footnote).foregroundStyle(.secondary)
                    }
                }
            }
        }
    }

    private var trackRecordSection: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Track record, 1988–present").font(.headline)
            Text("Out-of-sample, the Watch tier led the last three recessions by **12, 4, and 5 months**. Those are the honest figures to quote — not ones from any lightly calibrated version of the thresholds.")
                .font(.subheadline)
            Text("**No false Warning-tier reading in 35 years.** The board has shown no active tier roughly 75% of the time.")
                .font(.subheadline)
            Text("2020 is the exception: no advance warning, because no indicator-based system can forecast an external shock like a pandemic. That's a limit worth stating, not hiding.")
                .font(.subheadline)
        }
    }

    private func historySection(_ history: [HistoryPoint]) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("The board, 1988–present").font(.headline)
            HistoryChart(history: history)
            Text("Shaded bands are NBER recessions.")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
    }

    private var blindSpotsSection: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("What this board can't see").font(.headline)
            Text("Three blind spots, named rather than hidden:")
                .font(.subheadline)
            VStack(alignment: .leading, spacing: 8) {
                bulletText("Non-bank private credit — direct lending outside the traditional banking system isn't well covered by public data.")
                bulletText("AI-specific capital spending — a boom-and-bust in this narrow category wouldn't clearly show up in broad investment indicators.")
                bulletText("SMB customer-acquisition costs — stress in how small businesses find customers has no reliable public data series.")
            }
        }
    }

    private var methodologyLinks: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Published methodology").font(.headline)
            Text("The full specification, changelog, and backtest results are public.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
            Link("View on GitHub ↗", destination: URL(string: "https://github.com/cobraconsumer/economic-warning-board")!)
        }
    }

    private func bulletText(_ text: String) -> some View {
        HStack(alignment: .top, spacing: 8) {
            Text("•")
            Text(text)
        }
        .font(.footnote)
        .foregroundStyle(.secondary)
    }
}
