import SwiftUI

/// Context, not part of the scored board -- per spec-v0.5-candidates.md
/// section 4, this must render as a visually distinct, clearly labeled
/// section and never imply these items carry the same weight as the 20
/// scored indicators.
struct WatchlistView: View {
    @EnvironmentObject private var store: BoardStore
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                disclaimer

                if let items = store.board?.watchlist, !items.isEmpty {
                    ForEach(items) { item in
                        WatchlistRow(item: item)
                    }
                } else {
                    Text("No watchlist data available right now.")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
            }
            .padding(20)
        }
        .navigationTitle("Context")
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button("Done") { dismiss() }
            }
        }
    }

    private var disclaimer: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Not part of the scored board")
                .font(.headline)
            Text("These readings are public, free, and timely, but don't yet have enough history to be backtested across three or more recessions the way the 20 scored indicators are. They never affect the count, the tier, or any notification.")
                .font(.footnote)
                .foregroundStyle(.secondary)
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(.secondarySystemBackground), in: RoundedRectangle(cornerRadius: 14))
    }
}

private struct WatchlistRow: View {
    let item: WatchlistItem

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(item.name)
                .font(.headline)

            if !item.sparkline.isEmpty {
                SparklineChart(values: item.sparkline, thresholdValue: nil)
                    .frame(height: 70)
            }

            if let value = item.value {
                VStack(alignment: .leading, spacing: 2) {
                    Text(formattedValue(value))
                        .font(.title3.weight(.semibold))
                    if let date = item.observationDate,
                       let formatted = DateFormatting.dayMonthYear(date) {
                        Text("as of \(formatted)")
                            .font(.footnote)
                            .foregroundStyle(.secondary)
                    }
                }
            }

            Text(item.whatIsThis)
                .font(.callout)
                .foregroundStyle(.secondary)

            HStack(spacing: 6) {
                Text(item.sourceName)
                if let url = URL(string: item.sourceUrl) {
                    Link("View on FRED ↗", destination: url)
                }
            }
            .font(.footnote)
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color(.secondarySystemBackground), in: RoundedRectangle(cornerRadius: 14))
    }

    private func formattedValue(_ value: Double) -> String {
        if item.unit == "applications" || item.unit == "$ billions" {
            let formatter = NumberFormatter()
            formatter.numberStyle = .decimal
            formatter.maximumFractionDigits = item.unit == "$ billions" ? 1 : 0
            let number = formatter.string(from: NSNumber(value: value)) ?? "\(value)"
            return "\(number) \(item.unit)"
        }
        return String(format: "%.2f %@", value, item.unit)
    }
}
