import Foundation

struct Board: Decodable {
    let generatedAt: Date
    let specVersion: String
    let specHash: String
    let board: BoardSummary
    let indicators: [Indicator]
    let history: [HistoryPoint]
    let watchlist: [WatchlistItem]?
}

struct BoardSummary: Decodable {
    let reds: Int
    let available: Int
    let fraction: Double
    let tier: Tier
    let tierSince: String
    let buckets: [String: BucketSummary]
    let ignitionActive: Bool
}

/// Per-bucket score counts, keyed by Bucket.rawValue ("A"/"B"/"C") in
/// BoardSummary.buckets. Not to be confused with `Bucket`, the category enum.
struct BucketSummary: Decodable, Hashable {
    let red: Int
    let available: Int
    let label: String
}

/// Category. Rides directly on the server's existing "A"/"B"/"C" indicator.bucket
/// string -- no schema change needed, just a typed wrapper around it.
enum Bucket: String, Decodable, Hashable, CaseIterable {
    case financial = "A"
    case business = "B"
    case household = "C"

    static let order: [Bucket] = [.financial, .business, .household]

    var label: String {
        switch self {
        case .financial: return "Financial & Credit"
        case .business: return "Business"
        case .household: return "Household & Labor"
        }
    }
}

enum Tier: String, Decodable, Hashable, CaseIterable {
    case quiet = "QUIET"
    case watch = "WATCH"
    case warning = "WARNING"
    case broad = "BROAD"

    /// Escalation order, low to high. Used to tell an escalating tier change
    /// from a de-escalating one for notification copy.
    var severity: Int {
        switch self {
        case .quiet: return 0
        case .watch: return 1
        case .warning: return 2
        case .broad: return 3
        }
    }

    var explanation: String {
        switch self {
        case .quiet:
            return "No unusual conditions. Most of history looks like this."
        case .watch:
            return "Early signs are showing up. Historically the tier that matters most — it has led every recession studied by 4 to 12 months."
        case .warning:
            return "Conditions have broadened. Historically arrives at or near the start of a downturn, not far ahead of it."
        case .broad:
            return "Red across most of the board. Has not occurred outside an actual recession in the 35 years studied."
        }
    }
}

enum IndicatorState: String, Decodable, Hashable {
    case red, green, unavailable
}

/// One sub-condition of a compound rule -- e.g. level_and_rising's "level"
/// and "rising" legs. See evaluate.py's compute_legs. spec-v0.6-tile-
/// information.md section 5.
struct Leg: Decodable, Hashable {
    let name: String
    let met: Bool
    let text: String
}

struct Indicator: Decodable, Identifiable, Hashable {
    let id: Int
    let name: String
    let bucket: Bucket
    let role: String
    let state: IndicatorState
    let value: Double?
    let unit: String
    /// 1.0 == exactly at threshold, 0 == the metric's own historical typical
    /// level, >1.0 == past it. Server-computed; see evaluate.py's
    /// compute_position. nil only for indicators fetched before this field
    /// shipped (stale cache).
    let threshold: Double?
    let position: Double?
    /// Compound-rule breakdown -- nil or single-element for simple rules.
    /// `position` only ever measures `positionBasis`; the actual state can
    /// be decided by a different leg entirely (evaluate.py's compute_legs).
    let legs: [Leg]?
    /// For a red indicator, the leg that fired it; for green, the unmet leg
    /// keeping it that way. nil on cache predating this field.
    let bindingLeg: String?
    /// Which leg `position`/the distance bar actually measures.
    let positionBasis: String?
    let thresholdText: String
    let whyText: String
    let observationDate: String?
    let daysInState: Int
    let sourceName: String
    let sourceUrl: String
    let sparkline: [Double]
}

/// Context, not part of the scored board -- see spec-v0.5-candidates.md
/// section 4. No rule, no red/green, never counted in reds/available/fraction.
struct WatchlistItem: Decodable, Identifiable, Hashable {
    let id: String
    let name: String
    let unit: String
    let whatIsThis: String
    let value: Double?
    let observationDate: String?
    let sparkline: [Double]
    let sourceName: String
    let sourceUrl: String
}

struct HistoryPoint: Decodable, Identifiable, Hashable {
    let date: String
    let fraction: Double
    let tier: Tier
    var id: String { date }
}
