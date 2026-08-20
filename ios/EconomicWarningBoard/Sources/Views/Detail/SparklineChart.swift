import SwiftUI

/// Plain SwiftUI Path, not Swift Charts -- up to 21 of these can be live at
/// once (Methodology's history-adjacent indicators, Board's wide rows), and
/// Chart carries real per-instance overhead for what's a polyline with no
/// axes, legend, or interaction. Swift Charts is reserved for Methodology's
/// history chart, which is one instance and benefits from real axis
/// handling. Spec 5.5.
struct SparklineChart: View {
    let values: [Double]
    let thresholdValue: Double?
    var color: Color = EWB.ink
    var dimmed: Bool = false

    var body: some View {
        GeometryReader { geo in
            let w = geo.size.width
            let h = max(geo.size.height, 1)
            if values.count > 1 {
                let lo = min(values.min() ?? 0, thresholdValue ?? .greatestFiniteMagnitude)
                let hi = max(values.max() ?? 0, thresholdValue ?? -.greatestFiniteMagnitude)
                let span = max(hi - lo, 0.0001)

                ZStack {
                    if let thresholdValue {
                        let ty = h - CGFloat((thresholdValue - lo) / span) * h
                        Path { p in
                            p.move(to: CGPoint(x: 0, y: ty))
                            p.addLine(to: CGPoint(x: w, y: ty))
                        }
                        .stroke(EWB.ink3, style: StrokeStyle(lineWidth: 1, dash: [3, 3]))
                    }

                    Path { p in
                        for (i, v) in values.enumerated() {
                            let x = CGFloat(i) / CGFloat(values.count - 1) * w
                            let y = h - CGFloat((v - lo) / span) * h
                            if i == 0 { p.move(to: CGPoint(x: x, y: y)) }
                            else { p.addLine(to: CGPoint(x: x, y: y)) }
                        }
                    }
                    .stroke(color.opacity(dimmed ? 0.5 : 1), style: StrokeStyle(lineWidth: 2, lineCap: .round, lineJoin: .round))

                    if let last = values.last {
                        let ly = h - CGFloat((last - lo) / span) * h
                        Circle()
                            .fill(color.opacity(dimmed ? 0.5 : 1))
                            .frame(width: 5, height: 5)
                            .position(x: w, y: ly)
                    }
                }
            }
        }
    }
}
