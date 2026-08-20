import SwiftUI

/// The demotion here is structural, not cosmetic: these items get no dot, no
/// tile, no category color, because a dot signals a state and something
/// without a threshold has no state to report. Spec 7.5.
struct WatchlistView: View {
    @EnvironmentObject private var store: BoardStore
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        AmbientBackground {
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    Text("Three things worth watching, none of which count.")
                        .font(.title.weight(.bold))
                        .foregroundStyle(EWB.ink)

                    explainer

                    if let items = store.board?.watchlist, !items.isEmpty {
                        ForEach(Array(items.enumerated()), id: \.element.id) { index, item in
                            watchRow(item)
                            if index < items.count - 1 {
                                Rectangle().fill(EWB.stroke).frame(height: 1)
                            }
                        }
                        Rectangle().fill(EWB.stroke).frame(height: 1)
                        Text("If one of these accumulates enough history to be tested properly, it will be promoted to the twenty and the change will be recorded in the methodology.")
                            .font(.footnote)
                            .foregroundStyle(EWB.ink3)
                    } else {
                        Text("No watchlist data available right now.")
                            .font(.subheadline)
                            .foregroundStyle(EWB.ink3)
                    }
                }
                .padding(.horizontal, Metrics.screenPadding)
                .padding(.top, 12)
                .padding(.bottom, 40)
            }
            .scrollContentBackground(.hidden)
        }
        .navigationTitle("Context")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button("Done") { dismiss() }
                    .tint(EWB.ink2)
            }
        }
    }

    private var explainer: some View {
        HStack(alignment: .top, spacing: 10) {
            Image(systemName: "exclamationmark.circle")
                .foregroundStyle(EWB.ink3)
            Text("These are **not part of the count**. None has enough backtested history to earn a threshold, so none has a red or green state and none can move the number on the board. They are here because ignoring them would be dishonest, not because they are evidence.")
                .font(.subheadline)
                .foregroundStyle(EWB.ink2)
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .overlay(RoundedRectangle(cornerRadius: Radius.card).strokeBorder(EWB.stroke2, lineWidth: 1))
    }

    private func watchRow(_ item: WatchlistItem) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 2) {
                    Text(item.name)
                        .font(.headline)
                        .foregroundStyle(EWB.ink)
                    Text(item.unit)
                        .font(.footnote)
                        .foregroundStyle(EWB.ink3)
                }
                Spacer()
                if let value = item.value {
                    Text(formattedValue(value, unit: item.unit))
                        .font(.title3.weight(.semibold).monospacedDigit())
                        .foregroundStyle(EWB.ink2)
                }
            }

            if !item.sparkline.isEmpty {
                SparklineChart(values: item.sparkline, thresholdValue: nil, color: EWB.ink3, dimmed: true)
                    .frame(height: 40)
            }

            Text(item.whatIsThis)
                .font(.subheadline)
                .foregroundStyle(EWB.ink2)

            Link(destination: URL(string: item.sourceUrl) ?? URL(string: "https://fred.stlouisfed.org")!) {
                Text("\(item.sourceName) →")
                    .font(.footnote)
                    .foregroundStyle(EWB.ink3)
            }
        }
    }

    private func formattedValue(_ value: Double, unit: String) -> String {
        let formatter = NumberFormatter()
        formatter.numberStyle = .decimal
        formatter.maximumFractionDigits = unit == "$ billions" ? 1 : (abs(value) >= 100 ? 0 : 2)
        return formatter.string(from: NSNumber(value: value)) ?? "\(value)"
    }
}
