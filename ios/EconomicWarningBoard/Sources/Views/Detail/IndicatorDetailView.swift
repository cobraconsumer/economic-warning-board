import SwiftUI

/// Answers exactly five questions, in order, per spec 7.3. The why-callout
/// is the anti-confirmation-bias feature: a clear indicator gets the same
/// card, same weight, same five questions as a flagged one -- this screen
/// must never be a reduced version of itself based on state.
struct IndicatorDetailView: View {
    let indicator: Indicator

    var body: some View {
        AmbientBackground {
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    heroCard

                    questionBlock("What is this?") {
                        Text(IndicatorCopy.whatIsThis[indicator.id] ?? indicator.name)
                    }
                    divider

                    questionBlock("What is it now?") {
                        VStack(alignment: .leading, spacing: 4) {
                            HStack(alignment: .firstTextBaseline, spacing: 6) {
                                Text(indicator.tileValueText)
                                    .font(.title3.weight(.bold))
                                    .foregroundStyle(EWB.ink)
                                Text(indicator.unit)
                                    .font(.subheadline)
                                    .foregroundStyle(EWB.ink3)
                                if let observationDate = indicator.observationDate,
                                   let formatted = DateFormatting.dayMonthYear(observationDate) {
                                    Text("as of \(formatted)")
                                        .font(.footnote)
                                        .foregroundStyle(EWB.ink3)
                                }
                            }
                            if let observationDate = indicator.observationDate,
                               let age = DateFormatting.dataAgeText(observationDate) {
                                Text(age.uppercased())
                                    .font(.caption2.weight(.bold))
                                    .tracking(1)
                                    .foregroundStyle(EWB.ink3)
                            }
                        }
                    }
                    divider

                    questionBlock("What makes it red?") {
                        Text(indicator.thresholdText)
                    }
                    divider

                    questionBlock("How long in this state?") {
                        Text(durationText)
                    }
                    divider

                    DistanceBar(indicator: indicator)

                    if let legs = indicator.legs, legs.count > 1 {
                        legsSection(legs)
                    }

                    whyCallout

                    divider

                    HStack(alignment: .top) {
                        VStack(alignment: .leading, spacing: 2) {
                            Text("SOURCE")
                                .font(.caption2.weight(.bold))
                                .tracking(1.6)
                                .foregroundStyle(EWB.ink3)
                            Text(indicator.sourceName)
                                .font(.footnote)
                                .foregroundStyle(EWB.ink2)
                        }
                        Spacer()
                        if let url = URL(string: indicator.sourceUrl) {
                            Link("View on FRED ↗", destination: url)
                                .font(.footnote.weight(.semibold))
                                .foregroundStyle(indicator.bucket.textColor)
                        }
                    }
                }
                .padding(.horizontal, Metrics.screenPadding)
                .padding(.top, 12)
                .padding(.bottom, 40)
            }
            .scrollContentBackground(.hidden)
        }
        .navigationTitle(indicator.name)
        .navigationBarTitleDisplayMode(.inline)
    }

    private var heroCard: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text(indicator.bucket.label.uppercased())
                .font(.caption2.weight(.bold))
                .tracking(1.6)
                .foregroundStyle(EWB.ink3)

            HStack(alignment: .top) {
                Text(indicator.name)
                    .font(.title3.weight(.bold))
                    .foregroundStyle(EWB.ink)
                Spacer()
                StateDot(state: indicator.state, bucket: indicator.bucket, size: Metrics.dotLarge)
            }

            HStack(alignment: .firstTextBaseline, spacing: 6) {
                Text(indicator.tileValueText)
                    .font(.system(size: 42, weight: .bold))
                    .minimumScaleFactor(0.5)
                    .monospacedDigit()
                    .foregroundStyle(indicator.state == .red ? EWB.broadText : indicator.bucket.textColor)
                Text(indicator.unit)
                    .font(.subheadline)
                    .foregroundStyle(EWB.ink3)
            }

            if !indicator.sparkline.isEmpty {
                SparklineChart(
                    values: indicator.sparkline,
                    thresholdValue: indicator.threshold,
                    color: indicator.state == .red ? EWB.broadText : indicator.bucket.textColor
                )
                .frame(height: 70)
            }
        }
        .padding(20)
        .frame(maxWidth: .infinity, alignment: .leading)
        .glassCard(radius: Radius.hero)
    }

    private var divider: some View {
        Rectangle().fill(EWB.stroke).frame(height: 1)
    }

    /// Only for compound rules (legs.count > 1) -- `position` measures one
    /// leg, but the state can be decided by another entirely, so this is
    /// what actually explains the discrepancy the distance bar can't:
    /// #18 sits at 93% of its level leg but stays green because "rising"
    /// hasn't fired; #1 reads clear at the level leg but is red on the
    /// lookback leg alone. spec-v0.6-tile-information.md section 5.
    private func legsSection(_ legs: [Leg]) -> some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("THE FULL PICTURE")
                .font(.caption2.weight(.bold))
                .tracking(1.6)
                .foregroundStyle(EWB.ink3)
            ForEach(legs, id: \.name) { leg in
                HStack(alignment: .top, spacing: 10) {
                    Image(systemName: leg.met ? "checkmark.circle.fill" : "circle")
                        .font(.footnote)
                        .foregroundStyle(leg.met ? indicator.bucket.textColor : EWB.ink3)
                    VStack(alignment: .leading, spacing: 1) {
                        Text(leg.name.capitalized)
                            .font(.caption.weight(.semibold))
                            .foregroundStyle(EWB.ink)
                        Text(leg.text)
                            .font(.footnote)
                            .foregroundStyle(EWB.ink2)
                    }
                    if leg.name == indicator.bindingLeg {
                        Spacer()
                        Text("DECIDING")
                            .font(.caption2.weight(.bold))
                            .tracking(1)
                            .foregroundStyle(indicator.state == .red ? EWB.broadText : indicator.bucket.textColor)
                    }
                }
            }
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .overlay(RoundedRectangle(cornerRadius: Radius.card).strokeBorder(EWB.stroke2, lineWidth: 1))
    }

    private var whyCallout: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(calloutHeading.uppercased())
                .font(.caption2.weight(.bold))
                .tracking(1.6)
                .foregroundStyle(calloutColor)
            Text(indicator.whyText)
                .font(.subheadline)
                .foregroundStyle(EWB.ink2)
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .glassCard()
    }

    private var calloutHeading: String {
        switch indicator.state {
        case .green: return "Why it is clear"
        case .red: return "Why it is flagged"
        case .unavailable: return "Why it is excluded"
        }
    }

    private var calloutColor: Color {
        switch indicator.state {
        case .green: return indicator.bucket.textColor
        case .red: return EWB.broadText
        case .unavailable: return EWB.ink3
        }
    }

    private var durationText: String {
        let coarse = DateFormatting.daysInStateText(indicator.daysInState)
        return "\(coarse) \(indicator.accessibilityStateWord) · \(indicator.daysInState) days"
    }

    @ViewBuilder
    private func questionBlock<Content: View>(
        _ title: String, @ViewBuilder content: () -> Content
    ) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(title.uppercased())
                .font(.caption2.weight(.bold))
                .tracking(1.6)
                .foregroundStyle(EWB.ink3)
            content()
                .font(.subheadline)
                .foregroundStyle(EWB.ink2)
        }
    }
}
