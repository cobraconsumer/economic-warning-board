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
    let buckets: [String: Bucket]
    let ignitionActive: Bool
}

struct Bucket: Decodable, Hashable {
    let red: Int
    let available: Int
    let label: String
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
}

enum IndicatorState: String, Decodable, Hashable {
    case red, green, unavailable
}

struct Indicator: Decodable, Identifiable, Hashable {
    let id: Int
    let name: String
    let bucket: String
    let role: String
    let state: IndicatorState
    let value: Double?
    let unit: String
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

extension Bucket {
    static let order = ["A", "B", "C"]
}
