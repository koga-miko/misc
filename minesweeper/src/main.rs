use rand::Rng;
use std::io::{self, Write};

#[derive(Clone, Copy, Debug)]
enum State {
    None,
    Close(usize),
    Bomb,
}

enum Result {
    Invalid,
    Bomb,
    Opened,
}
struct Game {
    row: usize,
    col: usize,
    bombs: usize,
    map: Vec<Vec<(State, bool)>>,
}

impl Game {
    fn new(row: usize, col: usize, bombs: usize) -> Self {
        let mut map = vec![vec![(State::None, false); col]; row];
        let mut rng = rand::thread_rng();
        let mut bombs = bombs;
        if bombs >= row * col {
            bombs = row * col - 1;
        }
        while 0 < bombs {
            let r = rng.gen_range(0..row);
            let c = rng.gen_range(0..col);
            if (matches!(map[r][c].0, State::Bomb)) {
                continue;
            }
            map[r][c].0 = State::Bomb;
            bombs -= 1;
        }
        Game { row, col, bombs, map }
    }
    fn open(&mut self, row: usize, col: usize) -> Result {
        if row >= self.row || col >= self.col {
            return Result::Invalid;
        }
        match self.map[row][col].0 {
            State::Bomb => return Result::Bomb,
            State::Close(_) => return Result::Opened,
            State::None => {
                let mut cnt = 0;
                for r in row.saturating_sub(1)..=(row + 1).min(self.row - 1) {
                    for c in col.saturating_sub(1)..=(col + 1).min(self.col - 1) {
                        if matches!(self.map[r][c].0, State::Bomb) {
                            cnt += 1;
                        }
                    }
                }
                self.map[row][col].0 = State::Close(cnt);
                if cnt == 0 {
                    for r in row.saturating_sub(1)..=(row + 1).min(self.row - 1) {
                        for c in col.saturating_sub(1)..=(col + 1).min(self.col - 1) {
                            if !(r == row && c == col) {
                                self.open(r, c);
                            }
                        }
                    }
                }
            }
        }
        Result::Opened
    }

    fn display(&self) {
        for r in 0..self.row {
            for c in 0..self.col {
                match self.map[r][c].0 {
                    State::None => print!(". "),
                    State::Close(n) => print!("{} ", n),
                    State::Bomb => print!("* "),
                }
            }
            println!();
        }
    }
    
}


fn read_board_size() -> (usize, usize, usize) {
    print!("Row: ");
    io::stdout().flush().unwrap();
    let rows = read_usize();
    
    print!("Col: ");
    io::stdout().flush().unwrap();
    let cols = read_usize();
    
    print!("爆弾数: ");
    io::stdout().flush().unwrap();
    let bomps = read_usize();
    
    (rows, cols, bomps)
}

fn read_usize() -> usize {
    let mut input = String::new();
    io::stdin()
        .read_line(&mut input)
        .expect("入力の読み取りに失敗しました");
    
    input.trim()
        .parse()
        .expect("数値を入力してください")
}

fn main() {
    println!("Mainsweeper start!");
    
    let (rows, cols, bomps) = read_board_size();
    println!("ボードサイズ: {}行 × {}列, 爆弾数: {}個", rows, cols, bomps);

    let mut game = Game::new(rows, cols, bomps);
    game.display();
}