import SwiftUI

/// Answers exactly five questions, in order, per spec 2.2. The why_text card
/// at the bottom is the anti-confirmation-bias feature: it explains green
/// states with the same weight as red ones.
struct IndicatorDetailView: View {
    let indicator: Indicator

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 28) {
                header

                if !indicator.sparkline.isEmpty {
                    SparklineChart(
                        values: indicator.sparkline,
                        thresholdValue: IndicatorCopy.thresholdLine[indicator.id]
                    )
                }

                DistanceToThresholdBar(indicator: indicator)

                question("What is this?") {
                    Text(IndicatorCopy.whatIsThis[indicator.id] ?? indicator.name)
                }

                question("What is it now?") {
                    VStack(alignment: .leading, spacing: 3) {
                        Text(valueText)
                            .font(.title3.weight(.semibold))
                        if let observationDate = indicator.observationDate,
                           let formatted = DateFormatting.dayMonthYear(observationDate) {
                            Text("as of \(formatted)")
                                .font(.footnote)
                                .foregroundStyle(.secondary)
                        }
                        if let observationDate = indicator.observationDate,
                           let age = DateFormatting.dataAgeText(observationDate) {
                            Text(age)
                                .font(.footnote)
                                .foregroundStyle(.orange)
                        }
                    }
                }

                question("What makes it red?") {
                    Text(indicator.thresholdText)
                }

                question("How long has it been in this state?") {
                    Text(DateFormatting.daysInStateText(indicator.daysInState))
                }

                question("Where does this come from?") {
                    VStack(alignment: .leading, spacing: 6) {
                        Text(indicator.sourceName)
                        if let url = URL(string: indicator.sourceUrl) {
                            Link("View on FRED ↗", destination: url)
                        }
                    }
                }

                whyCard
            }
            .padding(20)
        }
        .navigationTitle(indicator.name)
        .navigationBarTitleDisplayMode(.inline)
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text((IndicatorCopy.bucketLabels[indicator.bucket] ?? indicator.bucket).uppercased())
                .font(.system(size: 12, weight: .semibold))
                .tracking(1)
                .foregroundStyle(.secondary)
            HStack(spacing: 8) {
                DotView(state: indicator.state)
                Text(indicator.state.rawValue.capitalized)
                    .font(.subheadline.weight(.medium))
                    .foregroundStyle(indicator.state == .red ? Tier.broad.color : .secondary)
            }
        }
    }

    private var whyCard: some View {
        Text(indicator.whyText)
            .font(.callout)
            .padding(16)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(
                (indicator.state == .red ? Tier.broad.color : Color.green).opacity(0.08),
                in: RoundedRectangle(cornerRadius: 12)
            )
    }

    private var valueText: String {
        guard let value = indicator.value else { return "Unavailable" }
        return String(format: "%.2f %@", value, indicator.unit)
    }

    @ViewBuilder
    private func question<Content: View>(
        _ title: String, @ViewBuilder content: () -> Content
    ) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title)
                .font(.subheadline.weight(.semibold))
                .foregroundStyle(.secondary)
            content()
        }
    }
}
