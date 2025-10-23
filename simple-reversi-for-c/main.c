#include "reversi.h"
#include "network.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

#define DEFAULT_PORT 8888

// クライアント側のゲームループ
void run_client(const char* host, int port) {
    Game game;
    init_game(&game);

    int sock = connect_to_server(host, port);
    if (sock < 0) {
        printf("サーバーへの接続に失敗しました。\n");
        return;
    }

    printf("\nクライアントモード（黒石）でゲーム開始\n");
    display_board(&game.board);

    int64_t buffer[64];
    bool game_over = false;

    while (!game_over) {
        // クライアントのターン（黒）
        if (has_valid_moves(&game.board, PLAYER_BLACK)) {
            printf("あなたのターン（黒石）\n");
            printf("有効な手を入力してください（例: d3）。終了するには 'quit' と入力してください。\n");

            bool valid_input = false;
            while (!valid_input) {
                char input[10];
                printf("> ");
                if (scanf("%s", input) != 1) {
                    printf("入力エラー\n");
                    continue;
                }

                if (strcmp(input, "quit") == 0) {
                    printf("ゲームを終了します。\n");
                    close_connection(sock);
                    return;
                }

                Position pos;
                if (!parse_position(input, &pos)) {
                    printf("無効な入力です。a1-h8の形式で入力してください。\n");
                    continue;
                }

                if (!is_valid_move(&game.board, pos, PLAYER_BLACK)) {
                    printf("そこには置けません。別の場所を指定してください。\n");
                    continue;
                }

                place_stone(&game.board, pos, PLAYER_BLACK);
                display_board(&game.board);

                // ボードをサーバーに送信
                serialize_board(&game.board, buffer);
                if (!send_board(sock, buffer)) {
                    printf("送信エラー\n");
                    close_connection(sock);
                    return;
                }

                valid_input = true;
            }
        } else {
            printf("黒石：有効な手がありません。パスします。\n");

            // パスの場合も現在のボード状態を送信
            serialize_board(&game.board, buffer);
            if (!send_board(sock, buffer)) {
                printf("送信エラー\n");
                close_connection(sock);
                return;
            }
        }

        // サーバーのターンを待つ（白）
        if (has_valid_moves(&game.board, PLAYER_WHITE)) {
            printf("相手のターンを待っています...\n");

            if (!receive_board(sock, buffer)) {
                printf("受信エラー\n");
                close_connection(sock);
                return;
            }

            deserialize_board(&game.board, buffer);
            printf("\n相手が石を置きました。\n");
            display_board(&game.board);
        } else {
            printf("白石：有効な手がありません。パスします。\n");
        }

        // ゲーム終了判定
        if (!has_valid_moves(&game.board, PLAYER_BLACK) && !has_valid_moves(&game.board, PLAYER_WHITE)) {
            game_over = true;
        }
    }

    // 結果表示
    int black_count, white_count;
    count_stones(&game.board, &black_count, &white_count);
    printf("\n=== ゲーム終了 ===\n");
    printf("黒石: %d\n", black_count);
    printf("白石: %d\n", white_count);

    if (black_count > white_count) {
        printf("あなたの勝ちです！\n");
    } else if (white_count > black_count) {
        printf("相手の勝ちです。\n");
    } else {
        printf("引き分けです。\n");
    }

    close_connection(sock);
}

