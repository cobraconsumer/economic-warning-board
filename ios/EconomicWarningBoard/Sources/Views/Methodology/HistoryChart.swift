import Charts
import SwiftUI

struct HistoryChart: View {
    let history: [HistoryPoint]

    private struct Recession {
        let name: String
        let start: Date
        let end: Date
    }

    private static let recessions: [Recession] = [
        Recession(name: "1990-91", start: date("1990-07-01"), end: date("1991-03-01")),
        Recession(name: "2001", start: date("2001-03-01"), end: date("2001-11-01")),
        Recession(name: "2007-09", start: date("2007-12-01"), end: date("2009-06-01")),
        Recession(name: "2020", start: date("2020-02-01"), end: date("2020-04-01")),
    ]

    private static func date(_ s: String) -> Date {
        DateFormatting.date(fromISODateOnly: s) ?? .distantPast
    }

    private var points: [(date: Date, fraction: Double)] {
        history.compactMap { point in
            guard let d = DateFormatting.date(fromISODateOnly: point.date) else { return nil }
            return (d, point.fraction * 100)
        }
    }

    var body: some View {
        Chart {
            ForEach(Self.recessions, id: \.name) { recession in
                RectangleMark(xStart: .value("Start", recession.start), xEnd: .value("End", recession.end))
                    .foregroundStyle(Color(.systemGray5))
            }
            ForEach(points, id: \.date) { point in
                LineMark(x: .value("Date", point.date), y: .value("% red", point.fraction))
                    .foregroundStyle(Color(.label))
                    .lineStyle(StrokeStyle(lineWidth: 1.3))
            }
            RuleMark(y: .value("Watch", 25))
                .foregroundStyle(Tier.watch.color.opacity(0.5))
                .lineStyle(StrokeStyle(lineWidth: 1, dash: [3, 3]))
            RuleMark(y: .value("Warning", 40))
                .foregroundStyle(Tier.warning.color.opacity(0.5))
                .lineStyle(StrokeStyle(lineWidth: 1, dash: [3, 3]))
            RuleMark(y: .value("Broad", 60))
                .foregroundStyle(Tier.broad.color.opacity(0.5))
                .lineStyle(StrokeStyle(lineWidth: 1, dash: [3, 3]))
        }
        .chartYAxisLabel("% of indicators red")
        .chartYScale(domain: 0...100)
        .frame(height: 220)
    }
}
