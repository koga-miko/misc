#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include <stdint.h>
#include <stdbool.h>

#define BOARD_SIZE 8
#define BUFFER_SIZE 512  // 64 cells * 8 bytes per int64_t

// セルの状態
typedef enum {
    EMPTY = 0,
    BLACK = 1,
    WHITE = 2
} Cell;

// プレイヤー
typedef enum {
    PLAYER_BLACK = 1,
    PLAYER_WHITE = 2
} Player;

// ボード構造体
typedef struct {
    int64_t cells[BOARD_SIZE][BOARD_SIZE];
} Board;

// ゲーム状態
typedef struct {
    Board board;
    Player current_player;
    int black_count;
    int white_count;
} Game;

// 座標構造体
typedef struct {
    int row;
    int col;
} Position;

// ゲーム初期化
void init_game(Game* game);

// ボード表示
void display_board(const Board* board);

// 有効手判定
bool is_valid_move(int **cells, int row, int col, int player);

// 石を置く（ひっくり返す処理を含む）
bool place_stone(int **cells, int row, int col, int player);

// ひっくり返す処理（カスタマイズ可能）
int flip_stones(int **cells, int row, int col, int player);

// 有効な手があるかチェック
bool has_valid_moves(int **cells, int player);

// 石の数をカウント
void count_stones(const Board* board, int* black_count, int* white_count);

// 座標文字列をPositionに変換 (例: "a1" -> {0, 0})
bool parse_position(const char* input, Position* pos);

// ボードをバッファにシリアライズ（送信用）
void serialize_board(const Board* board, int64_t* buffer);

// バッファからボードをデシリアライズ（受信用）
void deserialize_board(Board* board, const int64_t* buffer);

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

bool is_valid_move(int **cells, int row, int col, int player) {
    if (cells[row][col] != 0) {
        return false;
    }
    int enemy = (player == 1)? 2: 1;
    for (int d = 0; d < 8; d++) {
        int dr = directions[d][0];
        int dc = directions[d][1];
        int r = row + dr;
        int c = col + dc;
        int enemy_count = 0;
        while (r >= 0 && r < 8 && c >= 0 && c < 8) {
            if (cells[r][c] == enemy) {
                enemy_count++;
            } else if (cells[r][c] == player) {
                if (enemy_count > 0) {
                    return true;
                } else {
                    break;
                }
            } else {
                break;
            }
            r += dr;
            c += dc;
        }
    }
    return false;
}

int check_flip(int **cells, int row, int col, int player, int direction, int enemy_count) {
    int enemy = (player == 1)? 2: 1;
    int dr = directions[direction][0];
    int dc = directions[direction][1];
    int r = row + dr;
    int c = col + dc;
    if (r >= 0 && r < 8 && c >= 0 && c < 8) {
        if (cells[r][c] == enemy) {
            enemy_count++;
            if (check_flip(cells, r + dr, c + dc, player, direction)) {
                cells[r][c] = player;
                return true;
            }
        } else if (cells[r][c] == player) {
            if (enemy_count > 0) {
                return true;
            } else {
                break;
            }
        } else {
            break;
        }
        r += dr;
        c += dc;
    }
}
// ひっくり返す処理（カスタマイズ可能）
int flip_stones(int **cells, int row, int col, int player) {
    int enemy = (player == 1)? 2: 1;
    for (int d = 0; d < 8; d++) {
        int dr = directions[d][0];
        int dc = directions[d][1];
        int r = row + dr;
        int c = col + dc;
        int enemy_count = 0;
        while (r >= 0 && r < 8 && c >= 0 && c < 8) {
            if (cells[r][c] == enemy) {
                enemy_count++;
            } else if (cells[r][c] == player) {
                if (enemy_count > 0) {
                    return true;
                } else {
                    break;
                }
            } else {
                break;
            }
            r += dr;
            c += dc;
        }
    }
    return false;
}

// 石を置く
bool place_stone(int **cells, int row, int col, int player) {
    if (!is_valid_move(cells, row, col, player)) {
        return false;
    }
    cells[row][col] = player;
    flip_stones(cells, row, col, player);
    return true;
}

// 有効な手があるかチェック
bool has_valid_moves(int **cells, int player) {
    for (int row = 0; row < 8; row++) {
        for (int col = 0; col < 8; col++) {
            if (is_valid_move(cells, row, col, player)) {
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
