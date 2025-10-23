#include "reversi.h"
#include "network.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// モードの定義
typedef enum {
    MODE_SERVER,
    MODE_CLIENT
} GameMode;

// ゲーム情報
typedef struct {
    Game game;
    socket_t sock;
    GameMode mode;
    Player my_player;
} GameContext;

// ゲームの初期化
void init_game(GameContext *ctx) {
    init_board(&ctx->game.board);
    ctx->game.current_player = PLAYER_BLACK;  // 黒（クライアント）が先手
    ctx->game.game_over = false;
}

// プレイヤーの表示
const char* player_name(Player player) {
    return (player == PLAYER_BLACK) ? "黒(B)" : "白(W)";
}

// 自分のターン処理
bool handle_my_turn(GameContext *ctx) {
    printf("\n=== あなたのターン (%s) ===\n", player_name(ctx->my_player));

    // 有効な手があるかチェック
    if (!has_valid_moves(&ctx->game.board, ctx->my_player)) {
        printf("有効な手がありません。パスします。\n");
        return false;
    }

    // 有効な手を表示
    printf("有効な手: ");
    for (int i = 0; i < TOTAL_CELLS; i++) {
        if (is_valid_move(&ctx->game.board, i, ctx->my_player)) {
            int row, col;
            coordinates_from_position(i, &row, &col);
            printf("%c%d ", 'a' + col, row + 1);
        }
    }
    printf("\n");

    // 入力を受け付ける
    while (true) {
        printf("石を置く位置を入力してください (例: a1): ");
        char input[10];
        if (fgets(input, sizeof(input), stdin) == NULL) {
            continue;
        }

        // 改行を削除
        input[strcspn(input, "\n")] = 0;

        int position;
        if (!parse_input(input, &position)) {
            printf("無効な入力です。\n");
            continue;
        }

        if (!is_valid_move(&ctx->game.board, position, ctx->my_player)) {
            printf("そこには置けません。\n");
            continue;
        }

        // 石を置く
        place_stone(&ctx->game.board, position, ctx->my_player);
        printf("石を置きました: %s\n", input);

        // ボードを送信
        if (!send_board(ctx->sock, &ctx->game.board)) {
            printf("送信に失敗しました。\n");
            return false;
        }

        return true;
    }
}

// 相手のターン処理
bool handle_opponent_turn(GameContext *ctx) {
    Player opponent = get_opponent(ctx->my_player);
    printf("\n=== 相手のターン (%s) ===\n", player_name(opponent));
    printf("相手の手を待っています...\n");

    // 相手が有効な手を持っているかチェック
    if (!has_valid_moves(&ctx->game.board, opponent)) {
        printf("相手に有効な手がありません。パスされました。\n");
        return false;
    }

    // ボードを受信
    if (!receive_board(ctx->sock, &ctx->game.board)) {
        printf("受信に失敗しました。\n");
        return false;
    }

    printf("相手が石を置きました。\n");
    return true;
}

// ゲーム終了判定と結果表示
void check_game_end(GameContext *ctx) {
    bool my_has_moves = has_valid_moves(&ctx->game.board, ctx->my_player);
    bool opponent_has_moves = has_valid_moves(&ctx->game.board, get_opponent(ctx->my_player));

    if (!my_has_moves && !opponent_has_moves) {
        ctx->game.game_over = true;

        printf("\n=== ゲーム終了 ===\n");

        int black_count, white_count;
        count_stones(&ctx->game.board, &black_count, &white_count);

        printf("黒(B): %d\n", black_count);
        printf("白(W): %d\n", white_count);

        Player winner = get_winner(&ctx->game.board);
        if (winner == EMPTY) {
            printf("引き分けです！\n");
        } else if (winner == ctx->my_player) {
            printf("あなたの勝ちです！\n");
        } else {
            printf("あなたの負けです。\n");
        }
    }
}

