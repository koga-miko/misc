#include "reversi.h"
#include <stdio.h>
#include <string.h>
#include <ctype.h>

// ゲーム初期化
void init_game(Game* game) {
    // ボードを空にする
    for (int i = 0; i < BOARD_SIZE; i++) {
        for (int j = 0; j < BOARD_SIZE; j++) {
            game->board.cells[i][j] = EMPTY;
        }
    }

    // 初期配置
    game->board.cells[3][3] = BLACK;
    game->board.cells[3][4] = WHITE;
    game->board.cells[4][3] = WHITE;
    game->board.cells[4][4] = BLACK;

    game->current_player = PLAYER_BLACK;
    game->black_count = 2;
    game->white_count = 2;
}

// ボード表示
void display_board(const Board* board) {
    printf("\n  ");
    for (int i = 0; i < BOARD_SIZE; i++) {
        printf("%c ", 'a' + i);
    }
    printf("\n");

    for (int i = 0; i < BOARD_SIZE; i++) {
        printf("%d ", i + 1);
        for (int j = 0; j < BOARD_SIZE; j++) {
            switch (board->cells[i][j]) {
                case EMPTY:
                    printf(". ");
                    break;
                case BLACK:
                    printf("B ");
                    break;
                case WHITE:
                    printf("W ");
                    break;
            }
        }
        printf("\n");
    }
    printf("\n");
}

// 8方向のオフセット
static const int directions[8][2] = {
    {-1, -1}, {-1, 0}, {-1, 1},  // 上左、上、上右
    {0, -1},           {0, 1},    // 左、右
    {1, -1},  {1, 0},  {1, 1}     // 下左、下、下右
};

// 指定方向でひっくり返せる石の数をカウント
static int count_flips_in_direction(const Board* board, Position pos, Player player, int dr, int dc) {
    int count = 0;
    int r = pos.row + dr;
    int c = pos.col + dc;
    Player opponent = (player == PLAYER_BLACK) ? PLAYER_WHITE : PLAYER_BLACK;

    // 隣接セルが相手の石でない場合は0
    if (r < 0 || r >= BOARD_SIZE || c < 0 || c >= BOARD_SIZE ||
        board->cells[r][c] != opponent) {
        return 0;
    }

    // 相手の石が続く間カウント
    while (r >= 0 && r < BOARD_SIZE && c >= 0 && c < BOARD_SIZE) {
        if (board->cells[r][c] == opponent) {
            count++;
            r += dr;
            c += dc;
        } else if (board->cells[r][c] == player) {
            return count;  // 自分の石で挟めた
        } else {
            return 0;  // 空きマスがあった
        }
    }

    return 0;  // ボード外に出た
}

// 有効手判定
bool is_valid_move(const Board* board, Position pos, Player player) {
    // 範囲チェック
    if (pos.row < 0 || pos.row >= BOARD_SIZE || pos.col < 0 || pos.col >= BOARD_SIZE) {
        return false;
    }

    // 既に石がある場合は無効
    if (board->cells[pos.row][pos.col] != EMPTY) {
        return false;
    }

    // 8方向のいずれかでひっくり返せるかチェック
    for (int i = 0; i < 8; i++) {
        if (count_flips_in_direction(board, pos, player, directions[i][0], directions[i][1]) > 0) {
            return true;
        }
    }

    return false;
}

// 指定方向の石をひっくり返す（カスタマイズ可能な関数）
static void flip_in_direction(Board* board, Position pos, Player player, int dr, int dc, int count) {
    int r = pos.row + dr;
    int c = pos.col + dc;

    for (int i = 0; i < count; i++) {
        board->cells[r][c] = player;
        r += dr;
        c += dc;
    }
}

// ひっくり返す処理（カスタマイズ可能）
int flip_stones(Board* board, Position pos, Player player) {
    int total_flipped = 0;

    for (int i = 0; i < 8; i++) {
        int count = count_flips_in_direction(board, pos, player, directions[i][0], directions[i][1]);
        if (count > 0) {
            flip_in_direction(board, pos, player, directions[i][0], directions[i][1], count);
            total_flipped += count;
        }
    }

    return total_flipped;
}

// 石を置く
bool place_stone(Board* board, Position pos, Player player) {
    if (!is_valid_move(board, pos, player)) {
        return false;
    }

    // 石を置く
    board->cells[pos.row][pos.col] = player;

    // ひっくり返す
    flip_stones(board, pos, player);

    return true;
}

// 有効な手があるかチェック
bool has_valid_moves(const Board* board, Player player) {
    for (int i = 0; i < BOARD_SIZE; i++) {
        for (int j = 0; j < BOARD_SIZE; j++) {
            Position pos = {i, j};
            if (is_valid_move(board, pos, player)) {
                return true;
            }
        }
    }
    return false;
}

// 石の数をカウント
void count_stones(const Board* board, int* black_count, int* white_count) {
    *black_count = 0;
    *white_count = 0;

    for (int i = 0; i < BOARD_SIZE; i++) {
        for (int j = 0; j < BOARD_SIZE; j++) {
            if (board->cells[i][j] == BLACK) {
                (*black_count)++;
            } else if (board->cells[i][j] == WHITE) {
                (*white_count)++;
            }
        }
    }
}

// 座標文字列をPositionに変換 (例: "a1" -> {0, 0})
bool parse_position(const char* input, Position* pos) {
    if (strlen(input) < 2) {
        return false;
    }

    char col_char = tolower(input[0]);
    char row_char = input[1];

    if (col_char < 'a' || col_char > 'h') {
        return false;
    }

    if (row_char < '1' || row_char > '8') {
        return false;
    }

    pos->col = col_char - 'a';
    pos->row = row_char - '1';

    return true;
}

// ボードをバッファにシリアライズ（送信用）
void serialize_board(const Board* board, int64_t* buffer) {
    int index = 0;
    for (int i = 0; i < BOARD_SIZE; i++) {
        for (int j = 0; j < BOARD_SIZE; j++) {
            buffer[index++] = board->cells[i][j];
        }
    }
}

// バッファからボードをデシリアライズ（受信用）
void deserialize_board(Board* board, const int64_t* buffer) {
    int index = 0;
    for (int i = 0; i < BOARD_SIZE; i++) {
        for (int j = 0; j < BOARD_SIZE; j++) {
            board->cells[i][j] = buffer[index++];
        }
    }
}
