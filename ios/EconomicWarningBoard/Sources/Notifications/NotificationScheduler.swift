import Foundation
import UserNotifications

/// Local notifications only, fired on tier change alone -- never on
/// individual indicator changes, per spec 2.4. Copy is factual, not urgent.
@MainActor
final class NotificationScheduler {
    static let shared = NotificationScheduler()
    private init() {}

    func requestAuthorizationIfNeeded() {
        let center = UNUserNotificationCenter.current()
        center.getNotificationSettings { settings in
            guard settings.authorizationStatus == .notDetermined else { return }
            center.requestAuthorization(options: [.alert, .sound, .badge]) { _, _ in }
        }
    }

    func notifyTierChange(from previous: Tier, to summary: BoardSummary, history: [HistoryPoint]) {
        let content = UNMutableNotificationContent()
        content.title = "Economic Warning Board"
        content.body = copy(from: previous, to: summary, history: history)
        content.sound = .default

        let identifier = "tier-change-\(summary.tier.rawValue)-\(summary.tierSince)"
        let request = UNNotificationRequest(identifier: identifier, content: content, trigger: nil)
        UNUserNotificationCenter.current().add(request)
    }

    private func copy(from previous: Tier, to summary: BoardSummary, history: [HistoryPoint]) -> String {
        guard summary.tier.severity > previous.severity else {
            return "Down to \(summary.reds) of \(summary.available) — conditions have improved."
        }
        var text = "\(summary.reds) of \(summary.available) indicators are now red."
        if let since = monthOfMostRecentEqualOrHigherReading(fraction: summary.fraction, history: history) {
            text += " The most since \(since)."
        }
        return text
    }

    private func monthOfMostRecentEqualOrHigherReading(fraction: Double, history: [HistoryPoint]) -> String? {
        guard history.count > 1 else { return nil }
        let past = history.dropLast()
        guard let match = past.reversed().first(where: { $0.fraction >= fraction }) else { return nil }
        return DateFormatting.monthYear(match.date)
    }
}
