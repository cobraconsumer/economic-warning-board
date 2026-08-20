import SwiftUI

extension UIColor {
    convenience init(hex: UInt32) {
        self.init(
            red: CGFloat((hex >> 16) & 0xFF) / 255,
            green: CGFloat((hex >> 8) & 0xFF) / 255,
            blue: CGFloat(hex & 0xFF) / 255,
            alpha: 1
        )
    }
}

extension Color {
    init(light: UInt32, dark: UInt32) {
        self.init(UIColor { $0.userInterfaceStyle == .dark ? UIColor(hex: dark) : UIColor(hex: light) })
    }
}

/// Design tokens for the v2 UI. Every semantic color ships as a pair --
/// `mark` for dots/bars/borders/fills (WCAG 3:1), `text` for anything with a
/// glyph including thin sparkline strokes (WCAG 4.5:1). See
/// economic-warning-board-handoff/IMPLEMENTATION-SPEC.md section 2 for the
/// full rationale and contrast-check.py for the verification these values
/// are built against. Two tokens (hhMark light, quietMark light) have almost
/// no headroom -- do not hand-tune these without re-running the contrast check.
enum EWB {
    // MARK: Surface
    static let bg = Color(light: 0xF3F4F8, dark: 0x07080B)
    static let bgRaise = Color(light: 0xFFFFFF, dark: 0x101319)

    // MARK: Text ramp -- alphas differ per theme; never `.opacity()` these,
    // that applies one alpha to both sides and light mode fails contrast.
    static func ramp(_ lightAlpha: CGFloat, _ darkAlpha: CGFloat) -> Color {
        Color(UIColor { $0.userInterfaceStyle == .dark
            ? UIColor(white: 1, alpha: darkAlpha)
            : UIColor(red: 13 / 255, green: 15 / 255, blue: 21 / 255, alpha: lightAlpha) })
    }
    static let ink = Color(light: 0x0D0F15, dark: 0xFFFFFF)
    static let ink2 = ramp(0.72, 0.70)
    static let ink3 = ramp(0.58, 0.48)
    static let ink4 = ramp(0.46, 0.42)

    // MARK: Category -- blue, three steps
    static let finMark = Color(light: 0x0E3A8C, dark: 0x1F5FD4)
    static let finText = Color(light: 0x0E3A8C, dark: 0x3774E2)
    static let bizMark = Color(light: 0x1C64C4, dark: 0x5CA3F2)
    static let bizText = Color(light: 0x175AB3, dark: 0x5CA3F2)
    static let hhMark = Color(light: 0x3C8CE8, dark: 0xA9D8FF)
    static let hhText = Color(light: 0x1A6FC4, dark: 0xA9D8FF)

    // MARK: Tier -- green/teal/yellow/red, one distinct hue per tier so
    // adjacent tiers read apart at a glance. Every pair is checked against
    // both backgrounds (mark 3:1, text 4.5:1); light-mode warn in particular
    // has to run much darker than it looks like it should, since a bright
    // yellow simply cannot pass contrast on a near-white background.
    static let quietMark = Color(light: 0x1E9A4C, dark: 0x30D982)
    static let quietText = Color(light: 0x14793B, dark: 0x30D982)
    static let watchMark = Color(light: 0x0C8FA6, dark: 0x22D3EE)
    static let watchText = Color(light: 0x086E80, dark: 0x22D3EE)
    static let warnMark = Color(light: 0xA9840F, dark: 0xFACC15)
    static let warnText = Color(light: 0x7A5E12, dark: 0xFACC15)
    static let broadMark = Color(light: 0xC22B20, dark: 0xF04438)
    static let broadText = Color(light: 0xC22B20, dark: 0xF97066)

    // MARK: Tier, muted -- the hero count reads better in a quieter tone
    // than the vivid mark/text pair above; those stay for the chip, ladder,
    // and dots, where the point is separation at a glance.
    static let quietCount = Color(light: 0x667084, dark: 0x8A93A5)
    static let watchCount = Color(light: 0xAB5744, dark: 0xC47B6B)
    static let warnCount = Color(light: 0xB84D42, dark: 0xC4645A)
    static let broadCount = Color(light: 0xBC3E35, dark: 0xCB5048)

    // MARK: Structure
    static let stroke = ramp(0.10, 0.10)
    static let stroke2 = ramp(0.18, 0.19)
    static let glass = Color(UIColor { $0.userInterfaceStyle == .dark
        ? UIColor(white: 1, alpha: 0.048) : UIColor(white: 1, alpha: 0.72) })
    static let unavailable = Color(light: 0x848EA1, dark: 0x39404E)
}

extension Bucket {
    var markColor: Color {
        switch self {
        case .financial: return EWB.finMark
        case .business: return EWB.bizMark
        case .household: return EWB.hhMark
        }
    }
    var textColor: Color {
        switch self {
        case .financial: return EWB.finText
        case .business: return EWB.bizText
        case .household: return EWB.hhText
        }
    }
}

extension Tier {
    var markColor: Color {
        switch self {
        case .quiet: return EWB.quietMark
        case .watch: return EWB.watchMark
        case .warning: return EWB.warnMark
        case .broad: return EWB.broadMark
        }
    }
    var textColor: Color {
        switch self {
        case .quiet: return EWB.quietText
        case .watch: return EWB.watchText
        case .warning: return EWB.warnText
        case .broad: return EWB.broadText
        }
    }
    var countColor: Color {
        switch self {
        case .quiet: return EWB.quietCount
        case .watch: return EWB.watchCount
        case .warning: return EWB.warnCount
        case .broad: return EWB.broadCount
        }
    }
}

enum Radius {
    static let tile: CGFloat = 14
    static let card: CGFloat = 16
    static let hero: CGFloat = 22
}

enum Metrics {
    static let screenPadding: CGFloat = 20
    static let gapTile: CGFloat = 7
    static let gapGroup: CGFloat = 11
    static let dotSmall: CGFloat = 7
    static let dotLarge: CGFloat = 14
}
