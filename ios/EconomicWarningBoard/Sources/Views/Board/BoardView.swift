import SwiftUI

struct BoardView: View {
    @EnvironmentObject private var store: BoardStore
    @State private var showMethodology = false
    @State private var showWatchlist = false

    var body: some View {
        ScrollView {
            VStack(spacing: 36) {
                if let board = store.board {
                    content(for: board)
                } else if store.isLoading {
                    ProgressView()
                        .padding(.top, 140)
                } else {
                    unavailableState
                }
            }
            .padding(.horizontal, 24)
            .padding(.top, 24)
            .padding(.bottom, 48)
            .frame(maxWidth: .infinity)
        }
        .refreshable { await store.refresh() }
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .principal) {
                Text("ECONOMIC WARNING BOARD")
                    .font(.system(size: 13, weight: .semibold))
                    .tracking(1.4)
                    .foregroundStyle(.secondary)
            }
            ToolbarItem(placement: .topBarTrailing) {
                Button {
                    showMethodology = true
                } label: {
                    Image(systemName: "info.circle")
                }
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

    @ViewBuilder
    private func content(for board: Board) -> some View {
        VStack(spacing: 8) {
            Text("\(board.board.reds) of \(board.board.available)")
                .font(.system(size: 60, weight: .bold, design: .rounded))
                .monospacedDigit()
                .contentTransition(.numericText())
                .animation(.easeInOut(duration: 0.5), value: board.board.reds)
        }

        VStack(spacing: 6) {
            Text(board.board.tier.label)
                .font(.system(size: 20, weight: .bold))
                .tracking(2)
                .foregroundStyle(board.board.tier.color)
            Text(tierSinceText(board.board))
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
        }

        VStack(alignment: .leading, spacing: 28) {
            ForEach(Bucket.order, id: \.self) { key in
                if let bucket = board.board.buckets[key] {
                    BucketRow(
                        label: bucket.label,
                        indicators: board.indicators
                            .filter { $0.bucket == key }
                            .sorted { $0.id < $1.id }
                    )
                }
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)

        if let watchlist = board.watchlist, !watchlist.isEmpty {
            Button {
                showWatchlist = true
            } label: {
                HStack {
                    Text("CONTEXT")
                        .font(.system(size: 12, weight: .semibold))
                        .tracking(1)
                    Spacer()
                    Text("\(watchlist.count) items, not scored")
                        .font(.footnote)
                    Image(systemName: "chevron.right")
                        .font(.caption)
                }
                .foregroundStyle(.secondary)
                .padding(14)
                .background(Color(.secondarySystemBackground), in: RoundedRectangle(cornerRadius: 12))
            }
            .buttonStyle(.plain)
        }

        VStack(spacing: 4) {
            Text("Updated \(DateFormatting.dayMonthYear(board.generatedAt))")
                .font(.footnote)
                .foregroundStyle(.tertiary)
            if let lastError = store.lastError {
                Text(lastError)
                    .font(.footnote)
                    .foregroundStyle(.orange)
                    .multilineTextAlignment(.center)
            }
        }
    }

    private func tierSinceText(_ summary: BoardSummary) -> String {
        let since = DateFormatting.monthYear(summary.tierSince) ?? summary.tierSince
        switch summary.tier {
        case .quiet:
            return "No conditions met since \(since)"
        default:
            return "At \(summary.tier.label.capitalized) since \(since)"
        }
    }

    private var unavailableState: some View {
        VStack(spacing: 14) {
            Image(systemName: "wifi.slash")
                .font(.system(size: 34))
                .foregroundStyle(.secondary)
            Text("Couldn't load the board")
                .font(.headline)
            if let lastError = store.lastError {
                Text(lastError)
                    .font(.footnote)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
            }
            Button("Try Again") {
                Task { await store.refresh() }
            }
            .buttonStyle(.borderedProminent)
            .padding(.top, 4)
        }
        .padding(.top, 120)
    }
}
