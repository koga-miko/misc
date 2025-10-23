#ifndef REVERSI_H
#define REVERSI_H

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
bool is_valid_move(const Board* board, Position pos, Player player);

// 石を置く（ひっくり返す処理を含む）
bool place_stone(Board* board, Position pos, Player player);

// ひっくり返す処理（カスタマイズ可能）
int flip_stones(Board* board, Position pos, Player player);

// 有効な手があるかチェック
bool has_valid_moves(const Board* board, Player player);

// 石の数をカウント
void count_stones(const Board* board, int* black_count, int* white_count);

// 座標文字列をPositionに変換 (例: "a1" -> {0, 0})
bool parse_position(const char* input, Position* pos);

// ボードをバッファにシリアライズ（送信用）
void serialize_board(const Board* board, int64_t* buffer);

// バッファからボードをデシリアライズ（受信用）
void deserialize_board(Board* board, const int64_t* buffer);

#endif // REVERSI_H
