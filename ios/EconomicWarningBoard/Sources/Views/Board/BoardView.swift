import SwiftUI

struct BoardView: View {
    @EnvironmentObject private var store: BoardStore
    @State private var showMethodology = false
    @State private var showWatchlist = false

    var body: some View {
        AmbientBackground {
            ScrollView {
                VStack(alignment: .leading, spacing: 28) {
                    header
                    if let board = store.board {
                        content(for: board)
                    } else if store.isLoading {
                        ProgressView()
                            .tint(EWB.ink3)
                            .padding(.top, 140)
                            .frame(maxWidth: .infinity)
                    } else {
                        unavailableState
                    }
                }
                .padding(.horizontal, Metrics.screenPadding)
                .padding(.top, 12)
                .padding(.bottom, 40)
            }
            .scrollContentBackground(.hidden)
        }
        .refreshable { await store.refresh() }
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button {
                    showMethodology = true
                } label: {
                    Image(systemName: "info.circle")
                }
                .tint(EWB.ink2)
                .accessibilityLabel("About this board")
            }
        }
        .sheet(isPresented: $showMethodology) {
            NavigationStack { MethodologyView() }
        }
        .sheet(isPresented: $showWatchlist) {
            NavigationStack { WatchlistView() }
        }
    }

    private var header: some View {
        HStack(alignment: .firstTextBaseline) {
            Text("Warning Board")
                .font(.title3.weight(.bold))
                .foregroundStyle(EWB.ink)
            Spacer()
            if let board = store.board {
                Text(DateFormatting.dayMonthYear(board.generatedAt))
                    .font(.footnote)
                    .foregroundStyle(EWB.ink3)
            }
        }
    }

    @ViewBuilder
    private func content(for board: Board) -> some View {
        countBlock(board.board)

        VStack(alignment: .leading, spacing: Metrics.gapGroup + 10) {
            ForEach(Bucket.order, id: \.self) { bucket in
                let inds = board.indicators
                    .filter { $0.bucket == bucket }
                    .sorted { $0.id < $1.id }
                let flagged = board.board.buckets[bucket.rawValue]?.red ?? 0
                BucketGroupView(bucket: bucket, indicators: inds, flaggedCount: flagged)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)

        worthWatchingSection(board.indicators)

        if let watchlist = board.watchlist, !watchlist.isEmpty {
            contextRow(count: watchlist.count)
        }

        if let lastError = store.lastError {
            Text(lastError)
                .font(.footnote)
                .foregroundStyle(EWB.ink3)
        }
    }

    private func countBlock(_ summary: BoardSummary) -> some View {
        HStack(alignment: .top) {
            HStack(alignment: .lastTextBaseline, spacing: 8) {
                Text("\(summary.reds)")
                    .font(.system(size: 72, weight: .bold, design: .rounded))
                    .monospacedDigit()
                    .minimumScaleFactor(0.6)
                    .foregroundStyle(summary.tier.countColor)
                    .contentTransition(.numericText())
                Text("of \(summary.available)")
                    .font(.title2.weight(.semibold))
                    .foregroundStyle(EWB.ink2)
            }
            Spacer()
            VStack(alignment: .trailing, spacing: 8) {
                tierChip(summary.tier)
                Text(sinceText(summary))
                    .font(.footnote)
                    .foregroundStyle(EWB.ink3)
                    .multilineTextAlignment(.trailing)
                TierLadder(tier: summary.tier)
            }
        }
        .animation(.easeInOut(duration: 0.5), value: summary.reds)
    }

    private func tierChip(_ tier: Tier) -> some View {
        Text(tier.rawValue)
            .font(.caption.weight(.bold))
            .tracking(1.2)
            .foregroundStyle(tier.textColor)
            .padding(.horizontal, 12)
            .padding(.vertical, 5)
            .overlay(Capsule().strokeBorder(tier.markColor.opacity(0.5), lineWidth: 1))
    }

    private func sinceText(_ summary: BoardSummary) -> String {
        "since " + (DateFormatting.monthYear(summary.tierSince) ?? summary.tierSince)
    }

    /// Ranked by trend, not proximity -- a tile sitting right at its
    /// threshold but flat or improving isn't worth watching; a tile further
    /// off but moving steadily toward it is. Replaces the old proximity-
    /// ranked "closest to flipping" module, which spec-v0.6-tile-
    /// information.md section 0 shows gets indicator #18 backwards (it
    /// surfaced as "closest" while on a 7-quarter improving streak).
    /// Ranked by run length, then magnitude -- never by position, and never
    /// a count/fraction over all twenty (spec section 9 acceptance check 7).
    private func worthWatching(_ indicators: [Indicator]) -> Indicator? {
        indicators
            .filter { $0.trend?.direction == .toward }
            .max { a, b in
                let stepsA = a.trend?.steps ?? 0, stepsB = b.trend?.steps ?? 0
                if stepsA != stepsB { return stepsA < stepsB }
                return (a.trend?.deltaPosition ?? 0) < (b.trend?.deltaPosition ?? 0)
            }
    }

    /// Renders unconditionally -- per spec section 7, "nothing is trending
    /// toward a threshold" is itself a finding worth stating, not a state
    /// to hide the module for.
    @ViewBuilder
    private func worthWatchingSection(_ indicators: [Indicator]) -> some View {
        if let indicator = worthWatching(indicators) {
            worthWatchingRow(indicator)
        } else {
            worthWatchingEmptyState
        }
    }

    private func worthWatchingRow(_ indicator: Indicator) -> some View {
        NavigationLink(value: indicator) {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 2) {
                    Text("WORTH WATCHING")
                        .font(.caption2.weight(.bold))
                        .tracking(1.6)
                        .foregroundStyle(EWB.ink3)
                    Text(IndicatorCopy.shortName[indicator.id] ?? indicator.name)
                        .font(.subheadline.weight(.semibold))
                        .foregroundStyle(EWB.ink)
                    if let trend = indicator.trend {
                        Text(trend.text)
                            .font(.footnote)
                            .foregroundStyle(EWB.ink3)
                    }
                }
                Spacer()
                Image(systemName: "chevron.right")
                    .font(.footnote)
                    .foregroundStyle(EWB.ink3)
            }
            .padding(16)
            .frame(maxWidth: .infinity)
            .glassCard()
        }
        .buttonStyle(.plain)
    }

    private var worthWatchingEmptyState: some View {
        VStack(alignment: .leading, spacing: 2) {
            Text("WORTH WATCHING")
                .font(.caption2.weight(.bold))
                .tracking(1.6)
                .foregroundStyle(EWB.ink3)
            Text("Nothing is trending toward a threshold.")
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(EWB.ink)
            Text("All twenty indicators are flat or moving away.")
                .font(.footnote)
                .foregroundStyle(EWB.ink3)
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .glassCard()
    }

    private func contextRow(count: Int) -> some View {
        Button {
            showWatchlist = true
        } label: {
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    Text("Context")
                        .font(.subheadline.weight(.semibold))
                        .foregroundStyle(EWB.ink)
                    Text("\(count) points · outside the count")
                        .font(.footnote)
                        .foregroundStyle(EWB.ink3)
                }
                Spacer()
                Image(systemName: "chevron.right")
                    .font(.footnote)
                    .foregroundStyle(EWB.ink3)
            }
            .padding(16)
            .frame(maxWidth: .infinity)
            .glassCard()
        }
        .buttonStyle(.plain)
    }

    private var unavailableState: some View {
        VStack(spacing: 14) {
            Image(systemName: "wifi.slash")
                .font(.system(size: 34))
                .foregroundStyle(EWB.ink3)
            Text("Couldn't load the board")
                .font(.headline)
                .foregroundStyle(EWB.ink)
            if let lastError = store.lastError {
                Text(lastError)
                    .font(.footnote)
                    .foregroundStyle(EWB.ink3)
                    .multilineTextAlignment(.center)
            }
            Button("Try Again") {
                Task { await store.refresh() }
            }
            .buttonStyle(.borderedProminent)
            .tint(EWB.finMark)
            .padding(.top, 4)
        }
        .frame(maxWidth: .infinity)
        .padding(.top, 120)
    }
}
