#ifndef REVERSI_H
#define REVERSI_H

#include <stdint.h>
#include <stdbool.h>

#define BOARD_SIZE 8
#define TOTAL_CELLS 64

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
    int64_t cells[TOTAL_CELLS];  // 64要素の配列（通信用に8バイト整数を使用）
} Board;

// ゲーム状態
typedef struct {
    Board board;
    Player current_player;
    bool game_over;
} Game;

// 方向ベクトル（8方向）
typedef struct {
    int dx;
    int dy;
} Direction;

// 関数プロトタイプ
void init_board(Board *board);
void display_board(const Board *board);
bool is_valid_move(const Board *board, int position, Player player);
bool place_stone(Board *board, int position, Player player);
void flip_stones(Board *board, int position, Player player);
bool has_valid_moves(const Board *board, Player player);
void count_stones(const Board *board, int *black_count, int *white_count);
Player get_winner(const Board *board);
Player get_opponent(Player player);
int position_from_coordinates(int row, int col);
void coordinates_from_position(int position, int *row, int *col);
bool parse_input(const char *input, int *position);
void copy_board(const Board *src, Board *dst);

#endif // REVERSI_H
