import SwiftUI

/// Non-negotiable content per spec 7.4: "what this is not" sits near the top
/// as a real card (not fine print), the four tiers, the history chart, the
/// honest out-of-sample track record, three named blind spots, and a link
/// to the public methodology. All figures below are the real out-of-sample
/// numbers from the frozen backtest -- not the calibrated ones, which are
/// better and are deliberately withheld because the system was fitted on
/// the same history that produced them.
struct MethodologyView: View {
    @EnvironmentObject private var store: BoardStore
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        AmbientBackground {
            ScrollView {
                VStack(alignment: .leading, spacing: 28) {
                    intro
                    whatThisIsNot
                    fourTiers
                    tilesArentAVote
                    if let history = store.board?.history, !history.isEmpty {
                        historySection(history)
                    }
                    trackRecord
                    blindSpots
                    methodologyLink
                }
                .padding(.horizontal, Metrics.screenPadding)
                .padding(.top, 12)
                .padding(.bottom, 40)
            }
            .scrollContentBackground(.hidden)
        }
        .navigationTitle("Methodology")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button("Done") { dismiss() }
                    .tint(EWB.ink2)
            }
        }
    }

    private var intro: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("How this works.")
                .font(.title.weight(.bold))
                .foregroundStyle(EWB.ink)
            Text("Twenty indicators from public government data. Each has a fixed threshold set in advance. The count is how many are past theirs today. Nothing here is a forecast.")
                .font(.subheadline)
                .foregroundStyle(EWB.ink2)
        }
    }

    private var whatThisIsNot: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("WHAT THIS IS NOT")
                .font(.caption2.weight(.bold))
                .tracking(1.6)
                .foregroundStyle(EWB.ink3)
            notItem("Not a prediction.", "A high count means conditions resemble past pre-recession periods. It does not mean one is coming.")
            notItem("Not financial advice.", "Nothing here is a recommendation to buy, sell, or hold anything.")
            notItem("Not a live feed.", "The data updates once a day. Some underlying series are monthly or quarterly and are older than that.")
            notItem("Not complete.", "Three known blind spots are listed below. There are certainly others.")
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .overlay(RoundedRectangle(cornerRadius: Radius.card).strokeBorder(EWB.stroke2, lineWidth: 1))
    }

    private func notItem(_ lead: String, _ rest: String) -> some View {
        HStack(alignment: .top, spacing: 10) {
            Text("—").foregroundStyle(EWB.ink3)
            (Text(lead).fontWeight(.bold) + Text(" " + rest))
                .font(.subheadline)
                .foregroundStyle(EWB.ink2)
        }
    }

    private var fourTiers: some View {
        VStack(alignment: .leading, spacing: 0) {
            Text("THE FOUR TIERS")
                .font(.caption2.weight(.bold))
                .tracking(1.6)
                .foregroundStyle(EWB.ink3)
                .padding(.bottom, 14)
            ForEach(Tier.allCases, id: \.self) { tier in
                tierRow(tier)
                if tier != Tier.allCases.last {
                    Rectangle().fill(EWB.stroke).frame(height: 1).padding(.vertical, 14)
                }
            }
        }
    }

    private func tierRow(_ tier: Tier) -> some View {
        let isCurrent = store.board?.board.tier == tier
        return HStack(alignment: .top, spacing: 12) {
            Rectangle().fill(tier.markColor).frame(width: 3).frame(maxHeight: .infinity)
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text(tier.rawValue.capitalized + (isCurrent ? " · now" : ""))
                        .font(.subheadline.weight(.bold))
                        .foregroundStyle(isCurrent ? tier.textColor : EWB.ink)
                    Spacer()
                    Text(flaggedRange(tier))
                        .font(.footnote)
                        .foregroundStyle(EWB.ink3)
                }
                Text(tier.explanation)
                    .font(.footnote)
                    .foregroundStyle(EWB.ink2)
            }
        }
        .frame(minHeight: 44)
    }

    private func flaggedRange(_ tier: Tier) -> String {
        switch tier {
        case .quiet: return "0–4 flagged"
        case .watch: return "5–7 flagged"
        case .warning: return "8–11 flagged"
        case .broad: return "12+ flagged"
        }
    }

    private var tilesArentAVote: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("WHY TILES NEVER ADD UP TO A TIER")
                .font(.caption2.weight(.bold))
                .tracking(1.6)
                .foregroundStyle(EWB.ink3)
            Text("Each tile shows its own state and trend, but they never combine into a count or a tier of their own. The twenty indicators aren't twenty independent votes — several move together off the same underlying stress, so tallying coloured tiles would overstate how broad a signal really is. The bucket gates exist to handle that correlation properly, and they run on the hero count alone.")
                .font(.footnote)
                .foregroundStyle(EWB.ink2)
        }
    }

    private func historySection(_ history: [HistoryPoint]) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("SHARE OF INDICATORS FLAGGED, 1988 TO TODAY")
                .font(.caption2.weight(.bold))
                .tracking(1.6)
                .foregroundStyle(EWB.ink3)
            Text("Shaded bands are NBER recessions. Dashed line is the Watch threshold.")
                .font(.footnote)
                .foregroundStyle(EWB.ink3)
            HistoryChart(history: history, watchFraction: 0.25)
        }
    }

    private var trackRecord: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("TRACK RECORD, OUT OF SAMPLE")
                .font(.caption2.weight(.bold))
                .tracking(1.6)
                .foregroundStyle(EWB.ink3)

            LazyVGrid(columns: [GridItem(.flexible(), spacing: 10), GridItem(.flexible())], spacing: 10) {
                statCard("3 of 3", "Recessions called in advance", "1990-91, 2001, 2007-09")
                statCard("5 mo", "Median lead time", "range 4 to 12 months")
                statCard("0", "False Warning or Broad readings", "in 35 years, four stress tests")
                statCard("1", "Missed entirely", "2020 — external shock")
            }

            Text("These are the out-of-sample figures. The calibrated numbers are better and are not shown, because the system was fitted on the same history that produced them.")
                .font(.footnote)
                .foregroundStyle(EWB.ink3)
        }
    }

    private func statCard(_ value: String, _ title: String, _ subtitle: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(value)
                .font(.title2.weight(.bold).monospacedDigit())
                .foregroundStyle(EWB.ink)
            Text(title)
                .font(.caption.weight(.semibold))
                .foregroundStyle(EWB.ink2)
            Text(subtitle)
                .font(.caption2)
                .foregroundStyle(EWB.ink3)
        }
        .padding(14)
        .frame(maxWidth: .infinity, alignment: .leading)
        .glassCard(radius: Radius.tile)
    }

    private var blindSpots: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("THREE THINGS IT CANNOT SEE")
                .font(.caption2.weight(.bold))
                .tracking(1.6)
                .foregroundStyle(EWB.ink3)
            blindSpot("01", "Shocks with no economic build-up", "A pandemic, a war, a sudden fiscal cliff. 2020 was missed because nothing in the data was deteriorating beforehand. No indicator here can see an event that hasn't started.")
            blindSpot("02", "Stress that never reaches public data", "Non-bank private credit, AI-specific capital spending, and small-business customer acquisition costs don't appear in any series this reads. A crisis can build in places the government doesn't publish.")
            blindSpot("03", "A changed economy", "These thresholds were calibrated on 1988-2026. If the relationship between manufacturing, labor, and output has structurally shifted, the levels may be tuned to an economy that no longer exists.")
        }
    }

    private func blindSpot(_ number: String, _ title: String, _ body: String) -> some View {
        HStack(alignment: .top, spacing: 14) {
            Text(number)
                .font(.footnote.weight(.bold).monospacedDigit())
                .foregroundStyle(EWB.ink3)
            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.subheadline.weight(.bold))
                    .foregroundStyle(EWB.ink)
                Text(body)
                    .font(.footnote)
                    .foregroundStyle(EWB.ink2)
            }
        }
    }

    private var methodologyLink: some View {
        Link(destination: URL(string: "https://github.com/cobraconsumer/economic-warning-board")!) {
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    Text("Full methodology and source code")
                        .font(.subheadline.weight(.semibold))
                        .foregroundStyle(EWB.ink)
                    Text("Every threshold, in public")
                        .font(.footnote)
                        .foregroundStyle(EWB.ink3)
                }
                Spacer()
                Text("Open ↗")
                    .font(.footnote.weight(.semibold))
                    .foregroundStyle(EWB.finText)
            }
            .padding(16)
            .frame(maxWidth: .infinity)
            .glassCard()
        }
    }
}
