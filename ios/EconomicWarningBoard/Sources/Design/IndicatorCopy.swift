import Foundation

/// Static, spec-frozen copy the board.json payload deliberately doesn't carry
/// every day: the one-sentence "what is this?" per indicator (mirrors
/// evaluate.py's WHAT_IS_THIS) and short tile labels (the detail screen's
/// `name` is already the full descriptive form; tiles need something
/// shorter -- "Temp Help", not "Temporary help employment"). Keep in sync
/// with the backend by hand -- both are frozen alongside the spec, not data
/// that changes daily. threshold/position/direction now come from the
/// server (evaluate.py's threshold_value/compute_position) rather than
/// being duplicated here.
enum IndicatorCopy {
    static let shortName: [Int: String] = [
        1: "Yield Curve", 2: "HY Spread", 3: "Baa Spread", 4: "NFCI",
        5: "STL Stress", 6: "Lending Standards", 7: "Equity Drawdown",
        8: "CFNAI", 9: "Industrial Prod.", 10: "Truck Sales",
        11: "Building Permits", 12: "Capex Orders", 13: "Temp Help",
        14: "Loan Delinquency", 15: "Jobless Claims", 16: "Continuing Claims",
        17: "Sahm Rule", 18: "CC Delinquency", 19: "Mortgage Delinq.",
        20: "Retail Sales",
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
}
