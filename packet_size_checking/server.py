import socket
import threading
import time
from datetime import datetime

HOST = '127.0.0.1'
PORT = 12345

class ServerStats:
    def __init__(self):
        self.total_received = 0
        self.total_sent = 0
        self.message_count = 0
        self.lock = threading.Lock()

    def add_stats(self, received, sent):
        with self.lock:
            self.total_received += received
            self.total_sent += sent
            self.message_count += 1

    def get_stats(self):
        with self.lock:
            return self.total_received, self.total_sent, self.message_count

def handle_client(conn, addr, stats):
    """クライアント接続を処理"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] クライアント接続: {addr}")

    try:
        while True:
            # メッセージの長さを受信 (4バイト)
            length_data = conn.recv(4)
            if not length_data:
                break

            msg_length = int.from_bytes(length_data, 'big')

            # メッセージ本体を受信
            data = b''
            while len(data) < msg_length:
                chunk = conn.recv(min(msg_length - len(data), 4096))
                if not chunk:
                    break
                data += chunk

            if not data:
                break

            received_size = len(length_data) + len(data)

            # 受信したデータをそのまま送り返す（エコー）
            conn.sendall(length_data + data)
            sent_size = received_size

            # 統計情報を更新
            stats.add_stats(received_size, sent_size)

            print(f"[{datetime.now().strftime('%H:%M:%S')}] {addr} - 受信: {received_size}バイト, 送信: {sent_size}バイト")

    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] エラー ({addr}): {e}")
    finally:
        conn.close()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] クライアント切断: {addr}")

def stats_monitor(stats):
    """定期的に統計情報を表示"""
    start_time = time.time()

    while True:
        time.sleep(10)
        received, sent, count = stats.get_stats()
        elapsed = time.time() - start_time

        print(f"\n=== 統計情報 (稼働時間: {elapsed:.1f}秒) ===")
        print(f"メッセージ数: {count}")
        print(f"総受信量: {received:,} バイト ({received/1024:.2f} KB)")
        print(f"総送信量: {sent:,} バイト ({sent/1024:.2f} KB)")
        print(f"平均レート: 受信 {received/elapsed:.1f} バイト/秒, 送信 {sent/elapsed:.1f} バイト/秒")
        print("=" * 50 + "\n")

def main():
    stats = ServerStats()

    # 統計情報モニタースレッドを起動
    monitor_thread = threading.Thread(target=stats_monitor, args=(stats,), daemon=True)
    monitor_thread.start()

    # サーバーソケットを作成
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)

        print(f"サーバー起動: {HOST}:{PORT}")
        print("クライアントからの接続を待機中...\n")

        try:
            while True:
                conn, addr = server_socket.accept()
                # 各クライアント接続を別スレッドで処理
                client_thread = threading.Thread(
                    target=handle_client,
                    args=(conn, addr, stats),
                    daemon=True
                )
                client_thread.start()
        except KeyboardInterrupt:
            print("\n\nサーバーを停止しています...")
            received, sent, count = stats.get_stats()
            print(f"\n最終統計:")
            print(f"  メッセージ数: {count}")
            print(f"  総受信量: {received:,} バイト")
            print(f"  総送信量: {sent:,} バイト")

if __name__ == "__main__":
    main()
