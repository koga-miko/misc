#!/usr/bin/env python3
"""
gRPCサーバー実装 - 4つの通信方法を実装
TLS/SSL暗号化を有効化
"""
import grpc
from grpc_reflection.v1alpha import reflection
from concurrent import futures # pip install grpcio-reflection
import time
import demo_pb2
import demo_pb2_grpc


class DemoServiceServicer(demo_pb2_grpc.DemoServiceServicer):
    """4つの通信パターンを実装したサービス"""

    def UnaryCall(self, request, context):
        """1. Unary RPC: 単一リクエスト -> 単一レスポンス"""
        print(f"[Unary] Received: {request.name}")
        return demo_pb2.UnaryResponse(
            message=f"Hello, {request.name}! This is a unary response."
        )

    def ServerStreamingCall(self, request, context):
        """2. Server Streaming RPC: 単一リクエスト -> ストリームレスポンス"""
        print(f"[Server Streaming] Received count: {request.count}")
        for i in range(request.count):
            yield demo_pb2.ServerStreamingResponse(
                number=i + 1,
                message=f"Server streaming message #{i + 1}"
            )
            time.sleep(0.5)  # シミュレーション用の遅延

    def ClientStreamingCall(self, request_iterator, context):
        """3. Client Streaming RPC: ストリームリクエスト -> 単一レスポンス"""
        print("[Client Streaming] Started receiving stream")
        total_sum = 0
        count = 0
        for request in request_iterator:
            total_sum += request.value
            count += 1
            print(f"[Client Streaming] Received value: {request.value}")

        print(f"[Client Streaming] Total: {total_sum}, Count: {count}")
        return demo_pb2.ClientStreamingResponse(
            sum=total_sum,
            count=count
        )

    def BidirectionalStreamingCall(self, request_iterator, context):
        """4. Bidirectional Streaming RPC: 双方向ストリーミング"""
        print("[Bidirectional Streaming] Started")
        sequence = 0
        for request in request_iterator:
            sequence += 1
            print(f"[Bidirectional] Received: {request.message}")
            yield demo_pb2.BidirectionalResponse(
                echo=f"Echo: {request.message}",
                sequence=sequence
            )


def serve():
    """TLS/SSL暗号化を有効にしてサーバーを起動"""
    # サーバー証明書と秘密鍵を読み込む
    with open('certs/server-key.pem', 'rb') as f:
        private_key = f.read()
    with open('certs/server-cert.pem', 'rb') as f:
        certificate_chain = f.read()

    # サーバーの認証情報を設定
    server_credentials = grpc.ssl_server_credentials(
        [(private_key, certificate_chain)]
    )

    # サーバーを作成
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    demo_pb2_grpc.add_DemoServiceServicer_to_server(
        DemoServiceServicer(), server
    )

    # Reflection Service を登録 ← ★リフレクションAPIを有効化するためにここを追加
    SERVICE_NAMES = [
        demo_pb2.DESCRIPTOR.services_by_name['DemoService'].full_name,
        reflection.SERVICE_NAME,
    ]
    reflection.enable_server_reflection(SERVICE_NAMES, server)
        # TLS/SSLを有効にしてポートにバインド
    port = '50051'
    # server.add_insecure_port(f'[::]:{port}')
    server.add_secure_port(f'[::]:{port}', server_credentials)

    server.start()
    print(f"✓ gRPC Server started with TLS on port {port}")
    print("=" * 50)
    print("Waiting for client connections...")
    print("=" * 50)

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.stop(0)


if __name__ == '__main__':
    serve()
