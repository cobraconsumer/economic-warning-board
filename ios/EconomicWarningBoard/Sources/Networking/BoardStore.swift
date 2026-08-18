import Foundation

@MainActor
final class BoardStore: ObservableObject {
    @Published private(set) var board: Board?
    @Published private(set) var lastError: String?
    @Published private(set) var isLoading = false

    private let service = BoardService()
    private let cacheURL: URL

    init() {
        let caches = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask)[0]
        cacheURL = caches.appendingPathComponent("board.json")
        loadCached()
    }

    private func loadCached() {
        guard let data = try? Data(contentsOf: cacheURL) else { return }
        board = try? BoardService.decoder.decode(Board.self, from: data)
    }

    private func cache(_ data: Data) {
        try? data.write(to: cacheURL, options: .atomic)
    }

    func refresh() async {
        isLoading = true
        defer { isLoading = false }
        let previousTier = board?.board.tier
        do {
            let (newBoard, data) = try await service.fetchBoard()
            cache(data)
            board = newBoard
            lastError = nil
            if let previousTier, previousTier != newBoard.board.tier {
                NotificationScheduler.shared.notifyTierChange(
                    from: previousTier, to: newBoard.board, history: newBoard.history)
            }
        } catch {
            if board == nil {
                lastError = "Couldn't load the board. Check your connection and try again."
            } else {
                lastError = "Couldn't refresh — showing the last successful update."
            }
        }
    }
}
