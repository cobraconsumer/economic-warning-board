import XCTest
import SwiftUI
@testable import EconomicWarningBoard

/// Swift port of economic-warning-board-handoff/contrast-check.py, run
/// against the actual EWB enum rather than parsed-out-of-HTML tokens, so a
/// color nudged to "look better" fails CI instead of just failing a script
/// someone forgot to re-run. Spec section 10 (definition of done).
final class ContrastTests: XCTestCase {
    private func rgb(_ color: Color, style: UIUserInterfaceStyle) -> (Double, Double, Double) {
        let trait = UITraitCollection(userInterfaceStyle: style)
        let resolved = UIColor(color).resolvedColor(with: trait)
        var r: CGFloat = 0, g: CGFloat = 0, b: CGFloat = 0, a: CGFloat = 0
        resolved.getRed(&r, green: &g, blue: &b, alpha: &a)
        return (Double(r) * 255, Double(g) * 255, Double(b) * 255)
    }

    private func srgb(_ c: Double) -> Double {
        let v = c / 255
        return v <= 0.04045 ? v / 12.92 : pow((v + 0.055) / 1.055, 2.4)
    }

    private func luminance(_ p: (Double, Double, Double)) -> Double {
        0.2126 * srgb(p.0) + 0.7152 * srgb(p.1) + 0.0722 * srgb(p.2)
    }

    private func ratio(_ a: (Double, Double, Double), _ b: (Double, Double, Double)) -> Double {
        let la = luminance(a), lb = luminance(b)
        let hi = max(la, lb), lo = min(la, lb)
        return (hi + 0.05) / (lo + 0.05)
    }

    private func assertContrast(
        _ label: String, _ fg: Color, _ bg: Color, need: Double,
        style: UIUserInterfaceStyle, file: StaticString = #filePath, line: UInt = #line
    ) {
        let r = ratio(rgb(fg, style: style), rgb(bg, style: style))
        XCTAssertGreaterThanOrEqual(
            r, need,
            String(format: "%@ (%@) contrast %.2f < required %.2f",
                    label, style == .dark ? "dark" : "light", r, need),
            file: file, line: line
        )
    }

    private func assertBothThemes(_ label: String, _ fg: Color, need: Double) {
        assertContrast(label, fg, EWB.bg, need: need, style: .light)
        assertContrast(label, fg, EWB.bg, need: need, style: .dark)
    }

    func testTextRamp() {
        assertBothThemes("ink", EWB.ink, need: 4.5)
        assertBothThemes("ink2", EWB.ink2, need: 4.5)
        assertBothThemes("ink3", EWB.ink3, need: 4.5)
        assertBothThemes("ink4", EWB.ink4, need: 3.0)
    }

    func testCategoryMarkTokens() {
        assertBothThemes("finMark", EWB.finMark, need: 3.0)
        assertBothThemes("bizMark", EWB.bizMark, need: 3.0)
        assertBothThemes("hhMark", EWB.hhMark, need: 3.0)
    }

    func testCategoryTextTokens() {
        assertBothThemes("finText", EWB.finText, need: 4.5)
        assertBothThemes("bizText", EWB.bizText, need: 4.5)
        assertBothThemes("hhText", EWB.hhText, need: 4.5)
    }

    func testTierMarkTokens() {
        assertBothThemes("quietMark", EWB.quietMark, need: 3.0)
        assertBothThemes("watchMark", EWB.watchMark, need: 3.0)
        assertBothThemes("warnMark", EWB.warnMark, need: 3.0)
        assertBothThemes("broadMark", EWB.broadMark, need: 3.0)
    }

    func testTierTextTokens() {
        assertBothThemes("quietText", EWB.quietText, need: 4.5)
        assertBothThemes("watchText", EWB.watchText, need: 4.5)
        assertBothThemes("warnText", EWB.warnText, need: 4.5)
        assertBothThemes("broadText", EWB.broadText, need: 4.5)
    }

    /// The hero count uses a deliberately muted palette instead of the vivid
    /// tier tokens above -- still needs to clear text contrast on its own.
    func testTierCountTokens() {
        assertBothThemes("quietCount", EWB.quietCount, need: 4.5)
        assertBothThemes("watchCount", EWB.watchCount, need: 4.5)
        assertBothThemes("warnCount", EWB.warnCount, need: 4.5)
        assertBothThemes("broadCount", EWB.broadCount, need: 4.5)
    }
}
