import Charts
import SwiftUI

/// The one place in the app that uses Swift Charts rather than the plain
/// Path sparkline -- one instance, benefits from real axis handling. Spec
/// 7.4. Recession shading uses `ink` at low opacity, deliberately not red:
/// the bands are context, not warnings.
struct HistoryChart: View {
    let history: [HistoryPoint]
    let watchFraction: Double

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
                    .foregroundStyle(EWB.ink.opacity(0.085))
            }
            ForEach(points, id: \.date) { point in
                AreaMark(x: .value("Date", point.date), y: .value("% flagged", point.fraction))
                    .foregroundStyle(EWB.broadMark.opacity(0.12))
                LineMark(x: .value("Date", point.date), y: .value("% flagged", point.fraction))
                    .foregroundStyle(EWB.broadText)
                    .lineStyle(StrokeStyle(lineWidth: 1.3))
            }
            RuleMark(y: .value("Watch threshold", watchFraction * 100))
                .foregroundStyle(EWB.ink3)
                .lineStyle(StrokeStyle(lineWidth: 1, dash: [3, 3]))
        }
        .chartYAxis {
            AxisMarks(position: .leading) { _ in
                AxisGridLine().foregroundStyle(EWB.stroke)
                AxisValueLabel().foregroundStyle(EWB.ink3)
            }
        }
        .chartXAxis {
            AxisMarks { _ in
                AxisValueLabel().foregroundStyle(EWB.ink3)
            }
        }
        .chartYScale(domain: 0...100)
        .frame(height: 200)
    }
}
