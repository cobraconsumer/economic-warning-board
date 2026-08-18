import Foundation

enum DateFormatting {
    private static let isoDateOnly: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "yyyy-MM-dd"
        f.timeZone = TimeZone(identifier: "UTC")
        return f
    }()

    private static let monthYearFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "MMMM yyyy"
        return f
    }()

    private static let dayMonthYearFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "d MMM yyyy"
        return f
    }()

    static func date(fromISODateOnly string: String) -> Date? {
        isoDateOnly.date(from: string)
    }

    static func monthYear(_ isoDateOnlyString: String) -> String? {
        guard let d = date(fromISODateOnly: isoDateOnlyString) else { return nil }
        return monthYearFormatter.string(from: d)
    }

    static func dayMonthYear(_ isoDateOnlyString: String) -> String? {
        guard let d = date(fromISODateOnly: isoDateOnlyString) else { return nil }
        return dayMonthYearFormatter.string(from: d)
    }

    static func dayMonthYear(_ date: Date) -> String {
        dayMonthYearFormatter.string(from: date)
    }

    static func daysInStateText(_ days: Int) -> String {
        if days < 60 {
            return "\(days) day\(days == 1 ? "" : "s")"
        }
        let months = days / 30
        return "\(months) month\(months == 1 ? "" : "s")"
    }
}
