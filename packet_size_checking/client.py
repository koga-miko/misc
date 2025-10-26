import socket
import random
import string
import time
import sys
from datetime import datetime

HOST = '127.0.0.1'
PORT = 12345

class ClientStats:
    def __init__(self):
        self.total_sent = 0
        self.total_received = 0
        self.message_count = 0

    def add_stats(self, sent, received):
        self.total_sent += sent
        self.total_received += received
        self.message_count += 1

    def print_stats(self, client_id):
        print(f"\n[クライアント{client_id}] 統計情報:")
        print(f"  メッセージ数: {self.message_count}")
        print(f"  総送信量: {self.total_sent:,} バイト ({self.total_sent/1024:.2f} KB)")
        print(f"  総受信量: {self.total_received:,} バイト ({self.total_received/1024:.2f} KB)")

def generate_random_ascii(min_size=100, max_size=1000):
    """ランダムなASCII文字列を生成"""
    size = random.randint(min_size, max_size)
    return ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation + ' ', k=size))

def send_message(sock, message):
    """メッセージを送信（長さ情報付き）"""
    msg_bytes = message.encode('ascii')
    msg_length = len(msg_bytes)

    # メッセージの長さを4バイトで送信
    length_bytes = msg_length.to_bytes(4, 'big')

    # 長さ + メッセージを送信
    sock.sendall(length_bytes + msg_bytes)

    return len(length_bytes) + len(msg_bytes)

def receive_message(sock):
    """メッセージを受信（長さ情報付き）"""
    # メッセージの長さを受信
    length_data = sock.recv(4)
    if not length_data:
        return None, 0

    msg_length = int.from_bytes(length_data, 'big')

    # メッセージ本体を受信
    data = b''
    while len(data) < msg_length:
        chunk = sock.recv(min(msg_length - len(data), 4096))
        if not chunk:
            return None, 0
        data += chunk

    received_size = len(length_data) + len(data)
    return data.decode('ascii'), received_size

def run_client(client_id):
    """クライアントを実行"""
    stats = ClientStats()

    print(f"[クライアント{client_id}] サーバーに接続中: {HOST}:{PORT}")

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((HOST, PORT))
            print(f"[クライアント{client_id}] 接続成功\n")

            while True:
                # ランダムなASCII文字列を生成
                message = generate_random_ascii(100, 1000)

                # サーバーに送信
                sent_size = send_message(sock, message)

                timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
                print(f"[{timestamp}] クライアント{client_id} - 送信: {sent_size}バイト (データ: {len(message)}バイト)")

                # サーバーからのエコーバックを受信
                received_message, received_size = receive_message(sock)

                if received_message is None:
                    print(f"[クライアント{client_id}] サーバーから切断されました")
                    break

                print(f"[{timestamp}] クライアント{client_id} - 受信: {received_size}バイト")

                # 送信データと受信データが一致するか確認
                if message == received_message:
                    print(f"[{timestamp}] クライアント{client_id} - ✓ データ検証成功")
                else:
                    print(f"[{timestamp}] クライアント{client_id} - ✗ データ検証失敗!")

                # 統計情報を更新
                stats.add_stats(sent_size, received_size)

                # 3～5秒のランダムな間隔で待機
                sleep_time = random.uniform(3.0, 5.0)
                print(f"[{timestamp}] クライアント{client_id} - 次の送信まで {sleep_time:.1f}秒待機\n")
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        print(f"\n[クライアント{client_id}] 停止中...")
        stats.print_stats(client_id)
    except ConnectionRefusedError:
        print(f"[クライアント{client_id}] エラー: サーバーに接続できません。サーバーが起動しているか確認してください。")
    except Exception as e:
        print(f"[クライアント{client_id}] エラー: {e}")
        stats.print_stats(client_id)

if __name__ == "__main__":
    # コマンドライン引数からクライアントIDを取得（デフォルトは1）
    client_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1

    run_client(client_id)
