use std::fmt;
use std::io::{self, BufReader, Write};
use std::net::{TcpListener, TcpStream};

// セルの状態
#[derive(Clone, Copy, PartialEq, Debug)]
#[repr(i64)]
enum Cell {
    Empty = 0,
    Black = 1,
    White = 2,
}

impl Cell {
    fn from_i64(value: i64) -> Option<Self> {
        match value {
            0 => Some(Cell::Empty),
            1 => Some(Cell::Black),
            2 => Some(Cell::White),
            _ => None,
        }
    }
}

impl fmt::Display for Cell {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        let c = match self {
            Cell::Empty => '.',
            Cell::Black => 'B',
            Cell::White => 'W',
        };
        write!(f, "{}", c)
    }
}

// プレイヤー
#[derive(Clone, Copy, PartialEq, Debug)]
enum Player {
    Black,
    White,
}

impl Player {
    fn to_cell(&self) -> Cell {
        match self {
            Player::Black => Cell::Black,
            Player::White => Cell::White,
        }
    }

    fn opponent(&self) -> Player {
        match self {
            Player::Black => Player::White,
            Player::White => Player::Black,
        }
    }
}

impl fmt::Display for Player {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        let s = match self {
            Player::Black => "黒(B)",
            Player::White => "白(W)",
        };
        write!(f, "{}", s)
    }
}

// ボード
struct Board {
    cells: [[Cell; 8]; 8],
}

impl Board {
    fn new() -> Self {
        let mut board = Board {
            cells: [[Cell::Empty; 8]; 8],
        };
        // 初期配置
        board.cells[3][3] = Cell::Black;
        board.cells[3][4] = Cell::White;
        board.cells[4][3] = Cell::White;
        board.cells[4][4] = Cell::Black;
        board
    }

    fn display(&self) {
        println!("  a b c d e f g h");
        for (i, row) in self.cells.iter().enumerate() {
            print!("{} ", i + 1);
            for cell in row {
                print!("{} ", cell);
            }
            println!();
        }
    }

    // ボードを64要素の配列に変換（ネットワーク送信用）
    fn to_array(&self) -> [i64; 64] {
        let mut arr = [0i64; 64];
        for (i, row) in self.cells.iter().enumerate() {
            for (j, &cell) in row.iter().enumerate() {
                arr[i * 8 + j] = cell as i64;
            }
        }
        arr
    }

    // 64要素の配列からボードを復元
    fn from_array(arr: &[i64; 64]) -> Option<Self> {
        let mut board = Board {
            cells: [[Cell::Empty; 8]; 8],
        };
        for i in 0..8 {
            for j in 0..8 {
                board.cells[i][j] = Cell::from_i64(arr[i * 8 + j])?;
            }
        }
        Some(board)
    }

    fn get(&self, row: usize, col: usize) -> Cell {
        self.cells[row][col]
    }

    fn set(&mut self, row: usize, col: usize, cell: Cell) {
        self.cells[row][col] = cell;
    }

    fn count(&self, cell: Cell) -> usize {
        self.cells
            .iter()
            .flat_map(|row| row.iter())
            .filter(|&&c| c == cell)
            .count()
    }
}

// ゲーム状態
struct Game {
    board: Board,
    current_player: Player,
}

impl Game {
    fn new() -> Self {
        Game {
            board: Board::new(),
            current_player: Player::Black,
        }
    }

    // 指定位置に石を置けるかチェック（カスタマイズ可能な関数）
    fn can_place(&self, row: usize, col: usize, player: Player) -> bool {
        if self.board.get(row, col) != Cell::Empty {
            return false;
        }

        // 8方向をチェック
        let directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1),
        ];

        for &(dr, dc) in &directions {
            if self.can_flip_direction(row, col, dr, dc, player) {
                return true;
            }
        }
        false
    }

    // 特定方向に石をひっくり返せるかチェック
    fn can_flip_direction(&self, row: usize, col: usize, dr: i32, dc: i32, player: Player) -> bool {
        let opponent = player.opponent().to_cell();
        let mut r = row as i32 + dr;
        let mut c = col as i32 + dc;
        let mut found_opponent = false;

        while r >= 0 && r < 8 && c >= 0 && c < 8 {
            let cell = self.board.get(r as usize, c as usize);
            if cell == opponent {
                found_opponent = true;
            } else if cell == player.to_cell() && found_opponent {
                return true;
            } else {
                break;
            }
            r += dr;
            c += dc;
        }
        false
    }

    // 石を置いて、ひっくり返す（カスタマイズ可能な関数）
    fn place_stone(&mut self, row: usize, col: usize, player: Player) -> bool {
        if !self.can_place(row, col, player) {
            return false;
        }

        self.board.set(row, col, player.to_cell());

        // 8方向にひっくり返す
        let directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1),
        ];

        for &(dr, dc) in &directions {
            self.flip_direction(row, col, dr, dc, player);
        }

        true
    }

    // 特定方向の石をひっくり返す
    fn flip_direction(&mut self, row: usize, col: usize, dr: i32, dc: i32, player: Player) {
        if !self.can_flip_direction(row, col, dr, dc, player) {
            return;
        }

        let opponent = player.opponent().to_cell();
        let mut r = row as i32 + dr;
        let mut c = col as i32 + dc;

        while r >= 0 && r < 8 && c >= 0 && c < 8 {
            let cell = self.board.get(r as usize, c as usize);
            if cell == opponent {
                self.board.set(r as usize, c as usize, player.to_cell());
            } else {
                break;
            }
            r += dr;
            c += dc;
        }
    }

    // プレイヤーが置ける場所があるかチェック
    fn has_valid_moves(&self, player: Player) -> bool {
        for row in 0..8 {
            for col in 0..8 {
                if self.can_place(row, col, player) {
                    return true;
                }
            }
        }
        false
    }

    // ゲーム終了判定
    fn is_game_over(&self) -> bool {
        !self.has_valid_moves(Player::Black) && !self.has_valid_moves(Player::White)
    }

    // 勝者判定
    fn get_winner(&self) -> Option<Player> {
        let black_count = self.board.count(Cell::Black);
        let white_count = self.board.count(Cell::White);

        if black_count > white_count {
            Some(Player::Black)
        } else if white_count > black_count {
            Some(Player::White)
        } else {
            None
        }
    }

    fn switch_player(&mut self) {
        self.current_player = self.current_player.opponent();
    }
}

