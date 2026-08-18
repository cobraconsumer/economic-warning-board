import Charts
import SwiftUI

struct SparklineChart: View {
    let values: [Double]
    let thresholdValue: Double?

    var body: some View {
        Chart {
            ForEach(Array(values.enumerated()), id: \.offset) { index, value in
                LineMark(x: .value("Index", index), y: .value("Value", value))
                    .interpolationMethod(.monotone)
                    .foregroundStyle(Color(.label))
                    .lineStyle(StrokeStyle(lineWidth: 2))
            }
            if let thresholdValue {
                RuleMark(y: .value("Threshold", thresholdValue))
                    .foregroundStyle(Color(.systemGray3))
                    .lineStyle(StrokeStyle(lineWidth: 1, dash: [4, 3]))
            }
        }
        .chartXAxis(.hidden)
        .chartYAxis(.hidden)
        .frame(height: 100)
    }
}
