#!/usr/bin/env python3
"""
gRPCクライアント実装 - 4つの通信方法をテスト
TLS/SSL暗号化を有効化
"""
import grpc
import demo_pb2
import demo_pb2_grpc
import time
import threading
import queue

def generate_client_streaming_requests():
    """Client Streaming用のリクエストを生成"""
    values = [10, 20, 30, 40, 50]
    for value in values:
        print(f"  → Sending value: {value}")
        yield demo_pb2.ClientStreamingRequest(value=value)
        time.sleep(0.3)


def generate_bidirectional_requests(request_queue):
    """Bidirectional Streaming用のリクエストを生成（キューベース）"""
    try:
        while True:
            # キューから次のメッセージを取得（タイムアウトなし）
            msg = request_queue.get()
            if msg is None:  # 終了シグナル
                break
            yield demo_pb2.BidirectionalRequest(message=msg)
    except Exception as e:
        print(f"  ✗ Request generator error: {e}")


def run():
    """TLS/SSL暗号化を有効にしてクライアントを実行"""
    # サーバー証明書を読み込む
    with open('certs/server-cert.pem', 'rb') as f:
        trusted_certs = f.read()

    # クライアントの認証情報を設定
    credentials = grpc.ssl_channel_credentials(root_certificates=trusted_certs)

    # # インセキュアチャネルを作成
    # with grpc.insecure_channel('localhost:50051') as channel:
    # セキュアチャネルを作成
    with grpc.secure_channel('localhost:50051', credentials) as channel:
        stub = demo_pb2_grpc.DemoServiceStub(channel)

        print("=" * 60)
        print("gRPC Client with TLS - Testing 4 Communication Patterns")
        print("=" * 60)

        # 1. Unary RPC
        print("\n[1] Testing Unary RPC")
        print("-" * 60)
        try:
            response = stub.UnaryCall(demo_pb2.UnaryRequest(name="Alice"))
            print(f"✓ Response: {response.message}")
        except grpc.RpcError as e:
            print(f"✗ Error: {e.code()} - {e.details()}")

        time.sleep(1)

        # 2. Server Streaming RPC
        print("\n[2] Testing Server Streaming RPC")
        print("-" * 60)
        try:
            responses = stub.ServerStreamingCall(
                demo_pb2.ServerStreamingRequest(count=5)
            )
            for response in responses:
                print(f"✓ Received: #{response.number} - {response.message}")
        except grpc.RpcError as e:
            print(f"✗ Error: {e.code()} - {e.details()}")

        time.sleep(1)

        # 3. Client Streaming RPC
        print("\n[3] Testing Client Streaming RPC")
        print("-" * 60)
        try:
            response = stub.ClientStreamingCall(generate_client_streaming_requests())
            print(f"✓ Response: Sum={response.sum}, Count={response.count}")
        except grpc.RpcError as e:
            print(f"✗ Error: {e.code()} - {e.details()}")

        time.sleep(1)

        # 4. Bidirectional Streaming RPC（送信・受信スレッド分離）
        print("\n[4] Testing Bidirectional Streaming RPC (Async Send/Receive)")
        print("-" * 60)
        try:
            # 送信用キュー
            request_queue = queue.Queue()

            # 受信完了を通知するイベント
            receive_done = threading.Event()
            receive_error = [None]  # エラーを格納するリスト

            # ストリーミングコールを開始
            responses = stub.BidirectionalStreamingCall(
                generate_bidirectional_requests(request_queue)
            )

            # 受信スレッド
            def receive_thread():
                """受信専用スレッド"""
                try:
                    print("  [Receive Thread] Started")
                    for response in responses:
                        print(f"  ✓ [Receive] {response.echo} (seq: {response.sequence})")
                    print("  [Receive Thread] Completed")
                except grpc.RpcError as e:
                    receive_error[0] = e
                    print(f"  ✗ [Receive] Error: {e.code()} - {e.details()}")
                except Exception as e:
                    receive_error[0] = e
                    print(f"  ✗ [Receive] Unexpected error: {e}")
                finally:
                    receive_done.set()

            # 送信スレッド
            def send_thread():
                """送信専用スレッド"""
                try:
                    print("  [Send Thread] Started")
                    messages = ["Hello", "How are you?", "gRPC is great!", "Goodbye"]
                    for msg in messages:
                        print(f"  → [Send] {msg}")
                        request_queue.put(msg)
                        time.sleep(0.5)  # 送信間隔

                    # 送信終了を通知
                    request_queue.put(None)
                    print("  [Send Thread] Completed")
                except Exception as e:
                    print(f"  ✗ [Send] Error: {e}")
                    request_queue.put(None)  # 終了シグナル

            # スレッド起動
            receiver = threading.Thread(target=receive_thread, daemon=True)
            sender = threading.Thread(target=send_thread, daemon=True)

            receiver.start()
            sender.start()

            # 両方のスレッドが完了するまで待機
            sender.join()
            receive_done.wait()

            if receive_error[0]:
                print(f"✗ Bidirectional streaming completed with errors")
            else:
                print("✓ Bidirectional streaming completed successfully")

        except grpc.RpcError as e:
            print(f"✗ Error: {e.code()} - {e.details()}")
        except Exception as e:
            print(f"✗ Unexpected error: {e}")

        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)


if __name__ == '__main__':
    run()