// 座標入力のパース（例: "a1" -> (0, 0)）
fn parse_position(input: &str) -> Option<(usize, usize)> {
    let input = input.trim().to_lowercase();
    if input.len() != 2 {
        return None;
    }

    let mut chars = input.chars();
    let col_char = chars.next()?;
    let row_char = chars.next()?;

    let col = (col_char as u8).checked_sub(b'a')? as usize;
    let row = (row_char as u8).checked_sub(b'1')? as usize;

    if row < 8 && col < 8 {
        Some((row, col))
    } else {
        None
    }
}

fn main() {
    println!("Simple Reversi");
    println!("クライアント(C)かサーバー(S)を選択してください:");

    let mut input = String::new();
    io::stdin().read_line(&mut input).unwrap();
    let choice = input.trim().to_uppercase();

    match choice.as_str() {
        "C" => run_client(),
        "S" => run_server(),
        _ => println!("無効な選択です"),
    }
}

fn run_client() {
    println!("サーバーのアドレスを入力してください (例: 127.0.0.1:8080):");
    let mut addr = String::new();
    io::stdin().read_line(&mut addr).unwrap();
    let addr = addr.trim();

    match TcpStream::connect(addr) {
        Ok(stream) => {
            println!("サーバーに接続しました");
            play_game(stream, Player::Black);
        }
        Err(e) => {
            println!("接続エラー: {}", e);
        }
    }
}

fn run_server() {
    println!("ポート番号を入力してください (例: 8080):");
    let mut port = String::new();
    io::stdin().read_line(&mut port).unwrap();
    let port = port.trim();

    let addr = format!("0.0.0.0:{}", port);
    let listener = TcpListener::bind(&addr).unwrap();
    println!("{}で待機中...", addr);

    match listener.accept() {
        Ok((stream, addr)) => {
            println!("{}から接続されました", addr);
            play_game(stream, Player::White);
        }
        Err(e) => {
            println!("接続エラー: {}", e);
        }
    }
}

fn play_game(mut stream: TcpStream, my_player: Player) {
    let mut game = Game::new();
    let opponent = my_player.opponent();

    loop {
        game.board.display();

        if game.is_game_over() {
            println!("\nゲーム終了!");
            let black_count = game.board.count(Cell::Black);
            let white_count = game.board.count(Cell::White);
            println!("黒: {} 白: {}", black_count, white_count);

            match game.get_winner() {
                Some(winner) => println!("{}の勝ちです!", winner),
                None => println!("引き分けです!"),
            }
            break;
        }

        if game.current_player == my_player {
            // 自分のターン
            if !game.has_valid_moves(my_player) {
                println!("{}は置ける場所がありません。パスします。", my_player);
                game.switch_player();

                // パス情報を送信（現在のボード状態をそのまま送る）
                send_board(&mut stream, &game.board);
                continue;
            }

            println!("\n{}のターンです", my_player);

            loop {
                print!("位置を入力してください (例: d3): ");
                io::stdout().flush().unwrap();

                let mut input = String::new();
                io::stdin().read_line(&mut input).unwrap();

                if let Some((row, col)) = parse_position(&input) {
                    if game.place_stone(row, col, my_player) {
                        game.switch_player();

                        // ボード状態を送信
                        send_board(&mut stream, &game.board);
                        break;
                    } else {
                        println!("そこには置けません");
                    }
                } else {
                    println!("無効な入力です");
                }
            }
        } else {
            // 相手のターン
            if !game.has_valid_moves(opponent) {
                println!("{}は置ける場所がありません。パスします。", opponent);
                game.switch_player();
                continue;
            }

            println!("\n{}のターンです。待機中...", opponent);

            // ボード状態を受信
            if let Some(board) = receive_board(&mut stream) {
                game.board = board;
                game.switch_player();
            } else {
                println!("通信エラー");
                break;
            }
        }
    }
}

// ボード状態を送信（512バイト: 64個のi64）
fn send_board(stream: &mut TcpStream, board: &Board) {
    let arr = board.to_array();
    let mut buffer = [0u8; 512];

    // i64配列をバイト列に変換（リトルエンディアン）
    for i in 0..64 {
        let bytes = arr[i].to_le_bytes();
        buffer[i * 8..(i + 1) * 8].copy_from_slice(&bytes);
    }

    stream.write_all(&buffer).unwrap();
}

// ボード状態を受信
fn receive_board(stream: &mut TcpStream) -> Option<Board> {
    let mut buffer = [0u8; 512];
    let mut reader = BufReader::new(stream);

    reader.get_ref().set_nonblocking(false).ok()?;
    io::Read::read_exact(&mut reader, &mut buffer).ok()?;

    // バイト列をi64配列に変換
    let mut arr = [0i64; 64];
    for i in 0..64 {
        let bytes: [u8; 8] = buffer[i * 8..(i + 1) * 8].try_into().ok()?;
        arr[i] = i64::from_le_bytes(bytes);
    }

    Board::from_array(&arr)
}
