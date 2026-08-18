import BackgroundTasks
import SwiftUI

@main
struct EconomicWarningBoardApp: App {
    @StateObject private var store = BoardStore()
    @Environment(\.scenePhase) private var scenePhase

    static let refreshTaskID = "com.cobraconsumer.economicwarningboard.refresh"

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(store)
                .task {
                    await store.refresh()
                    NotificationScheduler.shared.requestAuthorizationIfNeeded()
                }
        }
        .onChange(of: scenePhase) { _, phase in
            if phase == .background {
                scheduleBackgroundRefresh()
            }
        }
        .backgroundTask(.appRefresh(Self.refreshTaskID)) {
            await store.refresh()
            scheduleBackgroundRefresh()
        }
    }

    private func scheduleBackgroundRefresh() {
        let request = BGAppRefreshTaskRequest(identifier: Self.refreshTaskID)
        request.earliestBeginDate = .now.addingTimeInterval(6 * 60 * 60)
        try? BGTaskScheduler.shared.submit(request)
    }
}
