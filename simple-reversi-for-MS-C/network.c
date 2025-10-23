#include "network.h"
#include <stdio.h>
#include <string.h>

// ネットワーク初期化（Windows用）
bool network_init(void) {
#ifdef _WIN32
    WSADATA wsa_data;
    int result = WSAStartup(MAKEWORD(2, 2), &wsa_data);
    if (result != 0) {
        printf("WSAStartup failed: %d\n", result);
        return false;
    }
#endif
    return true;
}

// ネットワーク終了処理
void network_cleanup(void) {
#ifdef _WIN32
    WSACleanup();
#endif
}

// サーバーとして起動（接続待ち）
socket_t start_server(int port) {
    socket_t listen_sock, client_sock;
    struct sockaddr_in server_addr, client_addr;
    int addr_len = sizeof(client_addr);

    // ソケット作成
    listen_sock = socket(AF_INET, SOCK_STREAM, 0);
    if (listen_sock == INVALID_SOCKET_VALUE) {
        printf("ソケット作成に失敗しました\n");
        return INVALID_SOCKET_VALUE;
    }

    // アドレス設定
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(port);

    // バインド
    if (bind(listen_sock, (struct sockaddr*)&server_addr, sizeof(server_addr)) == SOCKET_ERROR_VALUE) {
        printf("バインドに失敗しました\n");
        closesocket(listen_sock);
        return INVALID_SOCKET_VALUE;
    }

    // リッスン
    if (listen(listen_sock, 1) == SOCKET_ERROR_VALUE) {
        printf("リッスンに失敗しました\n");
        closesocket(listen_sock);
        return INVALID_SOCKET_VALUE;
    }

    printf("ポート %d で接続を待っています...\n", port);

    // 接続を受け付ける
    client_sock = accept(listen_sock, (struct sockaddr*)&client_addr, &addr_len);
    if (client_sock == INVALID_SOCKET_VALUE) {
        printf("接続受付に失敗しました\n");
        closesocket(listen_sock);
        return INVALID_SOCKET_VALUE;
    }

    printf("クライアントが接続しました\n");

    // リッスンソケットを閉じる
    closesocket(listen_sock);

    return client_sock;
}

// クライアントとして接続
socket_t connect_to_server(const char *host, int port) {
    socket_t sock;
    struct sockaddr_in server_addr;

    // ソケット作成
    sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock == INVALID_SOCKET_VALUE) {
        printf("ソケット作成に失敗しました\n");
        return INVALID_SOCKET_VALUE;
    }

    // サーバーアドレス設定
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(port);

    // IPアドレス変換
    if (inet_pton(AF_INET, host, &server_addr.sin_addr) <= 0) {
        printf("無効なアドレスです\n");
        closesocket(sock);
        return INVALID_SOCKET_VALUE;
    }

    // 接続
    printf("%s:%d に接続しています...\n", host, port);
    if (connect(sock, (struct sockaddr*)&server_addr, sizeof(server_addr)) == SOCKET_ERROR_VALUE) {
        printf("接続に失敗しました\n");
        closesocket(sock);
        return INVALID_SOCKET_VALUE;
    }

    printf("サーバーに接続しました\n");

    return sock;
}

// ボードデータを送信（リトルエンディアン）
bool send_board(socket_t sock, const Board *board) {
    int total_sent = 0;
    int bytes_to_send = BOARD_DATA_SIZE;
    const char *data = (const char*)board->cells;

    while (total_sent < bytes_to_send) {
        int sent = send(sock, data + total_sent, bytes_to_send - total_sent, 0);
        if (sent == SOCKET_ERROR_VALUE) {
            printf("送信エラー\n");
            return false;
        }
        total_sent += sent;
    }

    return true;
}

// ボードデータを受信（リトルエンディアン）
bool receive_board(socket_t sock, Board *board) {
    int total_received = 0;
    int bytes_to_receive = BOARD_DATA_SIZE;
    char *data = (char*)board->cells;

    while (total_received < bytes_to_receive) {
        int received = recv(sock, data + total_received, bytes_to_receive - total_received, 0);
        if (received == SOCKET_ERROR_VALUE) {
            printf("受信エラー\n");
            return false;
        }
        if (received == 0) {
            printf("接続が切断されました\n");
            return false;
        }
        total_received += received;
    }

    return true;
}

// ソケットを閉じる
void close_socket(socket_t sock) {
    if (sock != INVALID_SOCKET_VALUE) {
        closesocket(sock);
    }
}
