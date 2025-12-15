#!/usr/bin/env python3
"""
gRPCクライアント実装 - 4つの通信方法をテスト
TLS/SSL暗号化を有効化
"""
import grpc
import demo_pb2
import demo_pb2_grpc
import time


def generate_client_streaming_requests():
    """Client Streaming用のリクエストを生成"""
    values = [10, 20, 30, 40, 50]
    for value in values:
        print(f"  → Sending value: {value}")
        yield demo_pb2.ClientStreamingRequest(value=value)
        time.sleep(0.3)


def generate_bidirectional_requests():
    """Bidirectional Streaming用のリクエストを生成"""
    messages = ["Hello", "How are you?", "gRPC is great!", "Goodbye"]
    for msg in messages:
        print(f"  → Sending: {msg}")
        yield demo_pb2.BidirectionalRequest(message=msg)
        time.sleep(0.5)


def run():
    """TLS/SSL暗号化を有効にしてクライアントを実行"""
    # サーバー証明書を読み込む
    with open('certs/server-cert.pem', 'rb') as f:
        trusted_certs = f.read()

    # クライアントの認証情報を設定
    credentials = grpc.ssl_channel_credentials(root_certificates=trusted_certs)

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

        # 4. Bidirectional Streaming RPC
        print("\n[4] Testing Bidirectional Streaming RPC")
        print("-" * 60)
        try:
            responses = stub.BidirectionalStreamingCall(
                generate_bidirectional_requests()
            )
            for response in responses:
                print(f"✓ Received: {response.echo} (seq: {response.sequence})")
        except grpc.RpcError as e:
            print(f"✗ Error: {e.code()} - {e.details()}")

        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)


if __name__ == '__main__':
    run()