// サーバー側のゲームループ
void run_server(int port) {
    Game game;
    init_game(&game);

    int sock = start_server(port);
    if (sock < 0) {
        printf("サーバーの起動に失敗しました。\n");
        return;
    }

    printf("\nサーバーモード（白石）でゲーム開始\n");
    display_board(&game.board);

    int64_t buffer[64];
    bool game_over = false;

    while (!game_over) {
        // クライアントのターンを待つ（黒）
        if (has_valid_moves(&game.board, PLAYER_BLACK)) {
            printf("相手のターンを待っています...\n");

            if (!receive_board(sock, buffer)) {
                printf("受信エラー\n");
                close_connection(sock);
                return;
            }

            deserialize_board(&game.board, buffer);
            printf("\n相手が石を置きました。\n");
            display_board(&game.board);
        } else {
            printf("黒石：有効な手がありません。パスします。\n");
        }

        // サーバーのターン（白）
        if (has_valid_moves(&game.board, PLAYER_WHITE)) {
            printf("あなたのターン（白石）\n");
            printf("有効な手を入力してください（例: d3）。終了するには 'quit' と入力してください。\n");

            bool valid_input = false;
            while (!valid_input) {
                char input[10];
                printf("> ");
                if (scanf("%s", input) != 1) {
                    printf("入力エラー\n");
                    continue;
                }

                if (strcmp(input, "quit") == 0) {
                    printf("ゲームを終了します。\n");
                    close_connection(sock);
                    return;
                }

                Position pos;
                if (!parse_position(input, &pos)) {
                    printf("無効な入力です。a1-h8の形式で入力してください。\n");
                    continue;
                }

                if (!is_valid_move(&game.board, pos, PLAYER_WHITE)) {
                    printf("そこには置けません。別の場所を指定してください。\n");
                    continue;
                }

                place_stone(&game.board, pos, PLAYER_WHITE);
                display_board(&game.board);

                // ボードをクライアントに送信
                serialize_board(&game.board, buffer);
                if (!send_board(sock, buffer)) {
                    printf("送信エラー\n");
                    close_connection(sock);
                    return;
                }

                valid_input = true;
            }
        } else {
            printf("白石：有効な手がありません。パスします。\n");

            // パスの場合も現在のボード状態を送信
            serialize_board(&game.board, buffer);
            if (!send_board(sock, buffer)) {
                printf("送信エラー\n");
                close_connection(sock);
                return;
            }
        }

        // ゲーム終了判定
        if (!has_valid_moves(&game.board, PLAYER_BLACK) && !has_valid_moves(&game.board, PLAYER_WHITE)) {
            game_over = true;
        }
    }

    // 結果表示
    int black_count, white_count;
    count_stones(&game.board, &black_count, &white_count);
    printf("\n=== ゲーム終了 ===\n");
    printf("黒石: %d\n", black_count);
    printf("白石: %d\n", white_count);

    if (white_count > black_count) {
        printf("あなたの勝ちです！\n");
    } else if (black_count > white_count) {
        printf("相手の勝ちです。\n");
    } else {
        printf("引き分けです。\n");
    }

    close_connection(sock);
}

int main(int argc, char* argv[]) {
    printf("=== Simple Reversi ===\n");
    printf("ネットワーク対戦型オセロゲーム\n\n");

    if (argc < 2) {
        printf("使用方法:\n");
        printf("  サーバーとして起動: %s server [port]\n", argv[0]);
        printf("  クライアントとして起動: %s client <host> [port]\n", argv[0]);
        printf("\n例:\n");
        printf("  サーバー: %s server 8888\n", argv[0]);
        printf("  クライアント: %s client 127.0.0.1 8888\n", argv[0]);
        return 1;
    }

    network_init();

    if (strcmp(argv[1], "server") == 0) {
        int port = DEFAULT_PORT;
        if (argc >= 3) {
            port = atoi(argv[2]);
        }
        run_server(port);
    } else if (strcmp(argv[1], "client") == 0) {
        if (argc < 3) {
            printf("クライアントモードにはホスト名が必要です。\n");
            printf("使用方法: %s client <host> [port]\n", argv[0]);
            return 1;
        }

        const char* host = argv[2];
        int port = DEFAULT_PORT;
        if (argc >= 4) {
            port = atoi(argv[3]);
        }
        run_client(host, port);
    } else {
        printf("無効なモード: %s\n", argv[1]);
        printf("'server' または 'client' を指定してください。\n");
        return 1;
    }

    return 0;
}