// ゲームループ
void game_loop(GameContext *ctx) {
    init_game(ctx);

    while (!ctx->game.game_over) {
        display_board(&ctx->game.board);

        int black_count, white_count;
        count_stones(&ctx->game.board, &black_count, &white_count);
        printf("黒(B): %d  白(W): %d\n", black_count, white_count);

        // 自分のターンか相手のターンか
        if (ctx->game.current_player == ctx->my_player) {
            if (handle_my_turn(ctx)) {
                ctx->game.current_player = get_opponent(ctx->my_player);
            } else {
                // パスの場合も相手にターンを渡す
                ctx->game.current_player = get_opponent(ctx->my_player);
            }
        } else {
            if (handle_opponent_turn(ctx)) {
                ctx->game.current_player = ctx->my_player;
            } else {
                // 相手がパスした場合
                ctx->game.current_player = ctx->my_player;
            }
        }

        // ゲーム終了判定
        check_game_end(ctx);
    }

    display_board(&ctx->game.board);
}

// サーバーモード
void run_server(int port) {
    GameContext ctx;
    ctx.mode = MODE_SERVER;
    ctx.my_player = PLAYER_WHITE;  // サーバーは白

    printf("=== サーバーモード（白） ===\n");

    ctx.sock = start_server(port);
    if (ctx.sock == INVALID_SOCKET_VALUE) {
        printf("サーバーの起動に失敗しました。\n");
        return;
    }

    game_loop(&ctx);

    close_socket(ctx.sock);
}

// クライアントモード
void run_client(const char *host, int port) {
    GameContext ctx;
    ctx.mode = MODE_CLIENT;
    ctx.my_player = PLAYER_BLACK;  // クライアントは黒

    printf("=== クライアントモード（黒） ===\n");

    ctx.sock = connect_to_server(host, port);
    if (ctx.sock == INVALID_SOCKET_VALUE) {
        printf("サーバーへの接続に失敗しました。\n");
        return;
    }

    game_loop(&ctx);

    close_socket(ctx.sock);
}

// メイン関数
int main(int argc, char *argv[]) {
    printf("=================================\n");
    printf("  Simple Reversi (Network Game)  \n");
    printf("=================================\n\n");

    // ネットワーク初期化
    if (!network_init()) {
        printf("ネットワークの初期化に失敗しました。\n");
        return 1;
    }

    // モード選択
    printf("モードを選択してください:\n");
    printf("1. サーバー（白・後手）\n");
    printf("2. クライアント（黒・先手）\n");
    printf("選択 (1 or 2): ");

    char mode_input[10];
    if (fgets(mode_input, sizeof(mode_input), stdin) == NULL) {
        network_cleanup();
        return 1;
    }

    int mode = atoi(mode_input);

    if (mode == 1) {
        // サーバーモード
        printf("ポート番号を入力してください（デフォルト: %d）: ", DEFAULT_PORT);
        char port_input[10];
        if (fgets(port_input, sizeof(port_input), stdin) == NULL) {
            network_cleanup();
            return 1;
        }

        int port = atoi(port_input);
        if (port == 0) {
            port = DEFAULT_PORT;
        }

        run_server(port);

    } else if (mode == 2) {
        // クライアントモード
        printf("サーバーのIPアドレスを入力してください: ");
        char host[50];
        if (fgets(host, sizeof(host), stdin) == NULL) {
            network_cleanup();
            return 1;
        }
        host[strcspn(host, "\n")] = 0;

        printf("ポート番号を入力してください（デフォルト: %d）: ", DEFAULT_PORT);
        char port_input[10];
        if (fgets(port_input, sizeof(port_input), stdin) == NULL) {
            network_cleanup();
            return 1;
        }

        int port = atoi(port_input);
        if (port == 0) {
            port = DEFAULT_PORT;
        }

        run_client(host, port);

    } else {
        printf("無効なモードです。\n");
    }

    network_cleanup();
    return 0;
}
