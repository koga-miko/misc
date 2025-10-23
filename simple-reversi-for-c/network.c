#include "network.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#define BUFFER_SIZE 512

// ネットワーク初期化（現在は何もしない）
int network_init(void) {
    return 0;
}

// サーバーとして起動
int start_server(int port) {
    int server_fd, client_fd;
    struct sockaddr_in address;
    int addrlen = sizeof(address);
    int opt = 1;

    // ソケット作成
    if ((server_fd = socket(AF_INET, SOCK_STREAM, 0)) == 0) {
        perror("socket failed");
        return -1;
    }

    // ソケットオプション設定（アドレス再利用）
    if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt))) {
        perror("setsockopt");
        close(server_fd);
        return -1;
    }

    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(port);

    // バインド
    if (bind(server_fd, (struct sockaddr *)&address, sizeof(address)) < 0) {
        perror("bind failed");
        close(server_fd);
        return -1;
    }

    // リッスン
    if (listen(server_fd, 1) < 0) {
        perror("listen");
        close(server_fd);
        return -1;
    }

    printf("サーバー起動。ポート %d で接続を待っています...\n", port);

    // 接続を受け入れる
    if ((client_fd = accept(server_fd, (struct sockaddr *)&address, (socklen_t*)&addrlen)) < 0) {
        perror("accept");
        close(server_fd);
        return -1;
    }

    printf("クライアントが接続しました。\n");

    // サーバーソケットをクローズ（クライアントソケットのみ必要）
    close(server_fd);

    return client_fd;
}

// クライアントとして接続
int connect_to_server(const char* host, int port) {
    int sock = 0;
    struct sockaddr_in serv_addr;

    // ソケット作成
    if ((sock = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        printf("ソケット作成エラー\n");
        return -1;
    }

    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(port);

    // アドレス変換
    if (inet_pton(AF_INET, host, &serv_addr.sin_addr) <= 0) {
        printf("無効なアドレス / アドレスがサポートされていません\n");
        close(sock);
        return -1;
    }

    // 接続
    if (connect(sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) {
        printf("接続失敗\n");
        close(sock);
        return -1;
    }

    printf("サーバーに接続しました。\n");

    return sock;
}

// ボードデータを送信
bool send_board(int socket_fd, const int64_t* buffer) {
    ssize_t bytes_sent = send(socket_fd, buffer, BUFFER_SIZE, 0);
    if (bytes_sent < 0) {
        perror("送信エラー");
        return false;
    }
    if (bytes_sent != BUFFER_SIZE) {
        printf("警告: 完全なデータを送信できませんでした (%zd/%d bytes)\n", bytes_sent, BUFFER_SIZE);
        return false;
    }
    return true;
}

// ボードデータを受信
bool receive_board(int socket_fd, int64_t* buffer) {
    ssize_t total_received = 0;
    char* buf_ptr = (char*)buffer;

    // 512バイト全てを受信するまでループ
    while (total_received < BUFFER_SIZE) {
        ssize_t bytes_received = recv(socket_fd, buf_ptr + total_received, BUFFER_SIZE - total_received, 0);
        if (bytes_received < 0) {
            perror("受信エラー");
            return false;
        }
        if (bytes_received == 0) {
            printf("接続が切断されました\n");
            return false;
        }
        total_received += bytes_received;
    }

    return true;
}

// ソケットをクローズ
void close_connection(int socket_fd) {
    close(socket_fd);
}
