import Foundation

/// Static, spec-frozen copy the board.json payload deliberately doesn't carry
/// every day: the one-sentence "what is this?" per indicator (mirrors
/// evaluate.py's WHAT_IS_THIS) and the numeric threshold line drawn on each
/// sparkline (mirrors spec_v03.json's already-scaled params, in the same
/// units as evaluate.py's metric_series). Keep in sync with the backend by
/// hand -- both are frozen alongside the spec, not data that changes daily.
enum IndicatorCopy {
    static let bucketLabels: [String: String] = [
        "A": "Financial & Credit",
        "B": "Business",
        "C": "Household & Labor",
    ]

    static let whatIsThis: [Int: String] = [
        1: "The gap between the 10-year and 3-month Treasury yields. When investors expect trouble, short-term rates can rise above long-term rates and the curve “inverts.”",
        2: "The extra yield investors demand to hold risky (“junk”) corporate bonds over safe Treasurys. It widens when credit markets get nervous.",
        3: "The extra yield investment-grade Baa-rated corporate bonds pay over 10-year Treasurys — a broader read on credit stress than high-yield alone.",
        4: "The Chicago Fed's National Financial Conditions Index, a broad gauge of how loose or tight financial conditions are across money, debt, and equity markets. Zero is the long-run average.",
        5: "The St. Louis Fed Financial Stress Index, built from dozens of interest rates, spreads, and volatility measures. Zero is normal stress; positive means more than average.",
        6: "The net share of banks reporting they tightened lending standards on commercial and industrial loans, from the Fed's quarterly Senior Loan Officer survey.",
        7: "How far the S&P 500 has fallen from its highest close in the past year. A confirming signal, not a leading one — markets often drop only after the economy is already stressed.",
        8: "The Chicago Fed National Activity Index, a blend of 85 economic indicators, averaged over three months. Zero means growth at trend; negative means below-trend growth.",
        9: "Total US factory, mining, and utility output, compared with a year earlier.",
        10: "Sales of heavy (Class 8) trucks — a classic early-cycle indicator, since fleets stop replacing trucks when they expect less freight to move.",
        11: "New residential building permits issued nationwide, compared with a year earlier — one of the most reliably leading housing indicators.",
        12: "New orders for non-defense capital goods excluding aircraft — a proxy for business investment plans.",
        13: "Employment at temp-staffing agencies. Companies often cut temp workers first, before permanent layoffs, making this an early labor-market signal.",
        14: "The delinquency rate on commercial & industrial loans at all US banks.",
        15: "New unemployment claims, averaged over four weeks. A lagging confirmation signal — it tends to rise only after job losses are already underway.",
        16: "The number of people continuing to receive unemployment benefits, compared with a year earlier.",
        17: "The Sahm Rule: the 3-month average unemployment rate compared with its low over the prior 12 months. Historically reliable, if late.",
        18: "The delinquency rate on credit card balances at commercial banks.",
        19: "The delinquency rate on single-family residential mortgages at commercial banks.",
        20: "Retail sales adjusted for inflation, compared with a year earlier.",
    ]

    /// Horizontal threshold-line value for each indicator's sparkline, in the
    /// same metric units evaluate.py's metric_series computes (so the line
    /// and the plotted values always line up).
    static let thresholdLine: [Int: Double] = [
        1: 0.0, 2: 4.75, 3: 2.375, 4: 0.0, 5: 0.95, 6: 19.0, 7: -14.25,
        8: -0.3325, 9: -0.95, 10: -19.0, 11: -9.5, 12: -1.9, 13: -2.85,
        14: 1.9, 15: 19.0, 16: 14.25, 17: 0.4999, 18: 2.85, 19: 2.375, 20: 0.0,
    ]
}
