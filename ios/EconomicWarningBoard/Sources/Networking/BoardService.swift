import Foundation

enum BoardServiceError: Error {
    case invalidResponse
}

struct BoardService {
    static let boardURL = URL(string: "https://cobraconsumer.github.io/economic-warning-board/board.json")!

    static let decoder: JSONDecoder = {
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        decoder.dateDecodingStrategy = .iso8601
        return decoder
    }()

    func fetchBoard() async throws -> (board: Board, data: Data) {
        var request = URLRequest(url: Self.boardURL)
        request.cachePolicy = .reloadIgnoringLocalCacheData
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse, (200..<300).contains(http.statusCode) else {
            throw BoardServiceError.invalidResponse
        }
        let board = try Self.decoder.decode(Board.self, from: data)
        return (board, data)
    }
}
