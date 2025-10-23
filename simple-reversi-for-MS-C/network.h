#ifndef NETWORK_H
#define NETWORK_H

#include "reversi.h"
#include <stdbool.h>

#ifdef _WIN32
    #include <winsock2.h>
    #include <ws2tcpip.h>
    #pragma comment(lib, "ws2_32.lib")
    typedef SOCKET socket_t;
    #define INVALID_SOCKET_VALUE INVALID_SOCKET
    #define SOCKET_ERROR_VALUE SOCKET_ERROR
#else
    #include <sys/socket.h>
    #include <netinet/in.h>
    #include <arpa/inet.h>
    #include <unistd.h>
    typedef int socket_t;
    #define INVALID_SOCKET_VALUE -1
    #define SOCKET_ERROR_VALUE -1
    #define closesocket close
#endif

#define DEFAULT_PORT 8888
#define BOARD_DATA_SIZE (TOTAL_CELLS * sizeof(int64_t))  // 512バイト

// ネットワーク初期化
bool network_init(void);

// ネットワーク終了処理
void network_cleanup(void);

// サーバーとして起動（接続待ち）
socket_t start_server(int port);

// クライアントとして接続
socket_t connect_to_server(const char *host, int port);

// ボードデータを送信
bool send_board(socket_t sock, const Board *board);

// ボードデータを受信
bool receive_board(socket_t sock, Board *board);

// ソケットを閉じる
void close_socket(socket_t sock);

#endif // NETWORK_H
