#include "reversi.h"
#include <stdio.h>
#include <string.h>
#include <ctype.h>

// 8方向のベクトル
static const Direction directions[8] = {
    {-1, -1}, {-1, 0}, {-1, 1},
    {0, -1},           {0, 1},
    {1, -1},  {1, 0},  {1, 1}
};

// ボードの初期化
void init_board(Board *board) {
    memset(board->cells, 0, sizeof(board->cells));

    // 初期配置（中央の4つの石）
    board->cells[position_from_coordinates(3, 3)] = WHITE;
    board->cells[position_from_coordinates(3, 4)] = BLACK;
    board->cells[position_from_coordinates(4, 3)] = BLACK;
    board->cells[position_from_coordinates(4, 4)] = WHITE;
}

// ボードの表示
void display_board(const Board *board) {
    printf("\n  a b c d e f g h\n");
    for (int row = 0; row < BOARD_SIZE; row++) {
        printf("%d ", row + 1);
        for (int col = 0; col < BOARD_SIZE; col++) {
            int pos = position_from_coordinates(row, col);
            Cell cell = (Cell)board->cells[pos];

            switch (cell) {
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

// 座標からポジションへの変換
int position_from_coordinates(int row, int col) {
    return row * BOARD_SIZE + col;
}

// ポジションから座標への変換
void coordinates_from_position(int position, int *row, int *col) {
    *row = position / BOARD_SIZE;
    *col = position % BOARD_SIZE;
}

// 相手プレイヤーの取得
Player get_opponent(Player player) {
    return (player == PLAYER_BLACK) ? PLAYER_WHITE : PLAYER_BLACK;
}

// 指定した方向に石をひっくり返せるかチェック
static int count_flips_in_direction(const Board *board, int position, Player player, const Direction *dir) {
    int row, col;
    coordinates_from_position(position, &row, &col);

    Player opponent = get_opponent(player);
    int flip_count = 0;
    int r = row + dir->dy;
    int c = col + dir->dx;

    // 隣接するセルが相手の石であることを確認
    while (r >= 0 && r < BOARD_SIZE && c >= 0 && c < BOARD_SIZE) {
        int pos = position_from_coordinates(r, c);
        Cell cell = (Cell)board->cells[pos];

        if (cell == EMPTY) {
            return 0;  // 空きマスがあったら無効
        } else if (cell == opponent) {
            flip_count++;
            r += dir->dy;
            c += dir->dx;
        } else if (cell == player) {
            return flip_count;  // 自分の石で挟めた
        }
    }

    return 0;  // ボード外に出た
}

// 有効な手かどうかチェック
bool is_valid_move(const Board *board, int position, Player player) {
    if (position < 0 || position >= TOTAL_CELLS) {
        return false;
    }

    // すでに石が置かれている
    if (board->cells[position] != EMPTY) {
        return false;
    }

    // 8方向のいずれかで石をひっくり返せるかチェック
    for (int i = 0; i < 8; i++) {
        if (count_flips_in_direction(board, position, player, &directions[i]) > 0) {
            return true;
        }
    }

    return false;
}

// 石をひっくり返す処理
void flip_stones(Board *board, int position, Player player) {
    int row, col;
    coordinates_from_position(position, &row, &col);

    // 8方向について石をひっくり返す
    for (int i = 0; i < 8; i++) {
        int flip_count = count_flips_in_direction(board, position, player, &directions[i]);

        if (flip_count > 0) {
            int r = row + directions[i].dy;
            int c = col + directions[i].dx;

            for (int j = 0; j < flip_count; j++) {
                int pos = position_from_coordinates(r, c);
                board->cells[pos] = player;
                r += directions[i].dy;
                c += directions[i].dx;
            }
        }
    }
}

// 石を置く
bool place_stone(Board *board, int position, Player player) {
    if (!is_valid_move(board, position, player)) {
        return false;
    }

    board->cells[position] = player;
    flip_stones(board, position, player);

    return true;
}

// プレイヤーに有効な手があるかチェック
bool has_valid_moves(const Board *board, Player player) {
    for (int i = 0; i < TOTAL_CELLS; i++) {
        if (is_valid_move(board, i, player)) {
            return true;
        }
    }
    return false;
}

// 石の数をカウント
void count_stones(const Board *board, int *black_count, int *white_count) {
    *black_count = 0;
    *white_count = 0;

    for (int i = 0; i < TOTAL_CELLS; i++) {
        if (board->cells[i] == BLACK) {
            (*black_count)++;
        } else if (board->cells[i] == WHITE) {
            (*white_count)++;
        }
    }
}

// 勝者を判定
Player get_winner(const Board *board) {
    int black_count, white_count;
    count_stones(board, &black_count, &white_count);

    if (black_count > white_count) {
        return PLAYER_BLACK;
    } else if (white_count > black_count) {
        return PLAYER_WHITE;
    } else {
        return EMPTY;  // 引き分け
    }
}

// 入力をパース（例: "a1" -> position）
bool parse_input(const char *input, int *position) {
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

    int col = col_char - 'a';
    int row = row_char - '1';

    *position = position_from_coordinates(row, col);
    return true;
}

// ボードをコピー
void copy_board(const Board *src, Board *dst) {
    memcpy(dst->cells, src->cells, sizeof(src->cells));
}
