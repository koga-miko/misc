#ifndef NETWORK_H
#define NETWORK_H

#include <stdint.h>
#include <stdbool.h>

// ネットワーク初期化
int network_init(void);

// サーバーとして起動（ポートでリッスン）
int start_server(int port);

// クライアントとして接続
int connect_to_server(const char* host, int port);

// ボードデータを送信
bool send_board(int socket_fd, const int64_t* buffer);

// ボードデータを受信
bool receive_board(int socket_fd, int64_t* buffer);

// ソケットをクローズ
void close_connection(int socket_fd);

#endif // NETWORK_H
